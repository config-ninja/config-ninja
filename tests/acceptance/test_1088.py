"""Define acceptance tests for caching AppConfig requests."""

from __future__ import annotations

from unittest import mock

import boto3
import botocore
import botocore.paginate
import pytest
from mypy_boto3_appconfig import AppConfigClient

from config_ninja.contrib.appconfig import AppConfigBackend


@pytest.fixture
def mock_session() -> boto3.Session:
    """Mock the `AppConfig` session used by the `config_ninja.contrib.appconfig.AppConfigBackend` class."""
    return mock.MagicMock(spec_set=boto3.Session)


@pytest.fixture
def mock_client(mock_session: mock.MagicMock) -> AppConfigClient:
    """Create a mocked `AppConfig` client and patch the session to return it."""
    client = mock.MagicMock(spec_set=AppConfigClient)
    mock_session.client.return_value = client
    return client


@pytest.fixture
def mock_paginator(mock_client: mock.MagicMock) -> botocore.paginate.Paginator[str]:
    """Create a mocked paginator and patch the client to return it."""
    paginator = mock.MagicMock(spec_set=botocore.paginate.Paginator)
    mock_client.get_paginator.return_value = paginator
    return paginator


@pytest.fixture
def mock_page_iterator(mock_paginator: mock.MagicMock) -> botocore.paginate.PageIterator[str]:
    """Create a mocked page iterator and patch the paginator to return it."""
    paginated_results = mock.MagicMock(spec_set=botocore.paginate.PageIterator)
    paginated_results.search.return_value = [f'mock-id-{__name__}']
    mock_paginator.paginate.return_value = paginated_results
    return paginated_results


def test_cached_appconfig_requests(
    mock_session: boto3.Session, mock_page_iterator: botocore.paginate.PageIterator[str]
) -> None:
    """Verify requests are cached when instantiating the `config_ninja.contrib.appconfig.AppConfigBackend` class."""
    # Arrange
    num_api_requests = (
        0
        + 1  # get application ID
        + 1  # get configuration profile ID
        + 1  # get environment ID
    )
    num_instances = 30
    num_cache_hits = (num_instances - 1) * num_api_requests

    mock_search: mock.MagicMock = mock_page_iterator.search  # type: ignore[assignment]

    # Act
    for _ in range(num_instances):
        AppConfigBackend.new(f'{__name__}_app', f'{__name__}_config', f'{__name__}_env')

    # Assert
    assert num_api_requests == mock_search.call_count
    assert num_cache_hits == AppConfigBackend._get_id_from_name.cache_info().hits  # pyright: ignore[reportPrivateUsage]
