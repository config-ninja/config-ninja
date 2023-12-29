"""Backend implementations for third-party integrations."""
from __future__ import annotations

import importlib

from config_ninja.backend import Backend


def get_backend(name: str) -> type[Backend]:
    """Retrieve the backend class for the given name."""
    module = importlib.import_module(f'config_ninja.contrib.{name}')
    for val in module.__dict__.values():
        try:
            is_subclass = issubclass(val, Backend)
        except TypeError:
            continue

        if is_subclass and val is not Backend:
            return val  # type: ignore[no-any-return]  # is_subclass ensures the correct type

    raise ValueError(f'No backend found for {name}')
