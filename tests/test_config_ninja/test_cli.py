"""Execute tests for the CLI."""
from __future__ import annotations

from pathlib import Path

import boto3
import pytest
from pytest_mock import MockerFixture
from tests.fixtures import MOCK_YAML_CONFIG
from typer.testing import CliRunner

import config_ninja
from config_ninja.cli import app

runner = CliRunner()


@pytest.fixture()
def settings_text() -> str:
    """Resolve the path to the settings file and return its contents as a string."""
    return config_ninja.resolve_settings_path().read_text().strip()


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
    # Arrange
    mocker.patch('config_ninja.DEFAULT_SETTINGS_PATHS', new=[Path('does not'), Path('exist')])

    # Act
    result = runner.invoke(app, ['self', 'print'])

    # Assert
    assert result.exit_code == 0
    assert all(
        [
            text in result.stdout
            for text in ['WARNING', 'Could not find', 'config-ninja', 'settings file']
        ]
    )


def test_get_example_appconfig(mock_full_session: boto3.Session) -> None:
    """Get the 'example-appconfig' configuration (as specified in config-ninja-settings.yaml)."""
    result = runner.invoke(app, ['get', 'example-appconfig'])
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == MOCK_YAML_CONFIG.decode('utf-8')


def test_get_example_local(settings_text: str) -> None:
    """Get the 'example-local' configuration (as specified in config-ninja-settings.yaml)."""
    result = runner.invoke(app, ['get', 'example-local'])
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == settings_text


def test_poll_example_local(mocker: MockerFixture, settings_text: str) -> None:
    """Test the `poll` command with a local file."""
    # Arrange
    mocker.patch('config_ninja.contrib.local.watch', return_value=iter([None]))

    # Act
    result = runner.invoke(app, ['poll', 'example-local'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == settings_text


def test_self_print() -> None:
    """Test the `self print` command."""
    result = runner.invoke(app, ['self', 'print'])

    assert result.exit_code == 0, result.exception
    assert 'example-local' in result.stdout.strip()
    assert 'example-appconfig' in result.stdout.strip()
