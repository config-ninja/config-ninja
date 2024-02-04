"""Generate a `systemd` unit file for installation as a service.

The following `jinja2` template is used to generate the `systemd` unit file:

```jinja
.. include:: ./templates/systemd.service.j2
```

Run the CLI's `install`_ command to install the service:

```sh
❯ config-ninja self install --env AWS_PROFILE --user
Installing /home/ubuntu/.config/systemd/user/config-ninja.service
● config-ninja.service - config synchronization daemon
     Loaded: loaded (/home/ubuntu/.config/systemd/user/config-ninja.service; disabled; vendor preset: enabled)
     Active: active (running) since Sun 2024-01-21 22:37:52 EST; 7ms ago
    Process: 20240 ExecStartPre=/usr/local/bin/config-ninja self print (code=exited, status=0/SUCCESS)
   Main PID: 20241 (config-ninja)
     CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/config-ninja.service
             └─20241 /usr/local/bin/python /usr/local/bin/config-ninja monitor

Jan 21 22:37:51 ubuntu config-ninja[20240]:     path: /tmp/config-ninja/settings-subset.toml
Jan 21 22:37:51 ubuntu config-ninja[20240]:   source:
Jan 21 22:37:51 ubuntu config-ninja[20240]:     backend: local
Jan 21 22:37:51 ubuntu config-ninja[20240]:     format: yaml
Jan 21 22:37:51 ubuntu config-ninja[20240]:     new:
Jan 21 22:37:51 ubuntu config-ninja[20240]:       kwargs:
Jan 21 22:37:51 ubuntu config-ninja[20240]:         path: config-ninja-settings.yaml
Jan 21 22:37:52 ubuntu config-ninja[20241]: Begin monitoring: ['example-local', 'example-local-template', 'example-appconfig']
Jan 21 22:37:52 ubuntu systemd[592]: Started config synchronization daemon.

SUCCESS ✅
```

.. _install: https://bryant-finney.github.io/config-ninja/config_ninja/cli.html#config-ninja-self-install
"""  # noqa: RUF002
from __future__ import annotations

import contextlib
import logging
import os
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2
import sdnotify

if TYPE_CHECKING:  # pragma: no cover
    import sh
else:
    try:
        import sh
    except ImportError:  # pragma: no cover
        sh = None

# pylint: disable=no-member
SERVICE_NAME = 'config-ninja.service'
SYSTEM_INSTALL_PATH = Path('/etc/systemd/system')
"""The file path for system-wide installation."""

USER_INSTALL_PATH = (
    Path(os.getenv('XDG_CONFIG_HOME') or Path.home() / '.config') / 'systemd' / 'user'
)
"""The file path for user-local installation."""

__all__ = ['SYSTEM_INSTALL_PATH', 'USER_INSTALL_PATH', 'Service', 'notify']
logger = logging.getLogger(__name__)

try:
    sudo = sh.contrib.sudo
except AttributeError:  # pragma: no cover

    @contextlib.contextmanager
    def dummy() -> typing.Iterator[None]:
        """We might be running inside a container; or we might be on Windows."""
        yield

    sudo = dummy()


def notify() -> None:  # pragma: no cover
    """Notify `systemd` that the service has finished starting up and is ready."""
    sock = sdnotify.SystemdNotifier()
    sock.notify('READY=1')  # pyright: ignore[reportUnknownMemberType]


class Service:
    """Manipulate the `systemd` service file for `config-ninja`.

    ## User Installation

    To install the service for only the current user, pass `user_mode=True` to the initializer:

    >>> svc = Service('config_ninja', 'systemd.service.j2', user_mode=True)
    >>> _ = svc.install(
    ...     config_ninja_cmd='config-ninja', workdir='.', environ={'TESTING': 'true'}
    ... )

    >>> print(svc.read())
    [Unit]
    Description=config synchronization daemon
    After=network.target
    <BLANKLINE>
    [Service]
    Environment=PYTHONUNBUFFERED=true
    Environment=TESTING=true
    ExecStartPre=config-ninja self print
    ExecStart=config-ninja monitor
    Restart=always
    RestartSec=30s
    Type=notify
    WorkingDirectory=...
    <BLANKLINE>
    [Install]
    Alias=config-ninja.service

    >>> svc.uninstall()

    ## System Installation

    For system-wide installation:

    >>> svc = Service('config_ninja', 'systemd.service.j2', user_mode=False)
    >>> _ = svc.install(
    ...     config_ninja_cmd='config-ninja', workdir='.', environ={'TESTING': 'true'}
    ... )

    >>> svc.uninstall()
    """

    path: Path
    """The installation location of the `systemd` unit file."""

    tmpl: jinja2.Template
    """Load the template on initialization."""

    user_mode: bool
    """Whether to install the service for the full system or just the current user."""

    def __init__(self, provider: str, template: str, user_mode: bool) -> None:
        """Prepare to render the specified `template` from the `provider` package."""
        loader = jinja2.PackageLoader(provider)
        env = jinja2.Environment(autoescape=jinja2.select_autoescape(default=True), loader=loader)
        self.tmpl = env.get_template(template)
        self.user_mode = user_mode
        self.path = (USER_INSTALL_PATH if user_mode else SYSTEM_INSTALL_PATH) / SERVICE_NAME

    def _install_system(self, content: str) -> str:
        with sudo:
            logger.info('writing to %s', self.path)
            sh.mkdir('-p', str(self.path.parent))
            sh.tee(str(self.path), _in=content, _out='/dev/null')

            logger.info('enabling and starting %s', self.path.name)
            sh.systemctl.start(self.path.name)
            return sh.systemctl.status(self.path.name)

    def _install_user(self, content: str) -> str:
        logger.info('writing to %s', self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding='utf-8')

        logger.info('enabling and starting %s', self.path.name)
        sh.systemctl.start('--user', self.path.name)
        return sh.systemctl.status('--user', self.path.name)

    def _uninstall_system(self) -> None:
        with sudo:
            logger.info('stopping and disabling %s', self.path.name)
            sh.systemctl.disable('--now', self.path.name)

            logger.info('removing %s', self.path)
            sh.rm(str(self.path))

    def _uninstall_user(self) -> None:
        logger.info('stopping and disabling %s', self.path.name)
        sh.systemctl.disable('--user', '--now', self.path.name)

        logger.info('removing %s', self.path)
        self.path.unlink()

    def install(self, **kwargs: typing.Any) -> str:
        """Render the `systemd` service file from `kwargs` and install it."""
        rendered = self.render(**kwargs)
        if self.user_mode:
            return self._install_user(rendered)
        return self._install_system(rendered)

    def read(self) -> str:
        """Read the `systemd` service file."""
        return self.path.read_text(encoding='utf-8')

    def render(self, **kwargs: typing.Any) -> str:
        """Render the `systemd` service file from the given parameters."""
        if workdir := kwargs.get('workdir'):
            kwargs['workdir'] = Path(workdir).absolute()

        kwargs.setdefault('user_mode', self.user_mode)
        if hasattr(os, 'geteuid'):  # pragma: no cover  # windows
            kwargs.setdefault('user', os.geteuid())

        if hasattr(os, 'getegid'):  # pragma: no cover  # windows
            kwargs.setdefault('group', os.getegid())

        return self.tmpl.render(**kwargs)

    def uninstall(self) -> None:
        """Disable, stop, and delete the service."""
        if self.user_mode:
            self._uninstall_user()
        else:
            self._uninstall_system()
