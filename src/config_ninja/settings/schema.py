"""Define the schema of `config-ninja`_'s settings file.

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

import logging
from typing import Literal, TypedDict

from config_ninja.backend import FormatT

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias


__all__ = ['ConfigNinjaObject', 'Dest', 'Init', 'New', 'PathStr', 'Source']

logger = logging.getLogger(__name__)


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


logger.debug('successfully imported %s', __name__)
