""".. include:: ../../README.md"""  # noqa: D415
from __future__ import annotations

__version__ = '0.0.0'

from pathlib import Path

from pyspry import Settings

DEFAULT_SETTINGS_PATHS = [
    Path.cwd() / 'config-ninja-settings.yaml',
    Path.home() / 'config-ninja-settings.yaml',
    Path('/etc/config-ninja/settings.yaml'),
]
SETTINGS_PREFIX = 'CONFIG_NINJA'


def load_settings(path: Path) -> Settings:
    """Load the settings from the given path."""
    return Settings.load(path, SETTINGS_PREFIX)


def resolve_settings_path() -> Path:
    """Locate the settings file."""
    for path in DEFAULT_SETTINGS_PATHS:
        if path.is_file():
            return path

    raise FileNotFoundError('Could not find config-ninja settings', DEFAULT_SETTINGS_PATHS)
