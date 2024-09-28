"""Type stubs for the `pyspry` library."""

# pylint: disable=useless-import-alias

from __future__ import annotations

from pathlib import Path

from config_ninja.settings import ConfigNinjaObject
from config_ninja.settings import Dest as Dest
from config_ninja.settings import Source as Source

class Settings:
    OBJECTS: dict[str, ConfigNinjaObject]

    @classmethod
    def load(cls, file_path: Path | str, prefix: str | None = None) -> Settings: ...
