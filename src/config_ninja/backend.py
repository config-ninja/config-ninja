"""Define the API for config backends."""

from __future__ import annotations

import abc
import json
import logging
import typing
from typing import Any, AsyncIterator, Callable, Dict

import tomlkit as toml
import yaml

__all__ = ['Backend', 'FormatT', 'dumps', 'loads']

logger = logging.getLogger(__name__)

FormatT = typing.Literal['json', 'raw', 'toml', 'yaml', 'yml']
"""The supported serialization formats (not including `jinja2` templates)"""

# note: `3.8` was not respecting `from __future__ import annotations` for delayed evaluation
LoadT = Callable[[str], Dict[str, Any]]
DumpT = Callable[[Dict[str, Any]], str]


def load_raw(raw: str) -> dict[str, str]:
    """Treat the string as raw text."""
    return {'content': raw}


def dump_raw(data: dict[str, str]) -> str:
    """Get the `'content'` key from the given `dict`."""
    return data['content']


LOADERS: dict[FormatT, LoadT] = {
    'json': json.loads,
    'raw': load_raw,
    'toml': toml.loads,
    'yaml': yaml.safe_load,
    'yml': yaml.safe_load,
}

DUMPERS: dict[FormatT, DumpT] = {
    'json': json.dumps,
    'raw': dump_raw,
    'toml': toml.dumps,  # pyright: ignore[reportUnknownMemberType]
    'yaml': yaml.dump,
    'yml': yaml.dump,
}


def dumps(fmt: FormatT, data: dict[str, Any]) -> str:
    """Serialize the given `data` object to the given `FormatT`."""
    try:
        dump = DUMPERS[fmt]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"unsupported format: '{fmt}'") from exc

    return dump(data)


def loads(fmt: FormatT, raw: str) -> dict[str, Any]:
    """Deserialize the given `raw` string for the given `FormatT`."""
    try:
        return LOADERS[fmt](raw)
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"unsupported format: '{fmt}'") from exc


class Backend(abc.ABC):
    """Define the API for backend implementations."""

    def __repr__(self) -> str:
        """Represent the backend object as its invocation.

        >>> example = ExampleBackend('an example')
        >>> example
        ExampleBackend(source='an example')
        """
        annotations = (klass := self.__class__).__annotations__
        annotations.pop('return', None)

        args = ', '.join(f'{key}={getattr(self, key)!r}' for key in annotations if hasattr(self, key))
        return f'{klass.__name__}({args})'

    @abc.abstractmethod
    def __str__(self) -> str:
        """When formatted as a string, represent the backend as the identifier of its source."""

    @abc.abstractmethod
    def get(self) -> str:
        """Retrieve the configuration as a raw string."""

    @classmethod
    def new(
        cls: type[Backend],
        *args: Any,
        **kwargs: Any,
    ) -> Backend:
        """Connect a new instance to the backend."""
        return cls(*args, **kwargs)

    @abc.abstractmethod
    async def poll(self, interval: int = 0) -> AsyncIterator[str]:
        """Poll the configuration for changes."""
        yield ''  # pragma: no cover


logger.debug('successfully imported %s', __name__)
