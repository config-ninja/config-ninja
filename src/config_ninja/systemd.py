"""Generate a `systemd` unit file for installation as a service.

The following `jinja2` template is used to generate the `systemd` unit file:

```jinja
.. include:: ./templates/systemd.service.j2
```

Run the CLI's `install`_ command to install the service:

```sh
❯ config-ninja self install --env AWS_PROFILE --user
Installing /home/ubuntu/.config/systemd/user/config-ninja.service
● config-ninja.service - config synchronization daemon
     Loaded: loaded (/home/ubuntu/.config/systemd/user/config-ninja.service; disabled; vendor preset: enabled)
     Active: active (running) since Sun 2024-01-21 22:37:52 EST; 7ms ago
    Process: 20240 ExecStartPre=/usr/local/bin/config-ninja self print (code=exited, status=0/SUCCESS)
   Main PID: 20241 (config-ninja)
     CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/config-ninja.service
             └─20241 /usr/local/bin/python /usr/local/bin/config-ninja monitor

Jan 21 22:37:51 ubuntu config-ninja[20240]:     path: /tmp/config-ninja/settings-subset.toml
Jan 21 22:37:51 ubuntu config-ninja[20240]:   source:
Jan 21 22:37:51 ubuntu config-ninja[20240]:     backend: local
Jan 21 22:37:51 ubuntu config-ninja[20240]:     format: yaml
Jan 21 22:37:51 ubuntu config-ninja[20240]:     new:
Jan 21 22:37:51 ubuntu config-ninja[20240]:       kwargs:
Jan 21 22:37:51 ubuntu config-ninja[20240]:         path: config-ninja-settings.yaml
Jan 21 22:37:52 ubuntu config-ninja[20241]: Begin monitoring: ['example-local', 'example-local-template', 'example-appconfig']
Jan 21 22:37:52 ubuntu systemd[592]: Started config synchronization daemon.

SUCCESS ✅
```

.. _install: https://bryant-finney.github.io/config-ninja/config_ninja/cli.html#config-ninja-self-install
"""  # noqa: RUF002

from __future__ import annotations

import contextlib
import logging
import os
import string
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2
import sdnotify

if TYPE_CHECKING:  # pragma: no cover
    import sh

    AVAILABLE = True
else:
    try:
        import sh
    except ImportError:  # pragma: no cover
        sh = None
        AVAILABLE = False
    else:
        AVAILABLE = hasattr(sh, 'systemctl')


SERVICE_NAME = 'config-ninja.service'
SYSTEM_INSTALL_PATH = Path('/etc/systemd/system')
"""The file path for system-wide installation."""

USER_INSTALL_PATH = Path(os.getenv('XDG_CONFIG_HOME') or Path.home() / '.config') / 'systemd' / 'user'
"""The file path for user-local installation."""

__all__ = ['SYSTEM_INSTALL_PATH', 'USER_INSTALL_PATH', 'Service', 'notify']
logger = logging.getLogger(__name__)


@contextlib.contextmanager
def dummy() -> typing.Iterator[None]:
    """Define a dummy context manager to use instead of `sudo`.

    There are a few scenarios where `sudo` is unavailable or unnecessary:
    - running on Windows
    - running in a container without `sudo` installed
    - already running as root
    """
    yield  # pragma: no cover


try:
    sudo = sh.contrib.sudo
except AttributeError:  # pragma: no cover
    sudo = dummy()


def notify() -> None:  # pragma: no cover
    """Notify `systemd` that the service has finished starting up and is ready."""
    sock = sdnotify.SystemdNotifier()
    sock.notify('READY=1')  # pyright: ignore[reportUnknownMemberType]


class Service:
    """Manipulate the `systemd` service file for `config-ninja`.

    ## User Installation

    To install the service for only the current user, pass `user_mode=True` to the initializer:

    >>> svc = Service('config_ninja', 'systemd.service.j2', user_mode=True)
    >>> _ = svc.install(
    ...     config_ninja_cmd='config-ninja', workdir='.', environ={'TESTING': 'true'}
    ... )

    >>> print(svc.read())
    [Unit]
    Description=config synchronization daemon
    After=network.target
    <BLANKLINE>
    [Service]
    Environment=PYTHONUNBUFFERED=true
    Environment=TESTING=true
    ExecStartPre=config-ninja self  print
    ExecStart=config-ninja apply  --poll
    Restart=always
    RestartSec=30s
    Type=notify
    WorkingDirectory=...
    <BLANKLINE>
    [Install]
    Alias=config-ninja.service

    >>> svc.uninstall()

    ## System Installation

    For system-wide installation:

    >>> svc = Service('config_ninja', 'systemd.service.j2', user_mode=False)
    >>> _ = svc.install(
    ...     config_ninja_cmd='config-ninja', workdir='.', environ={'TESTING': 'true'}
    ... )

    >>> svc.uninstall()
    """

    path: Path
    """The installation location of the `systemd` unit file."""

    sudo: typing.ContextManager[None]

    tmpl: jinja2.Template
    """Load the template on initialization."""

    user_mode: bool
    """Whether to install the service for the full system or just the current user."""

    valid_chars: str = f'{string.ascii_letters}{string.digits}_-:'
    """Valid characters for the `systemd` unit file name."""

    max_length: int = 255
    """Maximum length of the `systemd` unit file name."""

    def __init__(self, provider: str, template: str, user_mode: bool, config_fname: Path | None = None) -> None:
        """Prepare to render the specified `template` from the `provider` package."""
        loader = jinja2.PackageLoader(provider)
        env = jinja2.Environment(autoescape=jinja2.select_autoescape(default=True), loader=loader)
        self.tmpl = env.get_template(template)
        self.user_mode = user_mode

        install_path = USER_INSTALL_PATH if user_mode else SYSTEM_INSTALL_PATH
        if config_fname:
            base_name = (
                (
                    str(config_fname.resolve().with_suffix(''))
                    .replace('-', '--')
                    .replace('/', '-')[1 : self.max_length - len('.service')]
                )
                + '.service'
            )
            self.path = install_path / base_name
        else:
            self.path = install_path / 'config-ninja.service'

        if os.geteuid() == 0:
            self.sudo = dummy()
        else:
            self.sudo = sudo

    def _install_system(self, content: str) -> str:
        logger.info('writing to %s', self.path)
        sh.mkdir('-p', str(self.path.parent))
        sh.tee(str(self.path), _in=content, _out='/dev/null')

        logger.info('enabling and starting %s', self.path.name)
        sh.systemctl.start(self.path.name)
        return sh.systemctl.status(self.path.name)

    def _install_user(self, content: str) -> str:
        logger.info('writing to %s', self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding='utf-8')

        logger.info('enabling and starting %s', self.path.name)
        sh.systemctl.start('--user', self.path.name)
        return sh.systemctl.status('--user', self.path.name)

    def _uninstall_system(self) -> None:
        logger.info('stopping and disabling %s', self.path.name)
        sh.systemctl.disable('--now', self.path.name)

        logger.info('removing %s', self.path)
        sh.rm(str(self.path))

    def _uninstall_user(self) -> None:
        logger.info('stopping and disabling %s', self.path.name)
        sh.systemctl.disable('--user', '--now', self.path.name)

        logger.info('removing %s', self.path)
        self.path.unlink()

    def install(self, **kwargs: typing.Any) -> str:
        """Render the `systemd` service file from `kwargs` and install it."""
        rendered = self.render(**kwargs)
        if self.user_mode:
            return self._install_user(rendered)

        if os.geteuid() == 0:
            return self._install_system(rendered)

        with sudo:
            return self._install_system(rendered)

    def read(self) -> str:
        """Read the `systemd` service file."""
        return self.path.read_text(encoding='utf-8')

    def render(self, **kwargs: typing.Any) -> str:
        """Render the `systemd` service file from the given parameters."""
        if workdir := kwargs.get('workdir'):
            kwargs['workdir'] = Path(workdir).absolute()

        kwargs.setdefault('user_mode', self.user_mode)

        return self.tmpl.render(**kwargs)

    def uninstall(self) -> None:
        """Disable, stop, and delete the service."""
        if self.user_mode:
            return self._uninstall_user()

        if os.geteuid() == 0:
            return self._uninstall_system()

        with sudo:
            return self._uninstall_system()
