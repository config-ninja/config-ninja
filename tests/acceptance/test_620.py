"""Define acceptance tests for the callback system (#620)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import click.testing
from typer import testing

from config_ninja import cli, settings

runner = testing.CliRunner()


def config_ninja(*args: str) -> click.testing.Result:
    """Run the `config-ninja` command with the given arguments."""
    return runner.invoke(cli.app, args, prog_name='config-ninja')


def test_default_logging_level(mock_logging_dict_config: mock.MagicMock) -> None:
    """Test the null result (the level of `logger` is not set)."""
    result = config_ninja('self', 'print')

    assert 0 == result.exit_code
    mock_logging_dict_config.assert_called()
    assert settings.DEFAULT_LOGGING_CONFIG == mock_logging_dict_config.call_args_list[-1][0][0]


def test_logging_level(mock_logging_dict_config: mock.MagicMock) -> None:
    """Test the null result (the level of `logger` is not set)."""
    # Arrange
    config_file = Path('examples/logging.yaml')
    logging_cfg = settings.load(config_file).LOGGING
    logging_level = logging_cfg['loggers']['tests.acceptance.test_620']['level']  # type: ignore[index]

    # Act
    result = config_ninja('self', 'print', '--config', str(config_file))

    # Assert
    assert 0 == result.exit_code
    mock_logging_dict_config.assert_called()
    assert (
        logging_level
        == mock_logging_dict_config.call_args_list[-1][0][0]['loggers']['tests.acceptance.test_620']['level']
    )
