"""Integrate with the AWS AppConfig service."""
from __future__ import annotations

import logging
import time
import warnings
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal

import boto3
import yaml

from config_ninja.backend import AbstractBackend

try:  # pragma: no cover
    from typing import TypeAlias  # type: ignore[attr-defined,unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import TypeAlias


if TYPE_CHECKING:  # pragma: no cover
    from botocore.paginate import PageIterator
    from mypy_boto3_appconfig.client import AppConfigClient
    from mypy_boto3_appconfigdata import AppConfigDataClient

MINIMUM_POLL_INTERVAL_SECONDS = 60


OperationName: TypeAlias = Literal[
    'list_applications', 'list_configuration_profiles', 'list_environments'
]

logger = logging.getLogger(__name__)


class AppConfigBackend(AbstractBackend):
    """Retrieve the deployed configuration from AWS AppConfig.

    # Usage

    >>> backend = AppConfigBackend(appconfigdata_client, 'app-id', 'conf-id', 'env-id')
    >>> print(backend.get_raw())
    key_0: value_0
    key_1: 1
    key_2: true
    key_3:
        - 1
        - 2
        - 3

    >>> backend.get()
    {'key_0': 'value_0', 'key_1': 1, 'key_2': True, 'key_3': [1, 2, 3]}
    """

    client: AppConfigDataClient

    application_id: str
    configuration_profile_id: str
    environment_id: str

    def __init__(
        self,
        client: AppConfigDataClient,
        app_id: str,
        config_profile_id: str,
        env_id: str,
        #
        # note: the following are required for compatibility with AbstractBackend
        *_: Any,
        **__: Any,
    ) -> None:
        """Start a configuration session with the given parameters."""
        self.client = client

        self.application_id = app_id
        self.configuration_profile_id = config_profile_id
        self.environment_id = env_id

    def __str__(self) -> str:
        """Include properties in the string representation.

        >>> print(str(AppConfigBackend(appconfigdata_client, 'app-id', 'conf-id', 'env-id')))
        AppConfigBackend(app_id='app-id', conf_profile_id='conf-id', env_id='env-id')
        """
        return (
            f"{self.__class__.__name__}(app_id='{self.application_id}', "
            f"conf_profile_id='{self.configuration_profile_id}', "
            f"env_id='{self.environment_id}')"
        )

    @staticmethod
    def _get_id_from_name(
        name: str, operation_name: OperationName, client: AppConfigClient, **kwargs: Any
    ) -> str:
        page_iterator: PageIterator = client.get_paginator(operation_name).paginate(**kwargs)
        ids: list[str] = list(page_iterator.search(f'Items[?Name == `{name}`].Id'))

        if not ids:
            raise ValueError(f'no "{operation_name}" results found for Name="{name}"')

        if len(ids) > 1:
            warnings.warn(
                f"'{operation_name}' found {len(ids)} results for Name='{name}'; "
                f"'{ids[0]}' will be used and the others ignored: {ids[1:]}",
                category=RuntimeWarning,
                stacklevel=3,
            )

        return ids[0]

    def get(self, decoder: Callable[[str], dict[str, Any]] = yaml.safe_load) -> dict[str, Any]:
        """Retrieve and decode the latest configuration deployment."""
        return decoder(self.get_raw())

    def get_raw(self) -> str:
        """Retrieve the latest configuration deployment as a raw string."""
        token = self.client.start_configuration_session(
            ApplicationIdentifier=self.application_id,
            EnvironmentIdentifier=self.environment_id,
            ConfigurationProfileIdentifier=self.configuration_profile_id,
            RequiredMinimumPollIntervalInSeconds=MINIMUM_POLL_INTERVAL_SECONDS,
        )['InitialConfigurationToken']

        resp = self.client.get_latest_configuration(ConfigurationToken=token)
        return str(resp['Configuration'].read().decode())

    @classmethod
    def get_application_id(cls, name: str, client: AppConfigClient) -> str:
        """Retrieve the application ID for the given application name."""
        return cls._get_id_from_name(name, 'list_applications', client)

    @classmethod
    def get_configuration_profile_id(
        cls, name: str, client: AppConfigClient, application_id: str
    ) -> str:
        """Retrieve the configuration profile ID for the given configuration profile name."""
        return cls._get_id_from_name(
            name, 'list_configuration_profiles', client, ApplicationId=application_id
        )

    @classmethod
    def get_environment_id(cls, name: str, client: AppConfigClient, application_id: str) -> str:
        """Retrieve the environment ID for the given environment name & application ID."""
        return cls._get_id_from_name(
            name, 'list_environments', client, ApplicationId=application_id
        )

    @classmethod
    def new(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        application_name: str,
        configuration_profile_name: str,
        environment_name: str,
        session: boto3.Session | None = None,
    ) -> AppConfigBackend:
        """Create a new instance connected to the backend.

        # Usage

        >>> session = getfixture('mock_session_with_1_id')
        >>> backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        >>> print(f"{backend}")
        AppConfigBackend(app_id='id-1', conf_profile_id='id-1', env_id='id-1')

        ## Error: No IDs Found

        >>> session = getfixture('mock_session_with_0_ids')
        >>> backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        Traceback (most recent call last):
        ...
        ValueError: no "list_applications" results found for Name="app-name"

        ## Warning: Multiple IDs Found

        The first ID is used and the others ignored.

        >>> session = getfixture('mock_session_with_2_ids')
        >>> with pytest.warns(RuntimeWarning):
        ...     backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        """
        logger.info(
            'creating new instance: %s(app="%s", conf="%s", env="%s")',
            cls.__name__,
            application_name,
            configuration_profile_name,
            environment_name,
        )

        session = session or boto3.Session()
        appconfig_client = session.client('appconfig')  # pyright: ignore[reportUnknownMemberType]
        application_id = cls.get_application_id(application_name, appconfig_client)
        configuration_profile_id = cls.get_configuration_profile_id(
            configuration_profile_name, appconfig_client, application_id
        )
        environment_id = cls.get_environment_id(environment_name, appconfig_client, application_id)

        client: AppConfigDataClient = session.client('appconfigdata')  # pyright: ignore[reportUnknownMemberType]

        return cls(client, application_id, configuration_profile_id, environment_id)

    def poll(self, interval: int = MINIMUM_POLL_INTERVAL_SECONDS) -> Iterator[str]:
        """Poll the AppConfig service for configuration changes.

        # Usage

        >>> backend = AppConfigBackend(appconfigdata_client, 'app-id', 'conf-id', 'env-id')
        >>> content = next(backend.poll())
        >>> print(content)
        key_0: value_0
        key_1: 1
        key_2: true
        key_3:
            - 1
            - 2
            - 3

        ## Polling Too Quickly

        If polling is done too quickly, AWS AppConfig will raise a `BadRequestException`. This is
        handled automatically by the backend, which will retry the request after waiting for half
        the interval.

        >>> client = getfixture('mock_poll_too_early')    # seed a `BadRequestException`

        >>> backend = AppConfigBackend(client, 'app-id', 'conf-id', 'env-id')
        >>> content = next(backend.poll(interval=0.01))   # it is handled successfully
        >>> print(content)
        key_0: value_0
        key_1: 1
        key_2: true
        key_3:
            - 1
            - 2
            - 3
        """
        token = self.client.start_configuration_session(
            ApplicationIdentifier=self.application_id,
            EnvironmentIdentifier=self.environment_id,
            ConfigurationProfileIdentifier=self.configuration_profile_id,
            RequiredMinimumPollIntervalInSeconds=interval,
        )['InitialConfigurationToken']

        while True:
            logger.debug('polling for configuration changes')
            try:
                resp = self.client.get_latest_configuration(ConfigurationToken=token)
            except self.client.exceptions.BadRequestException as exc:
                if exc.response['Error']['Message'] != 'Request too early':
                    raise
                time.sleep(interval / 2)
                continue

            token = resp['NextPollConfigurationToken']
            if content := resp['Configuration'].read():
                yield content.decode()
            else:
                logger.debug('no configuration changes')

            time.sleep(resp['NextPollIntervalInSeconds'])


logger.debug('successfully imported %s', __name__)
