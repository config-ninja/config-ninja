"""Define a controller class for operating on a backend class, formatter, and output destination."""

from __future__ import annotations

import logging
import typing

import jinja2
import pyspry

from config_ninja import systemd
from config_ninja.backend import Backend, FormatT, dumps, loads
from config_ninja.settings import DestSpec, ObjectSpec

try:
    from typing import TypeAlias  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    from typing_extensions import TypeAlias  # type: ignore[assignment,attr-defined,unused-ignore]

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

    key: str
    """The key of the configuration object in the settings file."""

    src_format: FormatT
    """The format of the configuration object in the backend.

    The named `config_ninja.backend.LOADERS` function will be used to deserialize the configuration
    object from the backend.
    """

    def __init__(self, spec: ObjectSpec, key: str) -> None:
        """Ensure the parent directory of the destination path exists."""
        self.backend = spec.source.backend
        self.dest = spec.dest
        self.key = key
        self.src_format = spec.source.format
        spec.dest.path.parent.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        """Represent the controller as its backend populating its destination."""
        return f'{self.backend} ({self.src_format}) -> {self.dest}'

    def _do(self, action: ActionType, data: dict[str, typing.Any]) -> None:
        if self.dest.is_template:
            assert isinstance(self.dest.format, jinja2.Template)  # noqa: S101  # 👈 for static analysis
            action(self.dest.format.render(data))
        else:
            fmt: FormatT = self.dest.format  # type: ignore[assignment]
            action(dumps(fmt, data))

    @classmethod
    def from_settings(cls, settings: pyspry.Settings, key: str, handle_key_errors: ErrorHandler) -> BackendController:
        """Create a `BackendController` instance from the given settings."""
        cfg_obj = settings.OBJECTS[key]
        with handle_key_errors(cfg_obj):  # type: ignore[arg-type]
            spec = ObjectSpec.from_primitives(cfg_obj)
        return cls(spec, key)

    def get(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Retrieve and print the value of the configuration object."""
        data = loads(self.src_format, self.backend.get())
        self._do(do_print, data)

    async def aget(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Poll to retrieve the latest configuration object, and print on each update."""
        if systemd.AVAILABLE:  # pragma: no cover
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
        if systemd.AVAILABLE:  # pragma: no cover
            systemd.notify()

        async for content in self.backend.poll():
            data = loads(self.src_format, content)
            self._do(self.dest.path.write_text, data)


logger.debug('successfully imported %s', __name__)
