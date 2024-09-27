"""Define a controller class for operating on a backend class, formatter, and output destination."""

from __future__ import annotations

import logging
import typing

import jinja2
import pyspry

from config_ninja import systemd
from config_ninja.backend import Backend, FormatT, dumps, loads
from config_ninja.contrib import get_backend
from config_ninja.settings import DestSpec

if typing.TYPE_CHECKING:  # pragma: no cover
    import sh

    try:
        from typing import TypeAlias  # type: ignore[attr-defined,unused-ignore]
    except ImportError:
        from typing_extensions import TypeAlias  # type: ignore[assignment,attr-defined,unused-ignore]

    SYSTEMD_AVAILABLE = True
else:
    try:
        import sh
    except ImportError:  # pragma: no cover
        sh = None
        SYSTEMD_AVAILABLE = False
    else:
        SYSTEMD_AVAILABLE = hasattr(sh, 'systemctl')

__all__ = ['BackendController', 'DestSpec', 'ErrorHandler']

logger = logging.getLogger(__name__)

ActionType: TypeAlias = typing.Callable[[str], typing.Any]
ErrorHandler: TypeAlias = typing.Callable[[typing.Dict[typing.Any, typing.Any]], typing.ContextManager[None]]


class BackendController:
    """Define logic for initializing a backend from settings and interacting with it."""

    backend: Backend
    """The backend instance to use for retrieving configuration data."""

    dest: DestSpec
    """Parameters for writing the configuration file."""

    handle_key_errors: ErrorHandler
    """Context manager for handling key errors."""

    key: str
    """The key of the backend in the settings file"""

    settings: pyspry.Settings
    """`config-ninja`_'s own configuration settings

    .. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
    """

    src_format: FormatT
    """The format of the configuration object in the backend.

    The named `config_ninja.backend.LOADERS` function will be used to deserialize the configuration
    object from the backend.
    """

    def __init__(self, settings: pyspry.Settings, key: str, handle_key_errors: ErrorHandler) -> None:
        """Parse the settings to initialize the backend."""
        self.settings, self.key = settings, key

        self.handle_key_errors = handle_key_errors
        self.src_format, self.backend = self._init_backend()
        self.dest = self._get_dest()

    def __str__(self) -> str:
        """Represent the controller as its backend populating its destination."""
        return f'{self.backend} ({self.src_format}) -> {self.dest}'

    def _get_dest(self) -> DestSpec:
        """Read the destination spec from the settings file."""
        objects = self.settings.OBJECTS
        with self.handle_key_errors(objects):
            return DestSpec.from_primitives(objects[self.key]['dest'])

    def _init_backend(self) -> tuple[FormatT, Backend]:
        """Get the backend for the specified configuration object."""
        objects = self.settings.OBJECTS

        with self.handle_key_errors(objects):
            source = objects[self.key]['source']
            backend_class: type[Backend] = get_backend(source['backend'])
            fmt = source.get('format', 'raw')
            if source.get('new'):
                backend = backend_class.new(**source['new']['kwargs'])
            else:
                backend = backend_class(**source['init']['kwargs'])

        return fmt, backend

    def _do(self, action: ActionType, data: dict[str, typing.Any]) -> None:
        if self.dest.is_template:
            assert isinstance(self.dest.format, jinja2.Template)  # noqa: S101  # 👈 for static analysis
            action(self.dest.format.render(data))
        else:
            fmt: FormatT = self.dest.format  # type: ignore[assignment]
            action(dumps(fmt, data))

    def get(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Retrieve and print the value of the configuration object."""
        data = loads(self.src_format, self.backend.get())
        self._do(do_print, data)

    async def aget(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Poll to retrieve the latest configuration object, and print on each update."""
        if SYSTEMD_AVAILABLE:  # pragma: no cover
            systemd.notify()

        async for content in self.backend.poll():
            data = loads(self.src_format, content)
            self._do(do_print, data)

    def write(self) -> None:
        """Retrieve the latest value of the configuration object, and write to file."""
        data = loads(self.src_format, self.backend.get())
        self._do(self.dest.path.write_text, data)

    async def awrite(self) -> None:
        """Poll to retrieve the latest configuration object, and write to file on each update."""
        if SYSTEMD_AVAILABLE:  # pragma: no cover
            systemd.notify()

        async for content in self.backend.poll():
            data = loads(self.src_format, content)
            self._do(self.dest.path.write_text, data)


logger.debug('successfully imported %s', __name__)
