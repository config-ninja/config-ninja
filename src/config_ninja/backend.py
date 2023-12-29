"""Define the API for config backends."""
from __future__ import annotations

# stdlib
import abc
import logging
from typing import TYPE_CHECKING, Any, Callable, Iterator

import yaml

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    DecodeT = Callable[[str], dict[str, Any]]


class AbstractBackend(abc.ABC):
    """Define the API for backend implementations."""

    @abc.abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the backend."""

    def get(self, decoder: DecodeT = yaml.safe_load) -> dict[str, Any]:
        """Retrieve and decode the configuration."""
        return decoder(self.get_raw())

    @abc.abstractmethod
    def get_raw(self) -> str:
        """Retrieve the raw configuration as a string."""

    @classmethod
    def new(cls: type[AbstractBackend], *args: Any, **kwargs: Any) -> AbstractBackend:
        """Connect a new instance to the backend."""
        return cls(*args, **kwargs)

    @abc.abstractmethod
    def poll(self, interval: int = 0) -> Iterator[str]:
        """Poll the configuration for changes."""


logger.debug('successfully imported %s', __name__)
