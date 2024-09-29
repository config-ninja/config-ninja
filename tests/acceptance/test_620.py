"""Define acceptance tests for the callback system (#620)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import click.testing
import pytest
import pytest_mock
from typer import testing

from config_ninja import cli, settings

# pylint: disable=redefined-outer-name

runner = testing.CliRunner()
logging_config_file = Path('examples/logging.yaml')


@pytest.fixture
def mock_task_execute_method(mocker: pytest_mock.MockFixture) -> mock.MagicMock:
    """Mock the `poethepoet.task.base.PoeTask.execute` method."""
    return mocker.patch('poethepoet.executor.base.PoeExecutor.execute')


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
    logging_cfg = settings.load(logging_config_file).settings.LOGGING
    logging_level = logging_cfg['loggers']['tests.acceptance.test_620']['level']  # type: ignore[index]

    # Act
    result = config_ninja('self', 'print', '--config', str(logging_config_file))

    # Assert
    assert 0 == result.exit_code
    mock_logging_dict_config.assert_called()
    assert (
        logging_level
        == mock_logging_dict_config.call_args_list[-1][0][0]['loggers']['tests.acceptance.test_620']['level']
    )


def test_hook_is_executed(mock_task_execute_method: mock.MagicMock) -> None:
    """Test that the hooks are executed."""
    result = config_ninja('hook', 'print-environ', 'list-dir')

    assert 0 == result.exit_code, result.stdout
    assert ('printenv',) == mock_task_execute_method.call_args_list[0].args[0]
    assert ('ls',) == mock_task_execute_method.call_args_list[1].args[0]


def test_hook_without_hooks(mock_task_execute_method: mock.MagicMock) -> None:
    """Test that the hook is executed."""
    result = config_ninja('hook', '--config', str(logging_config_file), 'print-environ')

    assert 1 == result.exit_code, result.stdout
    mock_task_execute_method.assert_not_called()
    assert 'failed to load hooks from file' in result.stdout
    assert str(logging_config_file) in result.stdout


def test_hook_undefined(mock_task_execute_method: mock.MagicMock) -> None:
    """Verify that running an undefined hook name raises a `ValueError`."""
    result = config_ninja('hook', 'undefined-hook')
    exc = result.exception

    assert 1 == result.exit_code, result.stdout
    mock_task_execute_method.assert_not_called()

    assert exc is not None
    assert ValueError is exc.__class__
    assert 'Undefined hook' in exc.args[0]
