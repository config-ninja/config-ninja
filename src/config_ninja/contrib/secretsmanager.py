"""Integrate with the AWS SecretsManager service.

## Example

The following `config-ninja`_ settings file configures the `SecretsManagerBackend` to install
`~/.docker/config.json` from the latest version of the secret:

```yaml
.. include:: ../../../examples/secretsmanager-backend.yaml
```

.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

from __future__ import annotations

import asyncio
import logging
import typing

import boto3

from config_ninja.backend import Backend
from config_ninja.contrib.appconfig import MINIMUM_POLL_INTERVAL_SECONDS

if typing.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_secretsmanager import SecretsManagerClient


__all__ = ['SecretsManagerBackend']

logger = logging.getLogger(__name__)


class SecretsManagerBackend(Backend):
    """Retrieve config data from the AWS SecretsManager service.

    ## Usage

    >>> backend = SecretsManagerBackend(secretsmanager_client, 'secret-id')
    >>> print(backend.get())
    {"username": "admin", "password": 1234}
    """

    client: SecretsManagerClient
    """The `boto3` client used to communicate with the AWS Secrets Manager service."""

    secret_id: str
    """The ID of the secret to retrieve"""

    version_id: str | None = None

    def __init__(self, client: SecretsManagerClient, secret_id: str) -> None:
        """Initialize the backend."""
        self.client = client
        self.secret_id = secret_id
        logger.debug('Initialize: %s', repr(self))

    def __str__(self) -> str:
        """Return the secret ID.

        >>> print(str(SecretsManagerBackend(secretsmanager_client, 'secret-id')))
        secret-id
        """
        return self.secret_id if not self.version_id else f'{self.secret_id} (version: {self.version_id})'

    @classmethod
    def new(cls, secret_id: str, session: boto3.Session | None = None) -> SecretsManagerBackend:  # pylint: disable=arguments-differ
        """Instantiate a new `boto3` client and `SecretsManagerBackend` object.

        >>> backend = SecretsManagerBackend.new('secret-id')
        >>> print(backend)
        secret-id
        """
        logger.info('Create new instance: %s(secret_id="%s")', cls.__name__, secret_id)
        session = session or boto3.Session()
        client: SecretsManagerClient = session.client('secretsmanager')  # pyright: ignore[reportUnknownMemberType]
        return cls(client, secret_id)

    def get(self) -> str:
        """Retrieve the secret data."""
        response = self.client.get_secret_value(SecretId=self.secret_id)
        self.version_id = response.get('VersionId')
        return response['SecretString']

    def _retrieve_current_version(self) -> str:
        """Retrieve the version ID of the current value of the secret.

        A value error is raised if no current version was found:

        >>> backend = SecretsManagerBackend(secretsmanager_client_no_current, 'secret-id')
        >>> with pytest.raises(ValueError):
        ...     backend._retrieve_current_version()
        """
        response = self.client.list_secret_version_ids(SecretId=self.secret_id)
        for version in response['Versions']:
            if 'AWSCURRENT' in version.get('VersionStages', []) and (version_id := version.get('VersionId')):
                return version_id

        raise ValueError(f"No current version found for secret '{self}'")

    async def poll(self, interval: int = MINIMUM_POLL_INTERVAL_SECONDS) -> typing.AsyncIterator[str]:
        """Poll for changes to the secret."""
        while True:
            logger.debug('Poll for configuration changes')
            try:
                version_id = self._retrieve_current_version()
            except ValueError as exc:
                logger.warning('%s', exc)
            else:
                if version_id and version_id != self.version_id:
                    yield self.get()

            await asyncio.sleep(interval)

    def _async_doctests(self) -> None:
        """Define `async` `doctest` tests in this method to improve documentation.

        Verify that an empty response to the `boto3` client is handled and the polling continues:
        >>> backend = SecretsManagerBackend(secretsmanager_client, 'secret-id')
        >>> content = asyncio.run(anext(backend.poll(interval=0.01)))
        >>> print(content)
        {"username": "admin", "password": 1234}

        >>> backend = SecretsManagerBackend(secretsmanager_client_no_current_initially, 'secret-id')
        >>> _ = backend.get(); backend.version_id   # fetch the initial value from the mock fixture
        'v6'

        >>> content = asyncio.run(anext(backend.poll(interval=0.01)))
        >>> print(content)
        {"username": "admin", "password": 1234}
        """
