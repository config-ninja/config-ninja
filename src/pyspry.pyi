"""Type stubs for the `pyspry` library."""

# pylint: disable=useless-import-alias

from __future__ import annotations

from pathlib import Path

import pyspry.base

from config_ninja.settings.schema import ConfigNinjaObject, DictConfig
from config_ninja.settings.schema import Dest as Dest
from config_ninja.settings.schema import Source as Source

# pylint: disable=unused-argument,missing-class-docstring,missing-function-docstring

class Settings:
    LOGGING: DictConfig | pyspry.base.Null
    OBJECTS: dict[str, ConfigNinjaObject]

    @classmethod
    def load(cls, file_path: Path | str, prefix: str | None = None) -> Settings: ...
