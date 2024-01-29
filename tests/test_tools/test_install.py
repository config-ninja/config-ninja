"""Define tests for the `install` script."""
from __future__ import annotations

import importlib
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest
from pytest_mock import MockerFixture

from tools import install


def _run_installer(*argv: str) -> None:
    importlib.reload(install).main(*argv)


@pytest.fixture()
def _mock_ensurepip(mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Raise an `ImportError` if `importlib.import_module` is passed 'ensurepip'."""

    def _mock_import_module(name: str, package: str | None = None) -> ModuleType:
        if name == 'ensurepip':
            raise ImportError('Mocked!')
        return import_module(name, package=package)

    mocker.patch('importlib.import_module', new=_mock_import_module)


def test_unsupported_python(mocker: MockerFixture) -> None:
    """Test that the install script fails on Python 3.7."""
    mocker.patch('sys.version_info', (3, 7))

    with pytest.raises(SystemExit, match='1'):
        _run_installer()


def test_install_path_exists() -> None:
    """Test that the install script fails if the install path exists."""
    # Assert
    with pytest.raises(FileExistsError):
        # Act
        _run_installer('--path', '.')


@pytest.mark.usefixtures('_mock_ensurepip', '_mock_install_io', '_mock_urlopen_for_pypi')
def test_uses_virtualenv(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test that the install script falls back to using virtualenv."""
    # Arrange
    mock_run_path = mocker.patch('runpy.run_path')

    # Act
    _run_installer('--path', str(tmp_path / '.cn'))

    # Assert
    mock_run_path.assert_called_once()
    assert mock_run_path.call_args.args
    assert mock_run_path.call_args.args[0].endswith('virtualenv.pyz')
