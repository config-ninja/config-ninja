"""Define a controller class for operating on a `config_ninja.settings.ObjectSpec`."""

from __future__ import annotations

import logging
import typing

import jinja2

from config_ninja import settings, systemd
from config_ninja.backend import FormatT, dumps, loads
from config_ninja.settings import ObjectSpec

try:
    from typing import TypeAlias  # type: ignore[attr-defined,unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import TypeAlias  # type: ignore[assignment,attr-defined,unused-ignore]

__all__ = ['BackendController', 'ErrorHandler']

logger = logging.getLogger(__name__)

ActionType: TypeAlias = typing.Callable[[str], typing.Any]
ErrorHandler: TypeAlias = typing.Callable[[typing.Dict[typing.Any, typing.Any]], typing.ContextManager[None]]


class BackendController:
    """Define logic for operating a configuration `ObjectSpec`."""

    key: str
    """The key of the configuration object in the settings file."""

    logger: logging.Logger
    """Each `BackendController` has its own logger (named `"config_ninja.controller:{key}"`)."""

    spec: ObjectSpec
    """Full specification for the configuration object."""

    def __init__(self, spec: ObjectSpec, key: str) -> None:
        """Ensure the parent directory of the destination path exists; initialize a logger."""
        self.logger = logging.getLogger(f'{__name__}:{key}')
        self.key = key
        self.spec = spec

        spec.dest.path.parent.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        """Represent the controller as its backend populating its destination."""
        return f'{self.spec.source.backend} ({self.spec.source.format}) -> {self.spec.dest}'

    def _do(self, action: ActionType, data: dict[str, typing.Any]) -> None:
        if self.spec.dest.is_template:
            assert isinstance(self.spec.dest.format, jinja2.Template)  # noqa: S101  # 👈 for static analysis
            action(self.spec.dest.format.render(data))
        else:
            fmt: FormatT = self.spec.dest.format  # type: ignore[assignment]
            action(dumps(fmt, data))

    @classmethod
    def from_settings(
        cls, conf_settings: settings.Config, key: str, handle_key_errors: ErrorHandler
    ) -> BackendController:
        """Create a `BackendController` instance from the given settings."""
        cfg_obj = conf_settings.settings.OBJECTS[key]
        with handle_key_errors(cfg_obj):  # type: ignore[arg-type]
            spec = ObjectSpec.from_primitives(cfg_obj, conf_settings.engine)
        return cls(spec, key)

    def get(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Retrieve and print the value of the configuration object.

        Any `config_ninja.settings.poe.Hook`s will be skipped; they are only executed by the `BackendController.write()`
        and `BackendController.awrite()` methods.
        """
        data = loads(self.spec.source.format, self.spec.source.backend.get())
        self._do(do_print, data)
        for hook in self.spec.hooks:
            self.logger.debug('would execute: %s', hook)

    async def aget(self, do_print: typing.Callable[[str], typing.Any]) -> None:
        """Poll to retrieve the latest configuration object, and print on each update.

        Any `config_ninja.settings.poe.Hook`s will be skipped; they are only executed by the `BackendController.write()`
        and `BackendController.awrite()` methods.
        """
        if systemd.AVAILABLE:  # pragma: no cover
            systemd.notify()

        async for content in self.spec.source.backend.poll():
            data = loads(self.spec.source.format, content)
            self._do(do_print, data)
            for hook in self.spec.hooks:
                self.logger.debug('would execute: %s', hook)

    def write(self) -> None:
        """Retrieve the latest value of the configuration object, and write to file.

        If the `config_ninja.settings.ObjectSpec` provides any `config_ninja.settings.poe.Hook`s, they will be executed
        after writing the configuration object to the destination file.
        """
        data = loads(self.spec.source.format, self.spec.source.backend.get())
        self._do(self.spec.dest.path.write_text, data)
        for hook in self.spec.hooks:
            hook()

    async def awrite(self) -> None:
        """Poll to retrieve the latest configuration object, and write to file on each update.

        If the `config_ninja.settings.ObjectSpec` provides any `config_ninja.settings.poe.Hook`s, they will be executed
        after writing the configuration object to the destination file.
        """
        if systemd.AVAILABLE:  # pragma: no cover
            systemd.notify()

        async for content in self.spec.source.backend.poll():
            data = loads(self.spec.source.format, content)
            self._do(self.spec.dest.path.write_text, data)
            for hook in self.spec.hooks:
                hook()


logger.debug('successfully imported %s', __name__)
