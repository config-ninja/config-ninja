"""Allow invoking the CLI with `python -m config_ninja`."""

from __future__ import annotations

import logging

from config_ninja import main

__all__ = ['main']

logger = logging.getLogger(__name__)

if __name__ == '__main__':  # pragma: no cover
    main()
else:
    logger.debug('successfully imported %s', __name__)
