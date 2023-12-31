"""Define the API for config backends."""
from __future__ import annotations

# stdlib
import abc
import json
import logging
from typing import Any, AsyncIterator, Callable, Literal

import tomlkit as toml
import yaml

logger = logging.getLogger(__name__)

FormatT = Literal['json', 'raw', 'toml', 'yaml', 'yml']
LoadT = Callable[[str], dict[str, Any]]
DumpT = Callable[[dict[str, Any]], str]


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
    """Serialize the given data using the given format."""
    try:
        dump = DUMPERS[fmt]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"unsupported format: '{fmt}'") from exc

    return dump(data)


def loads(fmt: FormatT, raw: str) -> dict[str, Any]:
    """Deserialize the given data using the given format."""
    try:
        return LOADERS[fmt](raw)
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"unsupported format: '{fmt}'") from exc


class Backend(abc.ABC):
    """Define the API for backend implementations."""

    @abc.abstractmethod
    def get(self) -> str:
        """Retrieve the raw configuration as a string."""

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
