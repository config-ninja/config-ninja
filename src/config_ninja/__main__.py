"""Allow invoking the CLI with `python -m config_ninja`."""
from __future__ import annotations

import logging

from config_ninja.cli import app

logger = logging.getLogger(__name__)


def main() -> None:  # pylint: disable=missing-function-docstring  # noqa: D103
    logging.basicConfig(level=logging.INFO)
    app(prog_name='config-ninja')


if __name__ == '__main__':  # pragma: no cover
    main()
else:
    logger.debug('successfully imported %s', __name__)
