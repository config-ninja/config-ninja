"""Define fixtures for the test suite."""
from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar
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

from config_ninja import cli, systemd

# pylint: disable=redefined-outer-name

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


@pytest.fixture()
def monkeypatch_systemd(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, Path]:
    """Monkeypatch various utilities for interfacing with `systemd` and the shell.

    Returns:
        tuple[pathlib.Path, pathlib.Path]: the patched `SYSTEM_INSTALL_PATH` and `USER_INSTALL_PATH`
    """
    monkeypatch.setattr(cli, 'SYSTEMD_AVAILABLE', True)

    mocker.patch.context_manager(systemd, 'sudo')
    mocker.patch('sdnotify.socket')
    mocker.patch('config_ninja.systemd.sh.rm')
    mocker.patch('config_ninja.systemd.sh.tee')

    system_install_path = tmp_path / 'system'
    user_install_path = tmp_path / 'user'

    monkeypatch.setattr(systemd, 'SYSTEM_INSTALL_PATH', system_install_path)
    monkeypatch.setattr(systemd, 'USER_INSTALL_PATH', user_install_path)

    systemd.sh.systemctl = mocker.MagicMock()  # type: ignore[attr-defined,unused-ignore]

    return (system_install_path, user_install_path)


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
