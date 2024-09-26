"""Define acceptance tests for better logging (#619)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import click.testing
import pyspry
import pytest
import pytest_mock
from typer import testing

import config_ninja as cn
from config_ninja import cli, controller

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

# pylint: disable=redefined-outer-name


CONFIG_OBJECTS = ['example-local', 'example-local-template']

runner = testing.CliRunner()


class TruthT(TypedDict):
    """Type annotation for the structure of the truth dictionary."""

    dest: controller.DestSpec
    source: pyspry.SourceType
    source_path: str


def config_ninja(*args: str) -> click.testing.Result:
    """Run the `config-ninja` command with the given arguments."""
    return runner.invoke(cli.app, args, prog_name='config-ninja')


@pytest.fixture
def settings() -> pyspry.Settings:
    """Return a dictionary with settings for the test."""
    return cn.load_settings(Path('config-ninja-settings.yaml'))  # type: ignore[no-any-return,unused-ignore]


@pytest.fixture
def mock_rich_print(mocker: pytest_mock.MockFixture) -> MagicMock:
    """Patch the `rich.print` function."""
    return mocker.patch('rich.print')  # type: ignore[no-any-return]


@pytest.mark.parametrize('config_key', CONFIG_OBJECTS)
def test_output_message_per_config(settings: pyspry.Settings, mock_rich_print: MagicMock, config_key: str) -> None:
    """Verify that `config-ninja apply` prints a single message for each applied controller."""
    # Arrange
    truth: TruthT = {
        'dest': controller.DestSpec.from_primitives(settings.OBJECTS[config_key]['dest']),
        'source': (source := settings.OBJECTS[config_key]['source']),
        'source_path': source['init' if 'init' in source else 'new']['kwargs']['path'],
    }

    # Act
    out = config_ninja('apply', *CONFIG_OBJECTS)

    # Assert
    assert 0 == out.exit_code, out.stdout
    assert len(CONFIG_OBJECTS) == mock_rich_print.call_count, mock_rich_print.call_args_list
    mock_rich_print.assert_any_call(
        f'Apply [yellow]{config_key}[/yellow]: '
        f'{truth["source_path"]} ({truth["source"]["format"]}) -> {truth["dest"]}'
    )
