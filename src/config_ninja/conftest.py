"""Configure `doctest` tests."""

from __future__ import annotations

import builtins
import logging
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest
import pytest_mock
from mypy_boto3_appconfigdata import AppConfigDataClient

from config_ninja.backend import Backend

_no_default = object()

# pylint: disable=redefined-outer-name,too-many-arguments


# note: the following is needed for testing on Python < 3.10
# ref: https://docs.python.org/3/library/functions.html#anext
def py_anext(iterator: Iterator[Any], default: Any = _no_default) -> Any:  # pylint: disable=too-complex   # pragma: no cover
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


class ExampleBackend:
    """A sample backend class used in `doctest` tests."""

    source: str

    __repr__ = Backend.__repr__

    def __init__(self, source: str) -> None:
        """Initialize the backend with the given `source`."""
        self.source = source


@pytest.fixture
def mock_context(mocker: pytest_mock.MockerFixture) -> MagicMock:
    """Mock the `context` object that is passed between commands / groups."""
    ctx = mocker.MagicMock(spec=mocker.MagicMock)
    ctx.resilient_parsing = False
    return ctx  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def src_doctest_namespace(  # noqa: PLR0913
    doctest_namespace: dict[str, Any],
    mock_appconfigdata_client: AppConfigDataClient,
    mock_appconfigdata_client_first_empty: AppConfigDataClient,
    example_file: Path,
    monkeypatch_systemd: tuple[Path, Path],
    mock_context: MagicMock,
    caplog: pytest.LogCaptureFixture,
    mocker: pytest_mock.MockerFixture,
) -> dict[str, Any]:
    """Add various mocks and patches to the doctest namespace."""
    if 'anext' not in builtins.__dict__:  # pragma: no cover
        doctest_namespace['anext'] = py_anext

    mocker.patch('logging.basicConfig')
    caplog.set_level(logging.NOTSET)

    doctest_namespace['SYSTEM_INSTALL_PATH'] = monkeypatch_systemd[0]
    doctest_namespace['USER_INSTALL_PATH'] = monkeypatch_systemd[1]

    doctest_namespace['example_file'] = example_file
    doctest_namespace['pytest'] = pytest
    doctest_namespace['appconfigdata_client'] = mock_appconfigdata_client
    doctest_namespace['appconfigdata_client_first_empty'] = mock_appconfigdata_client_first_empty
    doctest_namespace['ExampleBackend'] = ExampleBackend
    doctest_namespace['ctx'] = mock_context
    doctest_namespace['caplog'] = caplog
    return doctest_namespace
