"""A simple test to check `config_ninja.__main__`."""

from __future__ import annotations

from pytest_mock import MockerFixture

from config_ninja import __main__


def test_main(mocker: MockerFixture) -> None:
    """Ensure the `typer` app is called."""
    # Arrange
    mock_app = mocker.patch.object(__main__, 'app')

    # Act
    __main__.main()

    # Assert
    mock_app.assert_called_once()
