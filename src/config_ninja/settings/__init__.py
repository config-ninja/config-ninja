"""Read and deserialize configuration for the `config-ninja`_ agent.

## Schema

See `config_ninja.settings.schema` for the schema of the `config-ninja`_ settings file.

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

import jinja2
import pyspry

from config_ninja.backend import DUMPERS, Backend, FormatT
from config_ninja.contrib import get_backend
from config_ninja.settings.schema import ConfigNinjaObject, Dest, DictConfigDefault, Source

__all__ = [
    'DEFAULT_LOGGING_CONFIG',
    'DEFAULT_PATHS',
    'DestSpec',
    'ObjectSpec',
    'PREFIX',
    'SourceSpec',
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


DEFAULT_LOGGING_CONFIG: DictConfigDefault = {
    'version': 1,
    'formatters': {
        'simple': {
            'datefmt': logging.Formatter.default_time_format,
            'format': '%(message)s',
            'style': '%',
            'validate': False,
        },
    },
    'filters': {},
    'handlers': {
        'rich': {
            'class': 'rich.logging.RichHandler',
            'formatter': 'simple',
            'rich_tracebacks': True,
        },
    },
    'loggers': {},
    'root': {
        'handlers': ['rich'],
        'level': logging.INFO,
        'propagate': False,
    },
    'disable_existing_loggers': True,
    'incremental': False,
}
"""Default logging configuration passed to `logging.config.dictConfig()`."""

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