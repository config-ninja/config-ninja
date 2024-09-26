"""Use a local file as the backend.

## Example

The following `config-ninja`_ settings file configures the `LocalBackend` to render two files
(`/tmp/config-ninja/local/settings.json` and `/tmp/config-ninja/local/subset.toml`) from a single
local source file (`config-ninja-settings.yaml`):

```yaml
.. include:: ../../../examples/local-backend.yaml
```

.. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import AsyncIterator

from watchfiles import awatch  # pyright: ignore[reportUnknownVariableType]

from config_ninja.backend import Backend

__all__ = ['LocalBackend']

logger = logging.getLogger(__name__)


class LocalBackend(Backend):
    """Read the configuration from a local file.

    ## Usage

    >>> backend = LocalBackend(example_file)
    >>> print(backend.get())
    key_0: value_0
    key_1: 1
    key_2: true
    key_3:
        - 1
        - 2
        - 3
    """

    path: Path
    """Read the configuration from this file"""

    def __init__(self, path: str | Path) -> None:
        """Set attributes to initialize the backend.

        If the given `path` doesn't exist, emit a warning and continue.

        >>> with pytest.warns(RuntimeWarning):
        ...     backend = LocalBackend('does_not_exist')
        """
        logger.debug("Initialize: %s('%s')", self.__class__.__name__, path)
        self.path = Path(path)
        if not self.path.is_file():
            warnings.warn(f'could not read file: {path}', category=RuntimeWarning, stacklevel=2)

    def __str__(self) -> str:
        """Return the source file's path as the string representation of the backend."""
        return f'{self.path}'

    def get(self) -> str:
        """Read the contents of the configuration file as a string."""
        logger.debug("Read file: '%s'", self.path)
        return self.path.read_text(encoding='utf-8')

    async def poll(self, interval: int = 0) -> AsyncIterator[str]:
        """Poll the file's parent directory for changes, and yield the file contents on change.

        .. note::
            The `interval` parameter is ignored
        """
        yield self.get()
        async for _ in awatch(self.path):
            logger.info("Detected change to '%s'", self.path)
            yield self.get()


logger.debug('successfully imported %s', __name__)
