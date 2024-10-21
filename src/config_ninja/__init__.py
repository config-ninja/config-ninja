""".. include:: ../../README.md

# Navigation

## `config_ninja.contrib`

For supported backends.

### `config_ninja.contrib.appconfig`

Integrate with the AWS AppConfig service.

### `config_ninja.contrib.local`

Use a local file as the backend.

## `config_ninja.cli`

Commands and CLI documentation.

## `config_ninja.settings`

For settings and configuration.

## `config_ninja.systemd`

Integration with `systemd`.
"""  # noqa: D415

from __future__ import annotations

__version__ = '0.0.0'

from config_ninja.settings import DEFAULT_PATHS
from config_ninja.settings import load as load_settings
from config_ninja.settings import resolve_path as resolve_settings_path

__all__ = ['DEFAULT_SETTINGS_PATHS', 'load_settings', 'resolve_settings_path']

DEFAULT_SETTINGS_PATHS = DEFAULT_PATHS
"""Check each of these locations for `config-ninja`_'s settings file.

The following locations are checked (ordered by priority):

1. `./config-ninja-settings.yaml`
2. `~/config-ninja-settings.yaml`
3. `/etc/config-ninja/settings.yaml`

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""
