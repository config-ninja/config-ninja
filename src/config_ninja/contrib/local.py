"""Use a local file as the backend."""
from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Iterator

from watchfiles import watch

from config_ninja.backend import AbstractBackend

logger = logging.getLogger(__name__)


class LocalBackend(AbstractBackend):
    """Read the configuration from a local file.

    ## Usage

    >>> backend = LocalBackend(example_file)
    >>> print(backend.get_raw())
    key_0: value_0
    key_1: 1
    key_2: true
    key_3:
        - 1
        - 2
        - 3

    If the file doesn't exist, emit a warning and continue.

    >>> with pytest.warns(RuntimeWarning):
    ...     backend = LocalBackend('does_not_exist')
    """

    path: Path

    def __init__(self, path: str) -> None:
        """Set attributes to initialize the backend."""
        self.path = Path(path)
        if not self.path.is_file():
            warnings.warn(f'could not read file: {path}', category=RuntimeWarning, stacklevel=2)

    def get_raw(self) -> str:
        """Read the contents of the configuration file as a string."""
        return self.path.read_text()

    def poll(self, interval: int = 10) -> Iterator[str]:
        """Poll the file's parent directory for changes, and yield the file contents on change."""
        for _ in watch(self.path):
            logger.info("detected change to '%s'", self.path)
            yield self.get_raw()


logger.debug('successfully imported %s', __name__)
