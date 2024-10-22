"""Define acceptance tests for the callback system (#620)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import click.testing
import pytest
import pytest_mock
from typer import testing

from config_ninja import cli, settings

try:
    from poethepoet import exceptions  # pyright: ignore[reportMissingTypeStubs]
except ImportError:  # pragma: no cover
    pytest.skip('poethepoet is not installed', allow_module_level=True)

# pylint: disable=redefined-outer-name

runner = testing.CliRunner()
logging_config_file = Path('examples/logging.yaml')


@pytest.fixture
def mock_get_execution_plan(mocker: pytest_mock.MockerFixture) -> mock.MagicMock:
    """Mock the `poethepoet.task.graph.TaskExecutionGraph.get_execution_plan` method."""
    mocked = mocker.patch('poethepoet.task.graph.TaskExecutionGraph.get_execution_plan')
    mocked.return_value = []
    return mocked


@pytest.fixture
def mock_task_execute_method(mocker: pytest_mock.MockFixture) -> mock.MagicMock:
    """Mock the `poethepoet.task.base.PoeTask.execute` method."""
    mocked = mocker.patch('poethepoet.executor.base.PoeExecutor.execute')
    mocked.return_value = 0
    return mocked


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


def test_example_callback(mock_task_execute_method: mock.MagicMock) -> None:
    """Test that the example hook is executed for the example-local config object."""
    result = config_ninja('apply', 'example-local')

    assert 0 == result.exit_code, result.stdout
    mock_task_execute_method.assert_called_once()
    assert ('ls',) == mock_task_execute_method.call_args_list[0].args[0]


def test_multi_callback(mock_task_execute_method: mock.MagicMock) -> None:
    """Test that the complex sequence hook is executed for the example-local-template config object."""
    num_tasks = 3
    result = config_ninja('apply', 'example-local-template')

    assert 0 == result.exit_code, result.stdout
    assert num_tasks == mock_task_execute_method.call_count
    assert ('ls',) == mock_task_execute_method.call_args_list[0].args[0]
    assert ('printenv',) == mock_task_execute_method.call_args_list[1].args[0]
    assert ('echo', 'success') == mock_task_execute_method.call_args_list[2].args[0]


def test_execution_error(mocker: pytest_mock.MockerFixture) -> None:
    """Verify behavior when a hook fails to execute."""
    mocked = mocker.patch(
        'poethepoet.executor.base.PoeExecutor.execute', side_effect=exceptions.ExecutionError('error executing hook')
    )

    result = config_ninja('apply', 'example-local')

    assert 1 == result.exit_code, result.stdout
    mocked.assert_called_once()

    assert exceptions.ExecutionError is result.exception.__class__


def test_multi_execution_error(mock_task_execute_method: mock.MagicMock) -> None:
    """Verify behavior when a command from a graph task returns a nonzero value."""
    mock_task_execute_method.return_value = 1

    result = config_ninja('apply', 'example-local-template')

    assert 1 == result.exit_code, result.stdout
    mock_task_execute_method.assert_called_once()

    assert exceptions.ExecutionError is result.exception.__class__


def test_that_last_sliver_of_missing_code_coverage(
    mock_get_execution_plan: mock.MagicMock, mock_task_execute_method: mock.MagicMock
) -> None:
    """Execute the scenario when `plan == []` inside `HooksEngine.run_task_graph()`."""
    result = config_ninja('apply', 'example-local-template')

    assert 0 == result.exit_code, result.stdout
    mock_get_execution_plan.assert_called_once()

    # the mocked `TaskExecutionGraph.get_execution_plan()` returns an empty list (without tasks to execute)
    mock_task_execute_method.assert_not_called()
