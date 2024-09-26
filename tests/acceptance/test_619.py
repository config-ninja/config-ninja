"""Define acceptance tests for better logging (#619)."""

from __future__ import annotations

import re
from pathlib import Path

import pyspry
import pytest

import config_ninja

try:
    import sh
except ImportError:
    pytest.skip('the tests in this module require `sh`', allow_module_level=True)

# pylint: disable=redefined-outer-name


CONFIG_OBJECTS = ['example-local', 'example-local-template']


@pytest.fixture
def settings() -> pyspry.Settings:
    """Return a dictionary with settings for the test."""
    return config_ninja.load_settings(Path('config-ninja-settings.yaml'))


@pytest.mark.parametrize('key', CONFIG_OBJECTS)
def test_output_message_per_config(settings: pyspry.Settings, key: str) -> None:
    """Verify that `config-ninja apply` prints a single message for each applied controller."""
    # Arrange
    dest = settings.OBJECTS[key]['dest']
    source = settings.OBJECTS[key]['source']
    src_path = source['init' if 'init' in source else 'new']['kwargs']['path']

    # Act
    out = sh.config_ninja('apply', *CONFIG_OBJECTS)
    no_colors = re.sub(r'\x1b\[[01359][35]?m', '', out)

    # Assert
    assert f'Apply {key}' in no_colors, no_colors
    assert dest['path'] in no_colors, no_colors
    assert source['format'] in no_colors, no_colors
    assert src_path in no_colors, no_colors
