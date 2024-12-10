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

import logging
import typing

from config_ninja.backend import Backend

if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

__all__ = ['SecretsManagerBackend']

logger = logging.getLogger(__name__)


class SecretsManagerBackend(Backend):
    """Retrieve config data from the AWS SecretsManager service.

    ## Usage

    >>> backend = SecretsManagerBackend(secretsmanager_client, 'secret-id')
    >>> print(backend.get())
    {"username": "admin", "pass}
    """

    client: SecretsManagerClient
    """The `boto3` client used to communicate with the AWS Secrets Manager service."""

    secret_id: str
    """The ID of the secret to retrieve"""

    version_id: str | None = None

    def __init__(self, client: SecretsManagerClient, secret_id: str) -> None:
        """Initialize the backend."""
        logger.debug("Initialize: %s(client=%s, '%s')", self.__class__.__name__, client, secret_id)
        self.client = client
        self.secret_id = secret_id

    def __str__(self) -> str:
        """Return the secret ID."""
        return self.secret_id if not self.version_id else f'{self.secret_id} (version: {self.version_id})'

    def get(self) -> str:
        """Retrieve the secret data."""
        response = self.client.get_secret_value(SecretId=self.secret_id)
        self.version_id = response.get('VersionId')
        return response['SecretString']
