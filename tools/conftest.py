"""Configure `doctest` tests for the `install` script."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

try:
    from typing import (  # type: ignore[attr-defined,unused-ignore]  # pylint: disable=ungrouped-imports
        TypeAlias,  # pyright: ignore[reportGeneralTypeIssues,reportUnknownVariableType]
    )
except ImportError:  # pragma: no cover
    from typing_extensions import TypeAlias

PathT: TypeAlias = Callable[..., Path]


# pylint: disable=redefined-outer-name


@pytest.fixture()
def mock_path(tmp_path: Path) -> PathT:
    """Mock `pathlib.Path` to return a temporary directory."""
    count = 0

    def _mock_path(*args: str | Path) -> Path:
        """Mock `pathlib.Path` to return a temporary directory instead of '.cn'."""
        if len(args) == 1 and args[0] == '.cn':
            nonlocal count, tmp_path
            args = (tmp_path / str(count) / '.cn',)
            count += 1
        return Path(*args)

    return _mock_path


@pytest.fixture(autouse=True)
def install_doctest_namespace(
    _mock_install_io: None,  # pylint: disable=unused-argument
    _mock_contextlib_closing: None,  # pylint: disable=unused-argument
    _mock_urlopen_for_pypi: MagicMock,  # pylint: disable=unused-argument
    mock_path: PathT,
    doctest_namespace: dict[str, Any],
) -> dict[str, Any]:
    """Configure globals for `doctest` tests in the `install` script."""
    doctest_namespace['Path'] = mock_path
    doctest_namespace['pytest'] = pytest
    return doctest_namespace
