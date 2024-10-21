"""Read and deserialize configuration for the `config-ninja`_ agent.

The `typing.TypedDict` classes in this module describe the structure of the `config-ninja` settings file:

```yaml
CONFIG_NINJA_OBJECTS:
```
```yaml
    example-1:
      dest:
        format: templates/settings-subset.toml.j2
        path: /tmp/config-ninja/local/subset.toml

      source:
        backend: local
        format: yaml

        new:
          kwargs:
            path: config-ninja-settings.yaml
```

This YAML file would be parsed into a dictionary of the following structure:

- `CONFIG_NINJA_OBJECTS:`
  - `example-1:`  (`ConfigNinjaObject`)
    - `dest:`  (`Dest`)
      - `...`
    - `source:`  (`Source`)
      - `...`


.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import Literal, TypedDict

import jinja2
import pyspry

from config_ninja.backend import DUMPERS, Backend, FormatT
from config_ninja.contrib import get_backend

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

__all__ = [
    'ConfigNinjaObject',
    'DEFAULT_PATHS',
    'DestSpec',
    'Dest',
    'Init',
    'New',
    'ObjectSpec',
    'PREFIX',
    'PathStr',
    'SourceSpec',
    'Source',
    'load',
    'resolve_path',
]

logger = logging.getLogger(__name__)

DEFAULT_PATHS = [
    Path.cwd() / 'config-ninja-settings.yaml',
    Path.home() / 'config-ninja-settings.yaml',
    Path('/etc/config-ninja/settings.yaml'),
]
"""Check each of these locations for `config-ninja`_'s settings file.

The following locations are checked (ordered by priority):

1. `./config-ninja-settings.yaml`
2. `~/config-ninja-settings.yaml`
3. `/etc/config-ninja/settings.yaml`

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

PREFIX = 'CONFIG_NINJA'
"""Each of `config-ninja`_'s settings must be prefixed with this string.

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""


def load(path: Path) -> pyspry.Settings:
    """Load the settings from the given path."""
    return pyspry.Settings.load(path, PREFIX)


def resolve_path() -> Path:
    """Return the first path in `DEFAULT_SETTINGS_PATHS` that exists."""
    for path in DEFAULT_PATHS:
        if path.is_file():
            return path

    raise FileNotFoundError('Could not find config-ninja settings', DEFAULT_PATHS)


class Init(TypedDict):
    """Initialization parameters for the backend class.

    ```yaml
    CONFIG_NINJA_OBJECTS:
      example-1:
        source:
    ```
    ```yaml
          init:
            kwargs:
              path: config-ninja-settings.yaml
    ```
    """

    kwargs: dict[str, str]
    """Pass these values as arguments to the `config_ninja.backend.Backend`'s `__init__()` method."""


class New(TypedDict):
    """Initialization parameters for the backend class.

    ```yaml
    CONFIG_NINJA_OBJECTS:
      example-1:
        source:
    ```
    ```yaml
          new:
            kwargs:
              path: config-ninja-settings.yaml
    ```
    """

    kwargs: dict[str, str]
    """Pass these values as arguments to the `config_ninja.backend.Backend.new()` on creation."""


class Source(TypedDict):
    """Describe the source of configuration data written to a `Dest`.

    The parameters `Source.init` and `Source.new` are mutually exclusive.

    ```yaml
    CONFIG_NINJA_OBJECTS:
      example-1:
    ```
    ```yaml
        source:
          backend: local
          format: yaml

          new:
            kwargs:
              path: config-ninja-settings.yaml
    ```
    """

    backend: Literal['local', 'appconfig']
    """The module in `config_ninja.contrib` implementing the `config_ninja.backend.Backend` class."""

    format: FormatT
    """Deserialize the source data from this format.

    Defaults to `'raw'`.
    """

    init: Init
    """Pass these parameters to the `config_ninja.backend.Backend`'s `__init__()` method.

    These are typically unique identifiers; friendly names can be passed to the
    `config_ninja.backend.Backend.new()` method (via `Source.new`) instead.
    """

    new: New
    """Pass these parameters to the backend class's `config_ninja.backend.Backend.new()` method.

    If this property is defined, the `Source.init` property is ignored.
    """


PathStr: TypeAlias = str
"""A string representing a file path."""


class Dest(TypedDict):
    """Destination metadata for the object's output file.

    ```yaml
    CONFIG_NINJA_OBJECTS:
      example-1:
    ```
    ```yaml
        dest:
          # you can specify the path to a Jinja2 template:
          format: templates/settings-subset.toml.j2
          path: /tmp/config-ninja/local/subset.toml
    ```
    """

    path: str
    """Write the configuration file to this path"""

    format: FormatT | PathStr
    """Set the output serialization format of the destination file.

    If given the path to a file, interpret the file as a Jinja2 template and render it with the
    source data.
    """


class ConfigNinjaObject(TypedDict):
    """Specify metadata to manage a system configuration file.

    ```yaml
    CONFIG_NINJA_OBJECTS:
    ```
    ```yaml
        example-1:
          dest:
            format: templates/settings-subset.toml.j2
            path: /tmp/config-ninja/local/subset.toml

          source:
            backend: local
            format: yaml

            new:
              kwargs:
                path: config-ninja-settings.yaml
    ```
    """

    dest: Dest
    """Metadata for the object's output file."""

    source: Source
    """Configuration data for the object's `config_ninja.backend.Backend` data source."""


@dataclasses.dataclass
class DestSpec:
    """Container for the destination spec parsed from `config-ninja`_'s own configuration file.

    .. _config-ninja: https://config-ninja.readthedocs.io/home.html
    """

    format: FormatT | jinja2.Template
    """Specify the format of the configuration file to write."""

    path: Path
    """Write the configuration file to this path."""

    def __str__(self) -> str:
        """Represent the destination spec as a string."""
        if self.is_template:
            assert isinstance(self.format, jinja2.Template)  # noqa: S101  # 👈 for static analysis
            fmt = f'(template: {self.format.name})'
        else:
            fmt = f'(format: {self.format})'

        return f'{fmt} -> {self.path}'

    @classmethod
    def from_primitives(cls, data: Dest) -> DestSpec:
        """Create a `DestSpec` instance from a dictionary of primitive types."""
        path = Path(data['path'])
        if data['format'] in DUMPERS:
            fmt: FormatT = data['format']  # type: ignore[assignment,unused-ignore]
            return DestSpec(format=fmt, path=path)

        template_path = Path(data['format'])

        loader = jinja2.FileSystemLoader(template_path.parent)
        env = jinja2.Environment(autoescape=jinja2.select_autoescape(default=True), loader=loader)

        return DestSpec(path=path, format=env.get_template(template_path.name))

    @property
    def is_template(self) -> bool:
        """Whether the destination uses a Jinja2 template."""
        return isinstance(self.format, jinja2.Template)


@dataclasses.dataclass
class SourceSpec:
    """The data source of a `config-ninja`_ object.

    .. _config-ninja: https://config-ninja.readthedocs.io/home.html
    """

    backend: Backend
    """Read configuration data from this backend (see `config_ninja.contrib` for supported backends)."""

    format: FormatT = 'raw'
    """Decode the source data from this format."""

    @classmethod
    def from_primitives(cls, data: Source) -> SourceSpec:
        """Create a `SourceSpec` instance from a dictionary of primitive types.

        If the given `Source` has a `Source.new` key, the appropriate `config_ninja.backend.Backend.new()` method is
        invoked to create `SourceSpec.backend`. Otherwise, the `Source` must have a `Source.init` key for passing
        arguments to the `config_ninja.backend.Backend`'s `__init__()` method.
        """
        backend_class = get_backend(data['backend'])
        fmt = data.get('format', 'raw')
        if new := data.get('new'):
            backend = backend_class.new(**new['kwargs'])
        else:
            backend = backend_class(**data['init']['kwargs'])

        return SourceSpec(backend=backend, format=fmt)


@dataclasses.dataclass
class ObjectSpec:
    """Container for each object parsed from `config-ninja`_'s own configuration file.

    .. _config-ninja: https://config-ninja.readthedocs.io/home.html
    """

    dest: DestSpec
    """Destination metadata for the object's output file."""

    source: SourceSpec
    """Configuration for the object's `config_ninja.backend.Backend` data source."""

    @classmethod
    def from_primitives(cls, data: ConfigNinjaObject) -> ObjectSpec:
        """Create an `ObjectSpec` instance from a dictionary of primitive types."""
        return ObjectSpec(
            dest=DestSpec.from_primitives(data['dest']), source=SourceSpec.from_primitives(data['source'])
        )


logger.debug('successfully imported %s', __name__)
