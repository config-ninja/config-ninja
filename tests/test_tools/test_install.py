"""Define tests for the `install` script."""

from __future__ import annotations

import importlib
import re
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from tools import install

# pylint: disable=redefined-outer-name


def _run_installer(*argv: str) -> None:
    importlib.reload(install).main(*argv)


@pytest.fixture
def _mock_ensurepip_missing(mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Raise an `ImportError` if `importlib.import_module` is passed 'ensurepip'."""

    def _mock_import_module(name: str, package: str | None = None) -> ModuleType:
        if name == 'ensurepip':
            raise ImportError('Mocked!')
        return import_module(name, package=package)

    mocker.patch('importlib.import_module', new=_mock_import_module)


@pytest.fixture
def mock_ensurepip_present(mocker: MockerFixture) -> mock.MagicMock:
    """Patch `importlib.import_module` to mimic `ensurepip` is installed."""
    mock_import_module: mock.MagicMock = mocker.patch('importlib.import_module')
    return mock_import_module


def test_unsupported_python(mocker: MockerFixture) -> None:
    """Test that the install script fails on Python 3.7."""
    mocker.patch('sys.version_info', (3, 7))

    with pytest.raises(SystemExit, match=str(install.RC_INVALID_PYTHON)):
        _run_installer()


def test_install_path_exists() -> None:
    """Test that the install script fails if the install path exists."""
    # Assert
    with pytest.raises(SystemExit, match=str(install.RC_PATH_EXISTS)):
        # Act
        _run_installer('--path', '.')


@pytest.mark.usefixtures('_mock_ensurepip_missing', '_mock_install_io', '_mock_urlopen_for_pypi')
def test_uses_virtualenv(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test that the install script falls back to using virtualenv."""
    # Arrange
    mocker.patch('os.symlink')
    # override the patch from _mock_install_io so we can access it in this test
    mock_run_path = mocker.patch('runpy.run_path')

    # Act
    _run_installer('--path', str(tmp_path / '.cn'))

    # Assert
    mock_run_path.assert_called_once()
    assert mock_run_path.call_args.args
    assert mock_run_path.call_args.args[0].endswith('virtualenv.pyz')


@pytest.mark.usefixtures('_mock_install_io', '_mock_urlopen_for_pypi')
def test_respects_config_ninja_home(
    mock_ensurepip_present: mock.MagicMock,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the environment variable `CONFIG_NINJA_HOME` is referenced during install."""
    # Arrange
    install_path = tmp_path / '.cn'
    mocker.patch('os.symlink')

    mock_stdout = mock.MagicMock(sys.stdout.__class__)
    monkeypatch.setattr(sys, 'stdout', mock_stdout)
    monkeypatch.setenv('CONFIG_NINJA_HOME', str(install_path))

    # Act
    _run_installer('--force')
    stdout = '\n'.join([args[0][0] for args in mock_stdout.write.call_args_list])
    call_count = len([args.args[0] for args in mock_ensurepip_present.call_args_list if args.args[0] == 'ensurepip'])

    # Assert
    assert (
        call_count == 1
    ), f'Expected \'import_module("ensurepip")\' to have been called once. Called {call_count} times.'

    assert str(install_path).lower() in stdout.lower()


@pytest.mark.usefixtures('_mock_install_io', '_mock_urlopen_for_pypi')
def test_respects_xdg_home(
    mock_ensurepip_present: mock.MagicMock,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the environment variable `XDG_DATA_HOME` is referenced during install."""
    # Arrange
    install_path = tmp_path / '.cn'
    mocker.patch('os.symlink')

    mock_stdout = mock.MagicMock(sys.stdout.__class__)
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(sys, 'stdout', mock_stdout)
    monkeypatch.setenv('XDG_DATA_HOME', str(install_path))

    # Act
    _run_installer('--force')
    stdout = '\n'.join([call[0][0] for call in mock_stdout.write.call_args_list])
    call_count = len([call.args[0] for call in mock_ensurepip_present.call_args_list if call.args[0] == 'ensurepip'])

    # Assert
    assert (
        call_count == 1
    ), f'Expected \'import_module("ensurepip")\' to have been called once. Called {call_count} times.'

    assert str(install_path).lower() in stdout.lower()


@pytest.mark.skipif(sys.platform == 'win32', reason='symlinks are not supported on Windows')
@pytest.mark.usefixtures('_mock_ensurepip_missing', '_mock_install_io', '_mock_urlopen_for_pypi')
def test_symlink_already_exists(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test that the install script fails if the symlink already exists."""
    # Arrange
    target = tmp_path / 'bin' / 'config-ninja'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()

    mock_stderr = mocker.patch('sys.stderr')

    # Act
    with pytest.raises(SystemExit, match=str(install.RC_PATH_EXISTS)):
        _run_installer('--path', str(tmp_path / '.cn'))
    stderr = '\n'.join([args[0][0] for args in mock_stderr.write.call_args_list])

    # Assert
    assert 'already exists:' in stderr.lower()
    assert str(target).lower() in stderr.lower()


@pytest.mark.skipif(sys.platform == 'win32', reason='symlinks are not supported on Windows')
@pytest.mark.usefixtures('_mock_ensurepip_missing', '_mock_install_io', '_mock_urlopen_for_pypi')
def test_no_symlink_perms(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test that errors are handled if the user lacks permissions to write the symlink."""
    # Arrange
    path = tmp_path / 'install-dir'
    mock_stderr = mocker.patch('sys.stderr')
    mock_symlink = mocker.patch('os.symlink', side_effect=PermissionError)
    regex = re.compile(r'.*export.* PATH=.*".+:\$PATH"')

    # Act
    _run_installer('--path', str(path))
    stderr = '\n'.join([args[0][0] for args in mock_stderr.write.call_args_list])

    # Assert
    assert mock_symlink.call_count == 1
    assert 'failed to create symlink' in stderr.lower()
    assert regex.match(mock_stderr.write.call_args[0][0]), mock_stderr.write.call_args[0][0]


@pytest.mark.usefixtures('_mock_install_io')
def test_uninstall_dne(mocker: MockerFixture, tmp_path: Path) -> None:
    """Verify the '--uninstall' option prints a warning if the install path does not exist."""
    # Arrange
    dne = tmp_path / 'does-not-exist'
    mock_stdout = mocker.patch('sys.stdout')

    # Act
    _run_installer('--uninstall', '--path', str(dne))

    # Assert
    assert 'path does not exist:' in mock_stdout.write.call_args[0][0].lower()
    assert str(dne) in mock_stdout.write.call_args[0][0]


def test_uninstall_aborted(mocker: MockerFixture, tmp_path: Path) -> None:
    """Verify that the uninstall operation is aborted if the user does not confirm."""
    # Arrange
    mock_stderr = mocker.patch('sys.stderr')
    mock_open = mocker.patch('builtins.open', mock.mock_open(read_data='n'))  # /dev/tty exists
    mock_input = mocker.patch('builtins.input', return_value='n')  # must be windows
    (tmp_path / '.cn').mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit, match=str(install.RC_PATH_EXISTS)):
        # Act
        _run_installer('--uninstall', '--path', str(tmp_path / '.cn'))
    stderr = '\n'.join([args[0][0] for args in mock_stderr.write.call_args_list])

    # Assert
    assert (tmp_path / '.cn').exists()
    assert 'aborted uninstallation' in stderr.lower()

    if mock_open.call_count > 0:
        mock_open.assert_called_once()
        assert mock_input.call_count == 0

    if mock_input.call_count > 0:
        mock_input.assert_called_once()
        assert mock_open.call_count == 0


def test_uninstall(mocker: MockerFixture, tmp_path: Path) -> None:
    """Verify that the uninstall operation is aborted if the user does not confirm."""
    # Arrange
    mock_stdout = mocker.patch('sys.stdout')
    (tmp_path / '.cn').mkdir(parents=True, exist_ok=True)

    # Act
    _run_installer('--uninstall', '--force', '--path', str(tmp_path / '.cn'))
    stdout = '\n'.join([args[0][0] for args in mock_stdout.write.call_args_list])

    # Assert
    assert not (tmp_path / '.cn').exists()
    assert 'uninstalled' in stdout.lower()
    assert str(tmp_path / '.cn').lower() in stdout.lower()
