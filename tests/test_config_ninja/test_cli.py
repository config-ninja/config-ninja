"""Execute tests for the CLI."""
from __future__ import annotations

import json
import re
import string
import uuid
from pathlib import Path
from typing import Any, AsyncIterable, Sequence

import pyspry
import pytest
import sh
import tomlkit
import yaml
from pytest_mock import MockerFixture
from typer.testing import CliRunner

import config_ninja
from config_ninja import cli, systemd
from config_ninja.cli import app
from tests.fixtures import MOCK_YAML_CONFIG

# pylint: disable=redefined-outer-name

SYSTEMD_AVAILABLE = hasattr(sh, 'systemctl')

runner = CliRunner()


def clean(text: str) -> str:
    """Remove hex/ANSI codes and leading/trailing newlines from the given string."""
    return re.sub(r'\x1b\[[0-9;]+m', '', text).strip()


@pytest.fixture()
def settings_text() -> str:
    """Resolve the path to the settings file and return its contents as a string."""
    return str(config_ninja.resolve_settings_path().read_text()).strip()


@pytest.fixture()
def settings(settings_text: str) -> dict[str, Any]:
    """Parse the settings file and return its contents as a `dict`."""
    out: dict[str, Any] = yaml.safe_load(settings_text)
    return out


@pytest.fixture()
def _patch_awatch(settings_text: str, mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Patch `watchfiles.awatch` to yield a single string."""

    async def mock_awatch(*_: Any, **__: Any) -> AsyncIterable[str]:
        yield settings_text

    mocker.patch('config_ninja.contrib.local.awatch', new=mock_awatch)


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


@pytest.mark.usefixtures('mock_full_session')
def test_get_example_appconfig() -> None:
    """Get the 'example-appconfig' configuration (as specified in config-ninja-settings.yaml)."""
    result = runner.invoke(app, ['get', 'example-appconfig'])
    assert result.exit_code == 0, result.exception
    assert result.stdout.strip() == MOCK_YAML_CONFIG.decode('utf-8')


def test_get_example_local(settings: dict[str, Any]) -> None:
    """Get the 'example-local' configuration (as specified in config-ninja-settings.yaml)."""
    result = runner.invoke(app, ['get', 'example-local'])
    assert result.exit_code == 0, result.exception
    assert result.stdout.replace('\n', '').strip() == json.dumps(settings)


@pytest.mark.usefixtures('_patch_awatch')
@pytest.mark.usefixtures('monkeypatch_systemd')
def test_get_example_local_poll(mocker: MockerFixture, settings: dict[str, Any]) -> None:
    """Test the `poll` command with a local file."""
    # Arrange
    mock_print = mocker.patch('config_ninja.cli.print')
    expected_call_count = 2  # 1 for the initial print, 2 for the patched awatch()

    # Act
    result = runner.invoke(app, ['get', '--poll', 'example-local'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert mock_print.call_count == expected_call_count
    assert (
        mock_print.call_args_list[0][0][0].strip()
        == mock_print.call_args_list[1][0][0].strip()
        == json.dumps(settings)
    )


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
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local']['dest']['path'])
        .read_text(encoding='utf-8')
        .strip()
    )

    assert result.exit_code == 0, result.exception
    assert output == json.dumps(settings)


def test_apply_example_local_template(settings: dict[str, Any]) -> None:
    """Execute the `apply` command for a local file backend."""
    result = runner.invoke(app, ['apply', 'example-local-template'])
    output = (
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']['path'])
        .read_text(encoding='utf-8')
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


@pytest.mark.usefixtures('_patch_awatch')
@pytest.mark.usefixtures('monkeypatch_systemd')
def test_apply_example_local_poll(settings: dict[str, Any]) -> None:
    """Test the `apply --poll` command with a local file backend."""
    result = runner.invoke(app, ['apply', '--poll', 'example-local'])

    assert result.exit_code == 0, result.exception
    assert Path(settings['CONFIG_NINJA_OBJECTS']['example-local']['dest']['path']).read_text(
        encoding='utf-8'
    ).strip() == json.dumps(settings)


@pytest.mark.usefixtures('_patch_awatch')
@pytest.mark.usefixtures('monkeypatch_systemd')
def test_apply_example_local_template_poll(settings: dict[str, Any]) -> None:
    """Test the `apply --poll` command with a local file backend."""
    result = runner.invoke(app, ['apply', '--poll', 'example-local-template'])
    output = (
        Path(settings['CONFIG_NINJA_OBJECTS']['example-local-template']['dest']['path'])
        .read_text(encoding='utf-8')
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


@pytest.mark.usefixtures('_patch_awatch')
@pytest.mark.usefixtures('monkeypatch_systemd')
def test_monitor_local(settings: dict[str, Any]) -> None:
    """Test the `monitor` command with a local file backend."""
    # Arrange
    local_settings = pyspry.Settings.load('examples/local-backend.yaml', 'CONFIG_NINJA')

    # Act
    result = runner.invoke(app, ['--config', 'examples/local-backend.yaml', 'monitor'])
    paths = [
        Path(local_settings.OBJECTS[obj]['dest']['path']) for obj in ('example-0', 'example-1')
    ]
    outputs = [p.read_text().strip() for p in paths]

    # Assert
    assert result.exit_code == 0, result.exception
    assert outputs[0] == json.dumps(settings)
    assert (
        outputs[1]
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


def test_install_no_systemd(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the `install` command fails gracefully when `systemd` is not available."""
    # Arrange
    monkeypatch.setattr(cli, 'SYSTEMD_AVAILABLE', False)

    # Act
    result = runner.invoke(app, ['self', 'install'])

    # Assert
    assert result.exit_code != 0
    assert result.stdout.startswith('ERROR: Missing systemd!')


@pytest.mark.usefixtures('monkeypatch_systemd')
def test_install() -> None:
    """Verify the `install` command works as expected."""
    result = runner.invoke(app, ['self', 'install'])

    assert result.exit_code == 0, result.exception
    assert result.stdout.startswith('Installing')
    assert 'SUCCESS' in result.stdout


def _clean_output(text: str) -> str:
    return re.sub(f'[^{string.ascii_letters + string.digits + string.punctuation}]', '', text)


def test_install_print_only() -> None:
    """Verify the `install` command respects the `--print-only` argument."""
    result = runner.invoke(app, ['self', 'install', '--print-only'])

    assert result.exit_code == 0, result.exception
    assert str(systemd.SYSTEM_INSTALL_PATH) in _clean_output(result.stdout)


@pytest.mark.usefixtures('monkeypatch_systemd')
def test_uninstall() -> None:
    """Verify the `uninstall` command works as expected."""
    # Arrange
    content = str(uuid.uuid4())
    systemd.USER_INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    (systemd.USER_INSTALL_PATH / systemd.SERVICE_NAME).write_text(content)

    # Act
    result = runner.invoke(app, ['self', 'uninstall', '--user'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert result.stdout.startswith('Uninstalling')
    assert 'SUCCESS' in result.stdout


@pytest.mark.usefixtures('monkeypatch_systemd')
def test_uninstall_print_only() -> None:
    """Verify the `uninstall` command respects the `--print-only` argument."""
    # Arrange
    content = str(uuid.uuid4())
    systemd.SYSTEM_INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    (systemd.SYSTEM_INSTALL_PATH / systemd.SERVICE_NAME).write_text(content)

    # Act
    result = runner.invoke(app, ['self', 'uninstall', '--print-only'])

    # Assert
    assert result.exit_code == 0, result.exception
    assert str(systemd.SYSTEM_INSTALL_PATH) in _clean_output(result.stdout)
    assert content in result.stdout
