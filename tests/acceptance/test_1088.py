"""Define acceptance tests for caching AppConfig requests."""

from __future__ import annotations

from unittest import mock

import botocore
import botocore.paginate
import pytest

from config_ninja.contrib.appconfig import AppConfigBackend


@pytest.mark.usefixtures('mock_session')
def test_cached_appconfig_requests(mock_page_iterator: botocore.paginate.PageIterator[str]) -> None:
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
