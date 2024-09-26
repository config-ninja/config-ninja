"""Configure `doctest` tests."""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

import pytest
from mypy_boto3_appconfigdata import AppConfigDataClient

from config_ninja.backend import Backend

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


class ExampleBackend(Backend):
    """A sample backend class used in `doctest` tests."""

    source: str

    def __init__(self, source: str) -> None:
        """Initialize the backend with the given `source`."""
        self.source = source

    def __str__(self) -> str:
        """Format a mock source identifier to satisfy `abc.abstractmethod()`."""
        return f'sid: {self.source}'

    def get(self) -> str:
        """Dummy method to retrieve an example configuration."""
        return 'example configuration'

    async def poll(self, interval: int = 0) -> AsyncIterator[str]:
        """Dummy method to poll the configuration."""
        yield 'example configuration'


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
    doctest_namespace['ExampleBackend'] = ExampleBackend
    return doctest_namespace
