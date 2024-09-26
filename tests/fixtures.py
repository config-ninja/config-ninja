"""Define fixtures for the test suite."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any, Iterator, TypeVar
from unittest import mock

import pytest
import pytest_mock
from boto3 import Session
from botocore.exceptions import ClientError
from botocore.paginate import PageIterator, Paginator
from botocore.response import StreamingBody
from mypy_boto3_appconfig import AppConfigClient
from mypy_boto3_appconfigdata import AppConfigDataClient
from mypy_boto3_appconfigdata.type_defs import GetLatestConfigurationResponseTypeDef
from pytest_mock import MockerFixture

from config_ninja import cli, systemd

# pylint: disable=redefined-outer-name

T = TypeVar('T')

MOCK_PYPI_RESPONSE = {'releases': {'1.0': 'ignore', '1.1': 'ignore', '1.2a0': 'ignore'}}
MOCK_YAML_CONFIG = b"""
key_0: value_0
key_1: 1
key_2: true
key_3:
    - 1
    - 2
    - 3
""".strip()


class MockFile(mock.MagicMock):
    """Mock the file object returned by `contextlib.closing`."""

    mock_bytes: bytes

    def read(self) -> bytes:
        """Mock the `read` method to return data used in tests."""
        return self.mock_bytes


def mock_file(mock_bytes: bytes) -> MockFile:
    """Mock the file object returned by `contextlib.closing`."""
    mock_file = MockFile()
    mock_file.mock_bytes = mock_bytes
    return mock_file


@pytest.fixture
def _mock_contextlib_closing(mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Mock `contextlib.closing`."""

    @contextlib.contextmanager
    def _mocked(request: Any) -> Iterator[Any]:
        """Pass the input parameter straight through."""
        yield request

    mocker.patch('contextlib.closing', new=_mocked)


@pytest.fixture
def _mock_urlopen_for_pypi(mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Mock `urllib.request.urlopen` for PyPI requests."""

    def _mocked(_: Any) -> MockFile:
        return mock_file(json.dumps(MOCK_PYPI_RESPONSE).encode('utf-8'))

    mocker.patch('urllib.request.urlopen', new=_mocked)


@pytest.fixture
def mock_appconfig_client() -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service."""
    return mock.MagicMock(name='mock_appconfig_client', spec_set=AppConfigClient)


@pytest.fixture
def _mock_install_io(mocker: MockerFixture) -> None:  # pyright: ignore[reportUnusedFunction]
    """Mock various I/O utilities used by the `install` script."""
    mocker.patch('shutil.rmtree')
    mocker.patch('subprocess.run')
    mocker.patch('venv.EnvBuilder')
    mocker.patch('runpy.run_path')


@pytest.fixture
def mock_session(mocker: MockerFixture) -> Session:
    """Mock the `boto3.Session` class."""
    mock_session = mock.MagicMock(name='mock_session', spec_set=Session)
    mocker.patch('boto3.Session', return_value=mock_session)
    return mock_session


@pytest.fixture
def mock_session_with_0_ids(mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return no IDs."""
    mock_page_iterator = mock.MagicMock(spec_set=PageIterator)
    mock_page_iterator.search.return_value = []

    mock_paginator = mock.MagicMock(spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator
    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture
def mock_session_with_1_id(mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return a single ID."""
    mock_page_iterator = mock.MagicMock(name='mock_page_iterator', spec_set=PageIterator)
    mock_page_iterator.search.return_value = ['id-1']

    mock_paginator = mock.MagicMock(name='mock_page_iterator', spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator

    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture
def mock_session_with_2_ids(mock_appconfig_client: mock.MagicMock, mock_session: mock.MagicMock) -> AppConfigClient:
    """Mock the `boto3` client for the `AppConfig` service to return two IDs."""
    mock_page_iterator = mock.MagicMock(spec_set=PageIterator)
    mock_page_iterator.search.return_value = ['id-1', 'id-2']

    mock_paginator = mock.MagicMock(spec_set=Paginator)
    mock_paginator.paginate.return_value = mock_page_iterator

    mock_appconfig_client.get_paginator.return_value = mock_paginator

    mock_session.client.return_value = mock_appconfig_client
    return mock_session


@pytest.fixture
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


@pytest.fixture
def mock_latest_config_first_empty() -> GetLatestConfigurationResponseTypeDef:
    """Mock the response from `get_latest_configuration`.

    Return an empty `bytes` on the first iteration, and `MOCK_YAML_CONFIG` on the second. This supports testing
        `config_ninja.contrib.appconfig.AppConfig`'s response to an empty return value.
    """
    was_called: list[bool] = []

    def mock_read(*_: Any, **__: Any) -> bytes:
        if was_called:
            return MOCK_YAML_CONFIG
        was_called.append(True)
        return b''

    mock_config_stream = mock.MagicMock(spec_set=StreamingBody)
    mock_config_stream.read = mock_read
    return {
        'NextPollConfigurationToken': 'token',
        'NextPollIntervalInSeconds': 0,
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


@pytest.fixture
def mock_appconfigdata_client(mock_latest_config: mock.MagicMock) -> AppConfigDataClient:
    """Mock the low-level `boto3` client for the `AppConfigData` service."""
    mock_client = mock.MagicMock(name='mock_appconfigdata_client', spec_set=AppConfigDataClient)
    mock_client.get_latest_configuration.return_value = mock_latest_config
    return mock_client


@pytest.fixture
def mock_appconfigdata_client_first_empty(mock_latest_config_first_empty: mock.MagicMock) -> AppConfigDataClient:
    """Mock the low-level `boto3` client for the `AppConfigData` service."""
    mock_client = mock.MagicMock(name='mock_appconfigdata_client', spec_set=AppConfigDataClient)
    mock_client.get_latest_configuration.return_value = mock_latest_config_first_empty
    return mock_client


@pytest.fixture
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


@pytest.fixture
def mock_poll_too_early(
    mock_latest_config: GetLatestConfigurationResponseTypeDef,
) -> AppConfigDataClient:
    """Raise a `BadRequestException` when polling for configuration changes."""
    mock_client = mock.MagicMock(spec_set=AppConfigDataClient)
    mock_client.exceptions.BadRequestException = ClientError
    call_count = 0

    def side_effect(*_: Any, **__: Any) -> GetLatestConfigurationResponseTypeDef:
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


@pytest.fixture
def monkeypatch_systemd(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    """Monkeypatch various utilities for interfacing with `systemd` and the shell.

    Returns:
        tuple[pathlib.Path, pathlib.Path]: the patched `SYSTEM_INSTALL_PATH` and `USER_INSTALL_PATH`
    """
    mocker.patch('config_ninja.systemd.sh')
    mocker.patch.context_manager(systemd, 'sudo')
    mocker.patch('config_ninja.systemd.sdnotify')

    system_install_path = tmp_path / 'system'
    user_install_path = tmp_path / 'user'

    monkeypatch.setattr(cli, 'SYSTEMD_AVAILABLE', True)
    monkeypatch.setattr(systemd, 'SYSTEM_INSTALL_PATH', system_install_path)
    monkeypatch.setattr(systemd, 'USER_INSTALL_PATH', user_install_path)

    return (system_install_path, user_install_path)


@pytest.fixture
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


@pytest.fixture(autouse=True)
def mock_logging_basic_config(mocker: pytest_mock.MockerFixture) -> mock.MagicMock:
    """Mock the `logging.basicConfig` function."""
    return mocker.patch('logging.basicConfig')
