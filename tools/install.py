"""Installation script for `config-ninja`_, based on the official `Poetry installer`_.

.. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
.. _Poetry installer: https://github.com/python-poetry/install.python-poetry.org/blob/d62875fc05fb20062175cd14d19a96dbefa48640/install-poetry.py
"""
from __future__ import annotations

import sys

RC_INVALID_PYTHON = 1
RC_PATH_EXISTS = 2

# Eager version check so we fail nicely before possible syntax errors
if sys.version_info < (3, 8):  # noqa: UP036
    sys.stdout.write('config-ninja installer requires Python 3.8 or newer to run!\n')
    sys.exit(RC_INVALID_PYTHON)

# pylint: disable=wrong-import-position,import-outside-toplevel

import argparse
import contextlib
import copy
import importlib
import json
import os
import re
import runpy
import shutil
import subprocess
import sysconfig
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.request import Request

# note: must be synchronized with 'tool.poetry.extras' in pyproject.toml
PACKAGE_EXTRAS = ['all', 'appconfig', 'local']

MACOS = sys.platform == 'darwin'
MINGW = sysconfig.get_platform().startswith('mingw')
SHELL = os.getenv('SHELL', '')
USER_AGENT = 'Python Config Ninja'
WINDOWS = sys.platform.startswith('win') or (sys.platform == 'cli' and os.name == 'nt')


def _get_win_folder_from_registry(
    csidl_name: Literal['CSIDL_APPDATA', 'CSIDL_COMMON_APPDATA', 'CSIDL_LOCAL_APPDATA'],
) -> Any:  # pragma: no cover
    import winreg as _winreg  # pylint: disable=import-error

    shell_folder_name = {
        'CSIDL_APPDATA': 'AppData',
        'CSIDL_COMMON_APPDATA': 'Common AppData',
        'CSIDL_LOCAL_APPDATA': 'Local AppData',
    }[csidl_name]

    key = _winreg.OpenKey(  # type: ignore[attr-defined,unused-ignore]
        _winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined,unused-ignore]
        r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
    )
    path, _ = _winreg.QueryValueEx(key, shell_folder_name)  # type: ignore[attr-defined,unused-ignore]

    return path  # pyright: ignore[reportUnknownVariableType]


def _get_win_folder_with_ctypes(
    csidl_name: Literal['CSIDL_APPDATA', 'CSIDL_COMMON_APPDATA', 'CSIDL_LOCAL_APPDATA'],
) -> Any:  # pragma: no cover
    import ctypes  # pylint: disable=import-error

    csidl_const = {
        'CSIDL_APPDATA': 26,
        'CSIDL_COMMON_APPDATA': 35,
        'CSIDL_LOCAL_APPDATA': 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)  # type: ignore[attr-defined,unused-ignore]

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:  # noqa: PLR2004
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):  # type: ignore[attr-defined,unused-ignore]
            buf = buf2

    return buf.value


def _get_data_dir() -> Path:
    if os.getenv('CONFIG_NINJA_HOME'):
        return Path(os.environ['CONFIG_NINJA_HOME']).expanduser()

    if WINDOWS:  # pragma: no cover
        try:
            from ctypes import (  # type: ignore[attr-defined,unused-ignore]
                windll,  # pyright: ignore  # noqa: F401
            )

            base_dir = Path(_get_win_folder_with_ctypes('CSIDL_APPDATA'))
        except ImportError:
            base_dir = Path(_get_win_folder_from_registry('CSIDL_APPDATA'))

    elif MACOS:  # pragma: no cover
        base_dir = Path('~/Library/Application Support').expanduser()

    else:
        base_dir = Path(os.getenv('XDG_DATA_HOME', '~/.local/share')).expanduser()

    return base_dir.resolve() / 'config-ninja'


def string_to_bool(value: str) -> bool:
    """Parse a boolean from the given string."""
    return value.lower() in {'true', '1', 'y', 'yes'}


class _VirtualEnvironment:
    """Create a virtual environment."""

    bin: Path
    path: Path
    python: Path

    def __init__(self, path: Path) -> None:
        self.path = path
        self.bin = path / ('Scripts' if WINDOWS and not MINGW else 'bin')
        self.python = self.bin / ('python.exe' if WINDOWS else 'python')

    def __repr__(self) -> str:
        """Define the string representation of the `_VirtualEnvironment` object.

        >>> _VirtualEnvironment(Path('.venv'))
        _VirtualEnvironment('.venv')
        """
        return f"{self.__class__.__name__}('{self.path}')"

    @staticmethod
    def _create_with_venv(target: Path) -> None:
        """Create a virtual environment using the `venv` module."""
        import venv

        builder = venv.EnvBuilder(clear=True, with_pip=True, symlinks=False)
        context = builder.ensure_directories(target)

        if (  # pragma: no cover  # windows
            WINDOWS and hasattr(context, 'env_exec_cmd') and context.env_exe != context.env_exec_cmd
        ):
            target = target.resolve()

        builder.create(target)

    @staticmethod
    def _create_with_virtualenv(target: Path) -> None:
        """Create a virtual environment using the `virtualenv` module."""
        python_version = f'{sys.version_info.major}.{sys.version_info.minor}'
        bootstrap_url = f'https://bootstrap.pypa.io/virtualenv/{python_version}/virtualenv.pyz'
        with tempfile.TemporaryDirectory(prefix='config-ninja-installer') as temp_dir:
            virtualenv_pyz = Path(temp_dir) / 'virtualenv.pyz'
            request = Request(bootstrap_url, headers={'User-Agent': USER_AGENT})
            with contextlib.closing(urllib.request.urlopen(request)) as response:
                virtualenv_pyz.write_bytes(response.read())

        # copy `argv` so we can override it and then restore it
        argv = copy.deepcopy(sys.argv)
        sys.argv = [str(virtualenv_pyz), '--clear', '--always-copy', str(target)]

        try:
            runpy.run_path(str(virtualenv_pyz))
        finally:
            sys.argv = argv

    @classmethod
    def create(cls, target: Path) -> _VirtualEnvironment:
        """Create a virtual environment at the specified path.

        On some linux distributions (eg: debian), the distribution-provided python installation
        might not include `ensurepip`, causing the `venv` module to fail when attempting to create a
        virtual environment. To mitigate this, we use `importlib` to import both `ensurepip` and
        `venv`; if either fails, we fall back to using `virtualenv` instead.
        """
        try:
            importlib.import_module('ensurepip')
        except ImportError:
            cls._create_with_virtualenv(target)
        else:
            cls._create_with_venv(target)

        env = cls(target)

        try:
            env.pip('install', '--disable-pip-version-check', '--upgrade', 'pip')
        except subprocess.CalledProcessError as exc:  # pragma: no cover
            sys.stderr.write(exc.stderr.decode('utf-8') + '\n')
            sys.stderr.write(f'{warning}: Failed to upgrade pip; additional errors may occur.\n')

        return env

    def pip(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        """Run the 'pip' installation inside the virtual environment."""
        return subprocess.run(
            [str(self.python), '-m', 'pip', *args],  # noqa: S603  # is trusted
            capture_output=True,
            check=True,
        )


class _Version:
    """Model a PEP 440 version string.

    >>> print(_Version('1.0'))
    1.0

    >>> _Version('0.9') < _Version('1') < _Version('1.0.1')
    True

    >>> _Version('1.1.0b3') < _Version('1.1.0b4') < _Version('1.1.0')
    True

    >>> _Version('2.1.0') > _Version('2.0.0') > _Version('2.0.0b1') > _Version('2.0.0a2')
    True

    >>> _Version('1.0') == '1.0'
    True

    >>> with pytest.raises(ValueError):
    ...     invalid = _Version('random')
    """

    REGEX = re.compile(
        r'v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?'
        '('
        '[._-]?'
        r'(?:(stable|beta|b|rc|RC|alpha|a|patch|pl|p)((?:[.-]?\d+)*)?)?'
        '([.-]?dev)?'
        ')?'
        r'(?:\+[^\s]+)?'
    )
    major: int | None
    minor: int | None
    patch: int | None
    pre: str

    raw: str
    """The original raw version string."""

    def __init__(self, version: str) -> None:
        self.raw = version

        match = self.REGEX.match(version)
        if not match:
            raise ValueError(f'Invalid version (does not match regex {self.REGEX}): {version}')

        groups = match.groups()
        self.major, self.minor, self.patch = tuple(
            None if ver is None else int(ver) for ver in groups[:3]
        )
        self.pre: str = groups[4]

    def __eq__(self, other: Any) -> bool:
        return self.tuple == _Version(str(other)).tuple

    def __gt__(self, other: _Version) -> bool:
        if self.tuple[:3] == other.tuple[:3]:
            if self.pre and other.pre:
                return self.pre > other.pre
            return self.pre == '' and other.pre > ''

        return self.tuple[:3] > other.tuple[:3]

    def __lt__(self, other: _Version) -> bool:
        if self.tuple[:3] == other.tuple[:3]:
            if self.pre and other.pre:
                return self.pre < other.pre
            return self.pre > '' and other.pre == ''
        return self.tuple[:3] < other.tuple[:3]

    def __repr__(self) -> str:
        """Define the string representation of the `_Version` object.

        >>> _Version('1.0')
        _Version('1.0')
        """
        return f"_Version('{self.raw}')"

    def __str__(self) -> str:
        semver = '.'.join([str(v) for v in self.tuple[:3] if v is not None])
        return f'{semver}{self.pre or ""}'

    @property
    def tuple(self) -> tuple[int | str | None, ...]:
        """Return the version as a tuple for comparisons."""
        version = (self.major, self.minor, self.patch, self.pre)
        return tuple(v for v in version if v == 0 or v)


class Installer:
    """Install the config-ninja package.

    >>> spec = Installer.Spec(Path('.cn'), version='1.0')
    >>> installer = Installer(spec)
    >>> installer.install()
    _VirtualEnvironment(...)

    If the specified version is not available, a `ValueError` is raised:

    >>> spec = Installer.Spec(Path('.cn'), version='0.9')
    >>> installer = Installer(spec)
    >>> with pytest.raises(ValueError):
    ...     installer.install()

    By default, the latest version available from PyPI is installed:

    >>> spec = Installer.Spec(Path('.cn'))
    >>> installer = Installer(spec)
    >>> installer.install()
    _VirtualEnvironment(...)

    Pre-release versions are excluded unless the `pre` argument is passed:

    >>> spec = Installer.Spec(Path('.cn'), pre=True)
    >>> installer = Installer(spec)
    >>> installer.install()
    _VirtualEnvironment(...)
    """

    METADATA_URL = 'https://pypi.org/pypi/config-ninja/json'
    """Retrieve the latest version of config-ninja from this URL."""

    _allow_pre_releases: bool
    _extras: str
    _force: bool
    _path: Path
    _version: _Version | None

    @dataclass
    class Spec:
        """Specify parameters for the `Installer` class."""

        path: Path

        extras: str = ''
        force: bool = False
        pre: bool = False
        version: str | None = None

    def __init__(self, spec: Spec) -> None:
        """Initialize properties on the `Installer` object."""
        self._path = spec.path

        self._allow_pre_releases = spec.pre
        self._extras = spec.extras
        self._force = spec.force
        self._version = _Version(spec.version) if spec.version else None

    def _get_releases_from_pypi(self) -> list[_Version]:
        request = Request(self.METADATA_URL, headers={'User-Agent': USER_AGENT})

        with contextlib.closing(urllib.request.urlopen(request)) as response:
            resp_bytes: bytes = response.read()

        metadata: dict[str, Any] = json.loads(resp_bytes.decode('utf-8'))
        return sorted([_Version(k) for k in metadata['releases'].keys()])

    def _get_latest_release(self, releases: list[_Version]) -> _Version:
        for version in reversed(releases):
            if version.pre and self._allow_pre_releases:
                return version

            if not version.pre:
                return version

        raise ValueError(  # pragma: no cover
            'Unable to find a valid release; try installing a pre-release '
            "by passing the '--pre' argument"
        )

    def _get_version(self) -> _Version:
        releases = self._get_releases_from_pypi()

        if self._version and self._version not in releases:
            raise ValueError(f'Unable to find version: {self._version}')

        if not self._version:
            return self._get_latest_release(releases)

        return self._version

    @property
    def force(self) -> bool:
        """If truthy, skip overwrite existing paths."""
        return self._force

    def symlink(self, source: Path, check_target: Path, remove: bool = False) -> Path:
        """Recurse up parent directories until the first 'bin' is found."""
        if (bin_dir := check_target / 'bin').is_dir():
            if (target := bin_dir / 'config-ninja').exists() and not self._force and not remove:
                raise FileExistsError(target)

            target.unlink(missing_ok=True)
            if not remove:
                os.symlink(source, target)
            return target

        if (  # pragma: no cover  # windows
            not check_target.parent or not check_target.parent.is_dir()
        ):
            raise FileNotFoundError('Could not find directory for symlink')

        return self.symlink(source, check_target.parent, remove)

    def install(self) -> _VirtualEnvironment:
        """Install the config-ninja package."""
        if self._path.exists() and not self._force:
            raise FileExistsError(f'Path already exists: {self._path}')

        version = self._get_version()
        env = _VirtualEnvironment.create(self._path)

        args = ['install']
        if self._force:
            args.append('--upgrade')
            args.append('--force-reinstall')
        args.append(f'config-ninja{self._extras}=={version}')

        env.pip(*args)

        return env

    @property
    def path(self) -> Path:
        """Get the installation path."""
        return self._path


def _extras_type(value: str) -> str:
    """Parse the given comma-separated string of package extras.

    >>> _extras_type('appconfig,local')
    '[appconfig,local]'

    If given 'none', an empty string is returned:

    >>> _extras_type('none')
    ''

    Invalid extras are removed:

    >>> _extras_type('appconfig,invalid,local')
    '[appconfig,local]'
    """
    if not value or value == 'none':
        return ''
    extras = [extra.strip() for extra in value.split(',') if extra.strip() in PACKAGE_EXTRAS]
    return f'[{",".join(extras)}]' if extras else ''


def _parse_args(argv: tuple[str, ...]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Installs the latest (or given) version of config-ninja'
    )
    parser.add_argument('--version', help='install named version', dest='version')
    parser.add_argument(
        '--pre',
        help='allow pre-release versions to be installed',
        dest='pre',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--uninstall',
        help='uninstall config-ninja',
        dest='uninstall',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--force',
        help="respond 'yes' to confirmation prompts; overwrite existing installations",
        dest='force',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--path',
        default=None,
        dest='path',
        action='store',
        type=Path,
        help='install config-ninja to this directory',
    )
    parser.add_argument(
        '--backends',
        dest='backends',
        action='store',
        type=_extras_type,
        help="comma-separated list of package extras to install, or 'none' to install no backends",
    )

    return parser.parse_args(argv)


def blue(text: Any) -> str:
    """Color the given text blue."""
    return f'\033[94m{text}\033[0m'


def cyan(text: Any) -> str:
    """Color the given text cyan."""
    return f'\033[96m{text}\033[0m'


def gray(text: Any) -> str:  # pragma: no cover  # edge case / windows
    """Color the given text gray."""
    return f'\033[90m{text}\033[0m'


def green(text: Any) -> str:
    """Color the given text green."""
    return f'\033[92m{text}\033[0m'


def orange(text: Any) -> str:
    """Color the given text orange."""
    return f'\033[33m{text}\033[0m'


def red(text: Any) -> str:
    """Color the given text red."""
    return f'\033[91m{text}\033[0m'


def yellow(text: Any) -> str:
    """Color the given text yellow."""
    return f'\033[93m{text}\033[0m'


warning = yellow('WARNING')
failure = red('FAILURE')
prompts = blue('PROMPTS')
success = green('SUCCESS')


def _maybe_create_symlink(installer: Installer, env: _VirtualEnvironment) -> None:
    if env.bin in [  # pragma: no cover  # edge case for installation to e.g. /usr/local
        Path(p) for p in os.getenv('PATH', '').split(os.pathsep)
    ]:
        # we're already on the PATH; no need to symlink
        return

    if WINDOWS and not MINGW:  # pragma: no cover
        sys.stdout.write(
            f'{warning}: In order to run the {blue("config-ninja")} command, add '
            f'the following line to {gray(os.getenv("USERPROFILE"))}:\n'
        )
        rhs = cyan(f'";{env.bin}"')
        sys.stdout.write(f'{green("$Env:Path")} += {rhs}')
        return

    try:
        symlink = installer.symlink(env.bin / 'config-ninja', env.path.parent)
    except FileExistsError as exc:
        sys.stderr.write(f'{warning}: Already exists: {cyan(exc.args[0])}\n')
        sys.stderr.write(f'Pass the {blue("--force")} argument to clobber it\n')
        sys.exit(RC_PATH_EXISTS)
    except (FileNotFoundError, PermissionError):
        sys.stderr.write(f'{warning}: Failed to create symlink\n')
        shell = os.getenv('SHELL', '').split(os.sep)[-1]
        your_dotfile = (
            cyan(Path.home() / f'.{shell}rc') if shell else f"your shell's {cyan('~/.*rc')} file"
        )
        sys.stderr.write(
            f'In order to run the {blue("config-ninja")} command, add the following '
            + f'line to {your_dotfile}:\n'
        )
        path = orange(f'"{env.bin}:$PATH"')
        sys.stderr.write(f'{blue("export")} PATH={path}')
        return

    sys.stdout.write(f'A symlink was created at {green(symlink)}\n')


def _do_install(installer: Installer) -> None:
    sys.stdout.write(f'🥷 Installing {blue("config-ninja")} to path {cyan(installer.path)}...\n')
    sys.stdout.flush()

    try:
        env = installer.install()
    except FileExistsError as exc:
        sys.stderr.write(f'{failure}: {exc}\n')
        sys.stdout.write(
            f"Pass the {blue('--force')} argument to clobber it or "
            f"{blue('--uninstall')} to remove it.\n"
        )
        sys.exit(RC_PATH_EXISTS)

    sys.stdout.write(f'{success}: Installation to virtual environment complete ✅\n')

    _maybe_create_symlink(installer, env)


def _do_uninstall(installer: Installer) -> None:
    if not installer.force:
        prompt = f"Uninstall {blue('config-ninja')} from {cyan(installer.path)}? [y/N]: "
        if Path('/dev/tty').exists():
            sys.stdout.write(prompt)
            sys.stdout.flush()
            with open('/dev/tty', encoding='utf-8') as tty:
                uninstall = tty.readline().strip()
        else:  # pragma: no cover  # windows
            uninstall = input(prompt)

        if not uninstall.lower().startswith('y'):
            sys.stderr.write(f'{failure}: Aborted uninstallation ❌\n')
            sys.exit(RC_PATH_EXISTS)

    sys.stdout.write('...\n')
    shutil.rmtree(installer.path)
    sys.stdout.write(
        f"{success}: Uninstalled {blue('config-ninja')} from path {cyan(installer.path)} ✅\n"
    )
    if not WINDOWS or MINGW:  # pragma: no cover  # windows
        installer.symlink(
            installer.path / 'bin' / 'config-ninja', installer.path.parent, remove=True
        )


def main(*argv: str) -> None:
    """Install the `config-ninja` package to a virtual environment."""
    args = _parse_args(argv)
    install_path: Path = args.path or _get_data_dir()

    spec = Installer.Spec(
        install_path,
        version=args.version or os.getenv('CONFIG_NINJA_VERSION'),
        force=args.force or string_to_bool(os.getenv('CONFIG_NINJA_FORCE', 'false')),
        pre=args.pre or string_to_bool(os.getenv('CONFIG_NINJA_PRE', 'false')),
        extras=args.backends or os.getenv('CONFIG_NINJA_BACKENDS', ''),
    )

    installer = Installer(spec)
    if args.uninstall:
        if not installer.path.is_dir():
            sys.stdout.write(f'{warning}: Path does not exist: {cyan(installer.path)}\n')
            return
        _do_uninstall(installer)
        return

    _do_install(installer)


if __name__ == '__main__':  # pragma: no cover
    main(*sys.argv[1:])
