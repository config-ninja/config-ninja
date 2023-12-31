from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias, TypedDict

from config_ninja.backend import FormatT

class InitType(TypedDict):
    """Initialization parameters for the backend class."""

    kwargs: dict[str, str]

class NewType(TypedDict):
    """Initialization parameters for the backend class."""

    kwargs: dict[str, str]

class SourceType(TypedDict):
    """Describe the source of configuration data written to a `DestType`.

    The parameters `init` and `backend` are mutually exclusive.
    """

    backend: Literal['local', 'appconfig']
    format: FormatT
    """Deserialize the source data from this format.

    Defaults to `'raw'`.
    """

    init: InitType
    """Pass these parameters to the backend's `__init__` method.

    These are typically unique identifiers; more friendly names can instead be passed to the `new`
    method.
    """

    new: NewType
    """Pass these parameters to the backend's `new` method.

    If this property is defined, the `init` property is ignored.
    """

PathStr: TypeAlias = str

class DestType(TypedDict):
    """The parameters `output` and `template` are mutually exclusive."""

    path: str
    """Write the configuration file to this path"""

    format: FormatT | PathStr
    """Set the output serialization format of the destination file.

    If given the path to a file, interpret the file as a Jinja2 template and render it with the
    source data.
    """

class ConfigNinjaObject(TypedDict):
    """Specify information needed to manage a configuration file."""

    dest: DestType
    source: SourceType

class Settings:
    OBJECTS: dict[str, ConfigNinjaObject]

    @classmethod
    def load(cls, file_path: Path | str, prefix: str | None = None) -> Settings: ...
