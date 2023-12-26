"""Define the API for config backends."""
from __future__ import annotations

# stdlib
import abc
import logging
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)


class AbstractBackend(abc.ABC):
    """Define the API for backend implementations."""

    @abc.abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the backend."""

    @abc.abstractmethod
    def get(self, decoder: Callable[[str], dict[str, Any]] = yaml.safe_load) -> dict[str, Any]:
        """Retrieve and decode the configuration."""

    @abc.abstractmethod
    def get_raw(self) -> str:
        """Retrieve the raw configuration as a string."""

    @classmethod
    def new(cls: type[AbstractBackend], *args: Any, **kwargs: Any) -> AbstractBackend:
        """Connect a new instance to the backend."""
        return cls(*args, **kwargs)


logger.debug('successfully imported %s', __name__)
