"""Configure `doctest` tests."""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any, Iterator

import pytest
from mypy_boto3_appconfigdata import AppConfigDataClient

_no_default = object()

# pylint: disable=too-complex


# note: the following is needed for testing on Python < 3.10
# ref: https://docs.python.org/3/library/functions.html#anext
def py_anext(iterator: Iterator[Any], default: Any = _no_default) -> Any:  # pragma: no cover
    """Pure-Python implementation of anext() for testing purposes.

    Closely matches the builtin anext() C implementation.
    Can be used to compare the built-in implementation of the inner
    coroutines machinery to C-implementation of __anext__() and send()
    or throw() on the returned generator.

    ref: https://github.com/python/cpython/blob/ea786a882b9ed4261eafabad6011bc7ef3b5bf94/Lib/test/test_asyncgen.py#L52-L80
    """
    try:
        __anext__ = type(iterator).__anext__  # type: ignore[attr-defined]
    except AttributeError as exc:
        raise TypeError(f'{iterator!r} is not an async iterator') from exc

    if default is _no_default:
        return __anext__(iterator)  # pyright: ignore[reportUnknownVariableType]

    async def anext_impl() -> Any:
        try:
            # The C code is way more low-level than this, as it implements
            # all methods of the iterator protocol. In this implementation
            # we're relying on higher-level coroutine concepts, but that's
            # exactly what we want -- crosstest pure-Python high-level
            # implementation and low-level C anext() iterators.
            return await __anext__(iterator)  # pyright: ignore[reportUnknownVariableType]
        except StopAsyncIteration:
            return default

    return anext_impl()


@pytest.fixture(autouse=True)
def src_doctest_namespace(
    doctest_namespace: dict[str, Any],
    mock_appconfigdata_client: AppConfigDataClient,
    example_file: Path,
    monkeypatch_systemd: tuple[Path, Path],
) -> dict[str, Any]:
    """Add various mocks and patches to the doctest namespace."""
    if 'anext' not in builtins.__dict__:  # pragma: no cover
        doctest_namespace['anext'] = py_anext

    doctest_namespace['SYSTEM_INSTALL_PATH'] = monkeypatch_systemd[0]
    doctest_namespace['USER_INSTALL_PATH'] = monkeypatch_systemd[1]

    doctest_namespace['example_file'] = example_file
    doctest_namespace['pytest'] = pytest
    doctest_namespace['appconfigdata_client'] = mock_appconfigdata_client
    return doctest_namespace
