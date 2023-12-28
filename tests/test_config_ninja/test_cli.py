"""Execute tests for the CLI."""
from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from pytest_mock import MockerFixture
from tests.fixtures import MOCK_YAML_CONFIG
from typer.testing import CliRunner

import config_ninja
from config_ninja.cli import app

if TYPE_CHECKING:  # pragma: no cover
    pass

runner = CliRunner()


def test_help() -> None:
    """Verify the `-h` argument matches `--help` and the default command."""
    results = [runner.invoke(app, args) for args in ([], ['-h'], ['--help'])]

    assert all(result.exit_code == 0 for result in results)
    assert all(result.stdout == results[0].stdout for result in results[1:])


def test_version() -> None:
    """Verify the `version` command returns the correct version."""
    result = runner.invoke(app, ['version'])

    assert result.exit_code == 0
    assert result.stdout.strip() == config_ninja.__version__


def test_missing_settings(mocker: MockerFixture) -> None:
    """Verify errors are handled correctly when the settings file is missing."""
    mocker.patch(
        'config_ninja.resolve_settings_path',
        side_effect=FileNotFoundError(
            'Could not find config-ninja settings', config_ninja.DEFAULT_SETTINGS_PATHS
        ),
    )
    result = runner.invoke(app, ['version'])

    assert result.exit_code == 0
    assert all(
        [
            text in result.stdout
            for text in ['WARNING', 'Could not find', 'config-ninja', 'settings file']
        ]
    )


def test_get_hello_world(mock_full_session: boto3.Session) -> None:
    """Get the 'hello_world' configuration."""
    result = runner.invoke(app, ['get', 'example-1'])
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == MOCK_YAML_CONFIG.decode('utf-8')
