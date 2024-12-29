""".. include:: ../../README.md

# Navigation

## `config_ninja.cli`

Commands and CLI documentation.

## `config_ninja.contrib`

For supported backends.

### `config_ninja.contrib.appconfig`

Integrate with the AWS AppConfig service.

### `config_ninja.contrib.local`

Use a local file as the backend.

### `config_ninja.contrib.secretsmanager`

Integrate with the AWS SecretsManager service.

## `config_ninja.hooks`

Execute [`poethepoet`](https://poethepoet.natn.io/) tasks as callback hooks for backend updates.

## `config_ninja.settings`

For settings and configuration.

## `config_ninja.systemd`

Integration with `systemd`.
"""  # noqa: D415

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

import pyspry

__version__ = '0.0.0'

from config_ninja.settings import DEFAULT_PATHS, load
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


def load_settings(path: Path) -> pyspry.Settings:  # pragma: no cover
    """(deprecated) Load the settings file at the given path.

    This function is deprecated and will be removed in a future release. Use `config_ninja.settings.load()` instead.
    """
    warnings.warn(
        '`config_ninja.load_settings()` is deprecated and will be removed in a future release. Use '
        '`config_ninja.settings.load()` instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return load(path).settings


def main(*args: Any) -> None:  # pylint: disable=missing-function-docstring
    """Entrypoint for the `config-ninja` CLI.

    When arguments are provided, they are used to replace `sys.argv[1:]`.
    """
    if args:
        sys.argv[1:] = list(args)

    from config_ninja.cli import app

    app(prog_name='config-ninja')
