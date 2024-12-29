"""Integrate with the AWS AppConfig service.

## Example

The following `config-ninja`_ settings file configures the `AppConfigBackend` to install
`/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json` from the latest version deployed
through AWS AppConfig:

```yaml
.. include:: ../../../examples/appconfig-backend.yaml
```

.. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
"""

from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, Literal

import boto3

from config_ninja.backend import Backend

try:  # pragma: no cover
    from typing import TypeAlias  # type: ignore[attr-defined,unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import TypeAlias


if TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_appconfig.client import AppConfigClient
    from mypy_boto3_appconfigdata import AppConfigDataClient

__all__ = ['AppConfigBackend']

MINIMUM_POLL_INTERVAL_SECONDS = 60


OperationName: TypeAlias = Literal['list_applications', 'list_configuration_profiles', 'list_environments']

logger = logging.getLogger(__name__)


class AppConfigBackend(Backend):
    """Retrieve the deployed configuration from AWS AppConfig.

    ## Usage

    To retrieve the configuration, use the `AppConfigBackend.get()` method:

    >>> backend = AppConfigBackend(appconfigdata_client, 'app-id', 'conf-id', 'env-id')
    >>> print(backend.get())
    key_0: value_0
    key_1: 1
    key_2: true
    key_3:
        - 1
        - 2
        - 3
    """

    client: AppConfigDataClient
    """The `boto3` client used to communicate with the AWS AppConfig service."""

    application_id: str
    """See [Creating a namespace for your application in AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-namespace.html)"""
    configuration_profile_id: str
    """See [Creating a configuration profile in AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-profile.html)"""
    environment_id: str
    """See [Creating environments for your application in AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-environment.html)"""

    def __init__(
        self,
        client: AppConfigDataClient,
        app_id: str,
        config_profile_id: str,
        env_id: str,
    ) -> None:
        """Initialize the backend."""
        logger.debug(
            "Initialize: %s(client=%s, app_id='%s', conf_id='%s', env_id='%s')",
            self.__class__.__name__,
            client,
            app_id,
            config_profile_id,
            env_id,
        )
        self.client = client

        self.application_id = app_id
        self.configuration_profile_id = config_profile_id
        self.environment_id = env_id

    def __str__(self) -> str:
        """Include properties in the string representation.

        >>> print(str( AppConfigBackend(appconfigdata_client, 'app-id', 'conf-id', 'env-id') ))
        boto3.client('appconfigdata').start_configuration_session(ApplicationIdentifier='app-id', ConfigurationProfileIdentifier='conf-id', EnvironmentIdentifier='env-id')
        """
        return (
            "boto3.client('appconfigdata').start_configuration_session("
            f"ApplicationIdentifier='{self.application_id}', "
            f"ConfigurationProfileIdentifier='{self.configuration_profile_id}', "
            f"EnvironmentIdentifier='{self.environment_id}')"
        )

    @staticmethod
    def _get_id_from_name(name: str, operation_name: OperationName, client: AppConfigClient, **kwargs: Any) -> str:
        out: Iterator[str] = (
            client.get_paginator(operation_name).paginate(**kwargs).search(f'Items[?Name == `{name}`].Id')
        )
        ids = list(out)

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

    def get(self) -> str:
        """Retrieve the latest configuration deployment as a string."""
        logger.debug('Retrieve latest configuration (%s)', self)
        token = self.client.start_configuration_session(
            ApplicationIdentifier=self.application_id,
            EnvironmentIdentifier=self.environment_id,
            ConfigurationProfileIdentifier=self.configuration_profile_id,
            RequiredMinimumPollIntervalInSeconds=MINIMUM_POLL_INTERVAL_SECONDS,
        )['InitialConfigurationToken']

        resp = self.client.get_latest_configuration(ConfigurationToken=token)
        return resp['Configuration'].read().decode()

    @classmethod
    def get_application_id(cls, name: str, client: AppConfigClient) -> str:
        """Retrieve the application ID for the given application name."""
        return cls._get_id_from_name(name, 'list_applications', client)

    @classmethod
    def get_configuration_profile_id(cls, name: str, client: AppConfigClient, application_id: str) -> str:
        """Retrieve the configuration profile ID for the given configuration profile name."""
        return cls._get_id_from_name(name, 'list_configuration_profiles', client, ApplicationId=application_id)

    @classmethod
    def get_environment_id(cls, name: str, client: AppConfigClient, application_id: str) -> str:
        """Retrieve the environment ID for the given environment name & application ID."""
        return cls._get_id_from_name(name, 'list_environments', client, ApplicationId=application_id)

    @classmethod
    def new(  # pylint: disable=arguments-differ  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        application_name: str,
        configuration_profile_name: str,
        environment_name: str,
        session: boto3.Session | None = None,
    ) -> AppConfigBackend:
        """Create a new instance of the backend.

        ## Usage: `AppConfigBackend.new()`

        <!-- fixture is used for doctest but excluded from documentation
        >>> session = getfixture('mock_session_with_1_id')

        -->

        Use `boto3` to fetch IDs for based on name:

        >>> backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        >>> print(f"{backend}")
        boto3.client('appconfigdata').start_configuration_session(ApplicationIdentifier='id-1', ConfigurationProfileIdentifier='id-1', EnvironmentIdentifier='id-1')

        ### Error: No IDs Found

        >>> session = getfixture('mock_session_with_0_ids')  # fixture for doctest

        A `ValueError` is raised if no IDs are found for the given name:

        >>> backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        Traceback (most recent call last):
        ...
        ValueError: no "list_applications" results found for Name="app-name"

        ### Warning: Multiple IDs Found

        >>> session = getfixture('mock_session_with_2_ids')

        The first ID is used and the others ignored.

        >>> with pytest.warns(RuntimeWarning):
        ...     backend = AppConfigBackend.new('app-name', 'conf-name', 'env-name', session)
        """
        logger.info(
            'Create new instance: %s(app="%s", conf="%s", env="%s")',
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

    async def poll(self, interval: int = MINIMUM_POLL_INTERVAL_SECONDS) -> AsyncIterator[str]:
        """Poll the AppConfig service for configuration changes.

        .. note::
            Methods written for `asyncio` need to jump through hoops to run as `doctest` tests.
            To improve the readability of this documentation, each Python code block corresponds to
            a `doctest` test defined in a private method.

        ## Usage: `AppConfigBackend.poll()`

        ```py
        In [1]: async for content in backend.poll():
           ...:     print(content)  # ← executes each time the configuration changes
        ```
        ```yaml
        key_0: value_0
        key_1: 1
        key_2: true
        key_3:
            - 1
            - 2
            - 3
        ```

        .. note::
            If polling is done too quickly, the AWS AppConfig client will raise a
            `BadRequestException`. This is handled automatically by the backend, which will retry
            the request after waiting for half the given `interval`.
        """
        token = self.client.start_configuration_session(
            ApplicationIdentifier=self.application_id,
            EnvironmentIdentifier=self.environment_id,
            ConfigurationProfileIdentifier=self.configuration_profile_id,
            RequiredMinimumPollIntervalInSeconds=interval,
        )['InitialConfigurationToken']

        while True:
            logger.debug('Poll for configuration changes')
            try:
                resp = self.client.get_latest_configuration(ConfigurationToken=token)
            except self.client.exceptions.BadRequestException as exc:
                if exc.response['Error']['Message'] != 'Request too early':  # pragma: no cover
                    raise
                logger.debug('Request too early; retrying in %d seconds', interval / 2)
                await asyncio.sleep(interval / 2)
                continue

            token = resp['NextPollConfigurationToken']
            if content := resp['Configuration'].read():
                yield content.decode()
            else:
                logger.debug('No configuration changes')

            await asyncio.sleep(resp['NextPollIntervalInSeconds'])

    def _async_doctests(self) -> None:
        """Define `async` `doctest` tests in this method to improve documentation.

        Verify that an empty response to the `boto3` client is handled and the polling continues:
        >>> backend = AppConfigBackend(appconfigdata_client_first_empty, 'app-id', 'conf-id', 'env-id')
        >>> content = asyncio.run(anext(backend.poll(interval=0.01)))
        >>> print(content)
        key_0: value_0
        key_1: 1
        key_2: true
        key_3:
            - 1
            - 2
            - 3


        >>> client = getfixture('mock_poll_too_early')    # seed a `BadRequestException`

        >>> backend = AppConfigBackend(client, 'app-id', 'conf-id', 'env-id')
        >>> content = asyncio.run(anext(backend.poll(interval=0.01)))   # it is handled successfully
        >>> print(content)
        key_0: value_0
        key_1: 1
        key_2: true
        key_3:
            - 1
            - 2
            - 3
        """


logger.debug('successfully imported %s', __name__)
