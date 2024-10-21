"""A simple test to check `config_ninja.__main__`."""

from __future__ import annotations

import sys

from pytest_mock import MockerFixture

from config_ninja import __main__, cli


def test_main(mocker: MockerFixture) -> None:
    """Ensure the `typer` app is called."""
    # Arrange
    mock_app = mocker.patch.object(cli, 'app')
    mocker.patch.object(sys, 'argv', ['config-ninja', 'version'])

    # Act
    __main__.main()

    # Assert
    mock_app.assert_called_once()


def test_main_args(mocker: MockerFixture) -> None:
    """Verify arguments override `sys.argv`."""
    # Arrange
    mock_argv = mocker.patch.object(sys, 'argv')
    mock_sys_exit = mocker.patch.object(sys, 'exit')

    # Act
    __main__.main('version')

    # Assert
    mock_argv.__setitem__.assert_called_once_with(slice(1, None, None), ['version'])
    mock_sys_exit.assert_called_once_with(0)
