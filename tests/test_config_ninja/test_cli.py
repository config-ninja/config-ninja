"""Execute tests for the CLI."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Sequence

import boto3
import pytest
import tomlkit
import yaml
from pytest_mock import MockerFixture
from tests.fixtures import MOCK_YAML_CONFIG
from typer.testing import CliRunner

import config_ninja
from config_ninja.cli import app

runner = CliRunner()


def clean(text: str) -> str:
    """Remove hex/ANSI codes and leading/trailing newlines from the given string."""
    return re.sub(r'\x1b\[[0-9;]+m', '', text).strip()


@pytest.fixture()
def settings(settings_text: str) -> dict[str, Any]:
    """Parse the settings file and return its contents as a `dict`."""
    out: dict[str, Any] = yaml.safe_load(settings_text)
    return out


@pytest.fixture()
def settings_text() -> str:
    """Resolve the path to the settings file and return its contents as a string."""
    out: str = config_ninja.resolve_settings_path().read_text().strip()
    return out


@pytest.mark.parametrize('args', [[], ['-h'], ['--help']])
def test_help(args: Sequence[str]) -> None:
    """Verify the `-h` argument matches `--help` and the default command."""
    results = runner.invoke(app, args)
    stdout = clean(results.stdout)
    assert results.exit_code == 0
    assert stdout.startswith('Usage')


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


def test_get_example_local_poll(mocker: MockerFixture, settings_text: str) -> None:
    """Test the `poll` command with a local file."""
    # Arrange
    mocker.patch('config_ninja.contrib.local.watch', return_value=iter([None]))

    # Act
    result = runner.invoke(app, ['get', '--poll', 'example-local'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == settings_text


def test_self_print() -> None:
    """Test the `self print` command."""
    result = runner.invoke(app, ['self', 'print'])

    assert result.exit_code == 0, result.exception
    assert 'example-local' in result.stdout.strip()
    assert 'example-appconfig' in result.stdout.strip()


def test_apply_example_local(settings: dict[str, Any]) -> None:
    """Execute the `apply` command for a local file backend."""
    result = runner.invoke(app, ['apply', 'example-local'])
    output = (
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local']['dest']['path']).read_text().strip()
    )

    assert result.exit_code == 0, result.exception
    assert output == json.dumps(settings)


def test_apply_example_local_template(settings: dict[str, Any]) -> None:
    """Execute the `apply` command for a local file backend."""
    result = runner.invoke(app, ['apply', 'example-local-template'])
    output = (
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']['path'])
        .read_text()
        .strip()
    )

    assert result.exit_code == 0, result.exception
    assert (
        output
        == tomlkit.dumps(  # pyright: ignore[reportUnknownMemberType]
            {
                'CONFIG_NINJA_OBJECTS': {
                    'example-local-template': {
                        'dest': settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']
                    }
                }
            }
        ).strip()
    )


def test_apply_example_local_poll(
    mocker: MockerFixture, settings_text: str, settings: dict[str, Any]
) -> None:
    """Test the `apply --poll` command with a local file backend."""
    # Arrange
    mocker.patch('config_ninja.contrib.local.watch', return_value=iter([settings_text]))

    # Act
    result = runner.invoke(app, ['apply', '--poll', 'example-local'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert Path(
        settings['CONFIG_NINJA_OBJECTS']['example-local']['dest']['path']
    ).read_text().strip() == json.dumps(settings)


def test_apply_example_local_template_poll(
    mocker: MockerFixture, settings_text: str, settings: dict[str, Any]
) -> None:
    """Test the `apply --poll` command with a local file backend."""
    # Arrange
    mocker.patch('config_ninja.contrib.local.watch', return_value=iter([settings_text]))

    # Act
    result = runner.invoke(app, ['apply', '--poll', 'example-local-template'])
    output = (
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']['path'])
        .read_text()
        .strip()
    )

    assert result.exit_code == 0, result.exception
    assert (
        output
        == tomlkit.dumps(  # pyright: ignore[reportUnknownMemberType]
            {
                'CONFIG_NINJA_OBJECTS': {
                    'example-local-template': {
                        'dest': settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']
                    }
                }
            }
        ).strip()
    )
