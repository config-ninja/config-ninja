"""Backend implementations for third-party integrations.

Each backend is implemented as a subclass of `config_ninja.backend.Backend` in a module of this
package. The `get_backend()` function is used to retrieve the backend class given its module name.

## Available Backends

- `config_ninja.contrib.appconfig`
- `config_ninja.contrib.local`
"""
from __future__ import annotations

import importlib

from config_ninja.backend import Backend


def get_backend(name: str) -> type[Backend]:
    """Import the `config_ninja.backend.Backend` subclass for the given module name."""
    module = importlib.import_module(f'config_ninja.contrib.{name}')
    for val in module.__dict__.values():
        try:
            is_subclass = issubclass(val, Backend)
        except TypeError:
            continue

        if is_subclass and val is not Backend:
            return val  # type: ignore[no-any-return]  # is_subclass ensures the correct type

    raise ValueError(f'No backend found for {name}')  # pragma: no cover
