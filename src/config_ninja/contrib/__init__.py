"""Backend implementations for third-party integrations."""
from __future__ import annotations

import importlib

from config_ninja.backend import AbstractBackend


def get_backend(name: str) -> type[AbstractBackend]:
    """Retrieve the backend class for the given name."""
    module = importlib.import_module(f'config_ninja.contrib.{name}')
    for val in module.__dict__.values():
        try:
            is_subclass = issubclass(val, AbstractBackend)
        except TypeError:
            continue

        if is_subclass and val is not AbstractBackend:
            return val  # type: ignore[no-any-return]  # is_subclass ensures the correct type

    raise ValueError(f'No backend found for {name}')
