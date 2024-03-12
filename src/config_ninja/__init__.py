""".. include:: ../../README.md

# Navigation
- `config_ninja.contrib` for supported backends:
    - `config_ninja.contrib.appconfig`
    - `config_ninja.contrib.local`
- `config_ninja.cli` for commands and CLI documentation
- `config_ninja.systemd` for `systemd` integration
"""  # noqa: D415

from __future__ import annotations

__version__ = '0.0.0'

from pathlib import Path

from pyspry import Settings

__all__ = ['DEFAULT_SETTINGS_PATHS', 'load_settings', 'resolve_settings_path']

DEFAULT_SETTINGS_PATHS = [
    Path.cwd() / 'config-ninja-settings.yaml',
    Path.home() / 'config-ninja-settings.yaml',
    Path('/etc/config-ninja/settings.yaml'),
]
"""Check each of these locations for `config-ninja`_'s settings file.

The following locations are checked (ordered by priority):

1. `./config-ninja-settings.yaml`
2. `~/config-ninja-settings.yaml`
3. `/etc/config-ninja/settings.yaml`

.. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
"""

SETTINGS_PREFIX = 'CONFIG_NINJA'


def load_settings(path: Path) -> Settings:
    """Load the settings from the given path."""
    return Settings.load(path, SETTINGS_PREFIX)


def resolve_settings_path() -> Path:
    """Return the first path in `DEFAULT_SETTINGS_PATHS` that exists."""
    for path in DEFAULT_SETTINGS_PATHS:
        if path.is_file():
            return path

    raise FileNotFoundError('Could not find config-ninja settings', DEFAULT_SETTINGS_PATHS)
