"""Define fixtures for the test suite."""
from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any, Iterator, TypeVar
from unittest import mock

import pytest
from boto3 import Session
from botocore.exceptions import ClientError
from botocore.paginate import PageIterator, Paginator
from botocore.response import StreamingBody
from mypy_boto3_appconfig import AppConfigClient
from mypy_boto3_appconfigdata import AppConfigDataClient
from mypy_boto3_appconfigdata.type_defs import GetLatestConfigurationResponseTypeDef
from pytest_mock import MockerFixture

T = TypeVar('T')
MOCK_YAML_CONFIG = b"""
key_0: value_0
key_1: 1
key_2: true
key_3:
    - 1
    - 2
    - 3
""".strip()


@pytest.fixture()
def mock_appconfig_client() -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service."""
    return mock.MagicMock(name='mock_appconfig_client', spec_set=AppConfigClient)


@pytest.fixture()
def mock_session(mocker: MockerFixture) -> Session:
    """Mock the `boto3.Session` class."""
    mock_session = mock.MagicMock(name='mock_session', spec_set=Session)
    mocker.patch('boto3.Session', return_value=mock_session)
    return mock_session


@pytest.fixture()
def mock_session_with_0_ids(
    mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock
) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return no IDs."""
    mock_page_iterator = mock.MagicMock(spec_set=PageIterator)
    mock_page_iterator.search.return_value = []

    mock_paginator = mock.MagicMock(spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator
    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture()
def mock_session_with_1_id(
    mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock
) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return a single ID."""
    mock_page_iterator = mock.MagicMock(name='mock_page_iterator', spec_set=PageIterator)
    mock_page_iterator.search.return_value = ['id-1']

    mock_paginator = mock.MagicMock(name='mock_page_iterator', spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator

    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture()
def mock_session_with_2_ids(
    mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock
) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return two IDs."""
    mock_page_iterator = mock.MagicMock(spec_set=PageIterator)
    mock_page_iterator.search.return_value = ['id-1', 'id-2']

    mock_paginator = mock.MagicMock(spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator

    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture()
def mock_latest_config() -> GetLatestConfigurationResponseTypeDef:
    """Mock the response from `get_latest_configuration`."""
    mock_config_stream = mock.MagicMock(spec_set=StreamingBody)
    mock_config_stream.read.return_value = MOCK_YAML_CONFIG
    return {
        'NextPollConfigurationToken': 'token',
        'NextPollIntervalInSeconds': 1,
        'ContentType': 'application/json',
        'Configuration': mock_config_stream,
        'VersionLabel': 'v1',
        'ResponseMetadata': {
            'RequestId': '',
            'HostId': '',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {},
            'RetryAttempts': 3,
        },
    }


@pytest.fixture()
def mock_appconfigdata_client(mock_latest_config: mock.MagicMock) -> AppConfigDataClient:
    """Mock the low-level `boto3` client for the `AppConfigData` service."""
    mock_client = mock.MagicMock(name='mock_appconfigdata_client', spec_set=AppConfigDataClient)
    mock_client.get_latest_configuration.return_value = mock_latest_config
    return mock_client


@pytest.fixture()
def mock_full_session(
    mock_session_with_1_id: mock.MagicMock,
    mock_appconfig_client: mock.MagicMock,
    mock_appconfigdata_client: mock.MagicMock,
) -> Session:
    """Mock the `boto3.Session` class with a full AppConfig client."""

    def client(service: str) -> mock.MagicMock:
        if service == 'appconfig':
            return mock_appconfig_client
        if service == 'appconfigdata':
            return mock_appconfigdata_client
        raise ValueError(f'Unknown service: {service}')

    mock_session_with_1_id.client = client
    return mock_session_with_1_id


@pytest.fixture()
def mock_poll_too_early(
    mock_latest_config: GetLatestConfigurationResponseTypeDef,
) -> AppConfigDataClient:
    """Raise a `BadRequestException` when polling for configuration changes."""
    mock_client = mock.MagicMock(spec_set=AppConfigDataClient)
    mock_client.exceptions.BadRequestException = ClientError
    call_count = 0

    def side_effect(*args: Any, **kwargs: Any) -> GetLatestConfigurationResponseTypeDef:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise mock_client.exceptions.BadRequestException(
                {
                    'Error': {
                        'Code': 'BadRequestException',
                        'Message': 'Request too early',
                    },
                    'ResponseMetadata': {},
                },
                'GetLatestConfiguration',
            )
        return mock_latest_config

    mock_client.get_latest_configuration.side_effect = side_effect

    return mock_client


@pytest.fixture()
def example_file(tmp_path: Path) -> Path:
    """Write the test configuration to a file in the temporary directory."""
    path = tmp_path / 'example.yaml'
    path.write_bytes(MOCK_YAML_CONFIG)
    return path


example_file.__doc__ = f"""Write the test configuration to a file in the temporary directory.

```yaml
{MOCK_YAML_CONFIG.decode('utf-8')}
```
"""

_no_default = object()


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
) -> dict[str, Any]:
    """Add the `mock_client` fixture to the doctest namespace."""
    if 'anext' not in builtins.__dict__:  # pragma: no cover
        doctest_namespace['anext'] = py_anext

    doctest_namespace['example_file'] = example_file
    doctest_namespace['pytest'] = pytest
    doctest_namespace['appconfigdata_client'] = mock_appconfigdata_client
    return doctest_namespace
