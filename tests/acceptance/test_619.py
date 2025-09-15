"""Define acceptance tests for better logging (#619)."""

from __future__ import annotations

import itertools
import logging
from pathlib import Path
from unittest.mock import MagicMock

import click.testing
import pytest
import pytest_mock
import typer
from typer import testing

import pyspry
from config_ninja import cli
from config_ninja import settings as settings_module

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

# pylint: disable=redefined-outer-name


CONFIG_OBJECTS = ['example-local', 'example-local-template']
GLOBAL_OPTION_ANNOTATIONS = {
    'config': cli.ConfigAnnotation,
    'get_help': cli.HelpAnnotation,
    'verbose': cli.VerbosityAnnotation,
    'version': cli.VersionAnnotation,
}


def _recurse_sub_apps(app: typer.Typer | None) -> list[typer.Typer]:
    if not app:
        return []
    return [app] + [sub_app for group in app.registered_groups for sub_app in _recurse_sub_apps(group.typer_instance)]


all_apps = _recurse_sub_apps(cli.app)
typer_cmd_infos = [
    callable
    for app in all_apps
    for callable in app.registered_commands + ([app.registered_callback] if app.registered_callback else [])
    if not callable.deprecated
]

runner = testing.CliRunner()


class TruthT(TypedDict):
    """Type annotation for the structure of the truth dictionary."""

    dest: settings_module.DestSpec
    source: pyspry.Source
    source_path: str


def config_ninja(*args: str) -> click.testing.Result:
    """Run the `config-ninja` command with the given arguments."""
    return runner.invoke(cli.app, args, prog_name='config-ninja')


@pytest.fixture
def settings() -> pyspry.Settings:
    """Return a dictionary with settings for the test."""
    return settings_module.load(Path('config-ninja-settings.yaml')).settings


@pytest.fixture
def mock_rich_print(mocker: pytest_mock.MockFixture) -> MagicMock:
    """Patch the `rich.print` function."""
    return mocker.patch('rich.print')


@pytest.mark.parametrize(('config_key', 'command'), tuple(itertools.product(CONFIG_OBJECTS, ['get', 'apply'])))
def test_output_message_per_config(
    caplog: pytest.LogCaptureFixture,
    settings: pyspry.Settings,
    mock_rich_print: MagicMock,
    config_key: str,
    command: str,
) -> None:
    """Verify that `config-ninja get|apply` prints a single message for each applied controller.

    - `config-ninja apply` should invoke `rich.print` for each controller
    - `config-ninja get` should log a message with the `logging` module for each controller
    """
    # Arrange
    truth: TruthT = {
        'dest': settings_module.DestSpec.from_primitives(settings.OBJECTS[config_key]['dest']),
        'source': (source := settings.OBJECTS[config_key]['source']),
        'source_path': source['init' if 'init' in source else 'new']['kwargs']['path'],
    }
    message = (
        f'{command.capitalize()} [yellow]{config_key}[/yellow]: '
        f'{truth["source_path"]} ({truth["source"]["format"]}) -> {truth["dest"]}'
    )

    # Act
    with caplog.at_level(logging.DEBUG):
        out = config_ninja(command, *CONFIG_OBJECTS)

    # Assert
    assert 0 == out.exit_code, out.stdout
    assert len(CONFIG_OBJECTS) == mock_rich_print.call_count, mock_rich_print.call_args_list

    if command == 'get':
        assert 1 == caplog.messages.count(message)
    else:
        mock_rich_print.assert_any_call(message)


@pytest.mark.usefixtures('monkeypatch_systemd')
@pytest.mark.parametrize(
    'command',
    [
        [],
        ['version'],
        ['get', 'example-local'],
        ['apply', 'example-local'],
        ['self'],
        ['self', 'install'],
        ['self', 'uninstall'],
        ['self', 'print'],
    ],
)
def test_verbosity_argument(command: list[str], caplog: pytest.LogCaptureFixture) -> None:
    """Verify that `config-ninja` commands support the verbosity argument."""
    # Arrange
    command.append('--verbose')

    # Act
    with caplog.at_level(logging.DEBUG):
        out = config_ninja(*command)

    # Assert
    assert 0 == out.exit_code, out.stdout
    assert cli.LOG_VERBOSITY_MESSAGE % 'DEBUG' in caplog.messages, caplog.text


@pytest.mark.parametrize('cmd_func_arg', itertools.product(typer_cmd_infos, GLOBAL_OPTION_ANNOTATIONS))
def test_global_options(cmd_func_arg: tuple[typer.models.CommandInfo | typer.models.TyperInfo, str]) -> None:
    """Verify that all registered commands support the global arguments."""
    cmd_func, arg_name = cmd_func_arg
    assert arg_name in cmd_func.callback.__annotations__, cmd_func.callback
    assert GLOBAL_OPTION_ANNOTATIONS[arg_name] is cmd_func.callback.__annotations__[arg_name], cmd_func.callback
