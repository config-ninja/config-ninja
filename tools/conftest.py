"""Configure `doctest` tests for the `install` script."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# pylint: disable=redefined-outer-name


@pytest.fixture()
def mock_path(tmp_path: Path) -> type[Path]:
    """Mock `pathlib.Path` to return a temporary directory."""
    count = 0

    class MockPath(Path):
        """Mock `pathlib.Path` to return a temporary directory instead of '.cn'."""

        def __init__(self, *args: str | Path) -> None:
            if len(args) == 1 and args[0] == '.cn':
                nonlocal count, tmp_path
                args = (tmp_path / str(count) / '.cn',)
                count += 1
            super().__init__(*args)

    return MockPath


@pytest.fixture(autouse=True)
def install_doctest_namespace(
    _mock_install_io: None,  # pylint: disable=unused-argument
    _mock_contextlib_closing: None,  # pylint: disable=unused-argument
    _mock_urlopen_for_pypi: MagicMock,  # pylint: disable=unused-argument
    mock_path: Path,
    doctest_namespace: dict[str, Any],
) -> dict[str, Any]:
    """Configure globals for `doctest` tests in the `install` script."""
    doctest_namespace['Path'] = mock_path
    doctest_namespace['pytest'] = pytest
    return doctest_namespace
