"""Read and deserialize configuration for the `config-ninja`_ agent.

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

import jinja2
import pyspry
from pyspry import Settings

from config_ninja.backend import DUMPERS, FormatT

__all__ = ['DEFAULT_PATHS', 'DestSpec', 'PREFIX', 'load', 'resolve_path']

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


def load(path: Path) -> Settings:
    """Load the settings from the given path."""
    return Settings.load(path, PREFIX)


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

    path: Path
    """Write the configuration file to this path."""

    format: FormatT | jinja2.Template
    """Specify the format of the configuration file to write.

    This property is either a `config_ninja.backend.FormatT` or a `jinja2.environment.Template`:
    - if `config_ninja.backend.FormatT`, the identified `config_ninja.backend.DUMPERS` will be used
        to serialize the configuration object
    - if `jinja2.environment.Template`, this template will be used to render the configuration file
    """

    def __str__(self) -> str:
        """Represent the destination spec as a string."""
        if self.is_template:
            assert isinstance(self.format, jinja2.Template)  # noqa: S101  # 👈 for static analysis
            fmt = f'(template: {self.format.name})'
        else:
            fmt = f'(format: {self.format})'

        return f'{fmt} -> {self.path}'

    @classmethod
    def from_primitives(cls, data: pyspry.DestType) -> DestSpec:
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


logger.debug('successfully imported %s', __name__)
