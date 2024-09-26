"""Create `config-ninja`_'s CLI with `typer`_.

.. include:: cli.md

.. note:: `typer`_ does not support `from __future__ import annotations` as of 2023-12-31

.. _config-ninja: https://bryant-finney.github.io/config-ninja/config_ninja.html
.. _typer: https://typer.tiangolo.com/
"""

import asyncio
import contextlib
import logging
import os
import sys
import typing
from pathlib import Path

import pyspry
import rich
import typer
import yaml
from rich.logging import RichHandler
from rich.markdown import Markdown

import config_ninja
from config_ninja import controller, systemd
from config_ninja.controller import SYSTEMD_AVAILABLE

try:
    from typing import Annotated, TypeAlias  # type: ignore[attr-defined,unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import Annotated, TypeAlias  # type: ignore[assignment,attr-defined,unused-ignore]


# ruff: noqa: PLR0913
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments

__all__ = [
    'app',
    'get',
    'apply',
    'monitor',
    'self_print',
    'install',
    'uninstall',
    'version',
    'main',
]

LOG_MISSING_SETTINGS_MESSAGE = "Could not find [bold blue]config-ninja[/]'s settings file"
LOG_VERBOSITY_MESSAGE = 'logging verbosity set to [green]%s[/green]'

logger = logging.getLogger(__name__)

app_kwargs: typing.Dict[str, typing.Any] = {
    'context_settings': {'help_option_names': ['-h', '--help']},
    'no_args_is_help': True,
    'rich_markup_mode': 'rich',
}

app = typer.Typer(**app_kwargs)
"""The root `typer`_ application.

.. _typer: https://typer.tiangolo.com/
"""

self_app = typer.Typer(**app_kwargs)

app.add_typer(self_app, name='self', help='Operate on this installation of [bold blue]config-ninja[/].')

ActionType = typing.Callable[[str], typing.Any]


def help_callback(ctx: typer.Context, value: typing.Optional[bool] = None) -> None:
    """Print the help message for the command."""
    if ctx.resilient_parsing:  # pragma: no cover
        return

    if value:
        rich.print(ctx.get_help())
        raise typer.Exit()


HelpAnnotation: TypeAlias = Annotated[
    typing.Optional[bool],
    typer.Option(
        '-h',
        '--help',
        callback=help_callback,
        rich_help_panel='Global',
        show_default=False,
        is_eager=True,
        help='Show this message and exit.',
    ),
]

KeyAnnotation: TypeAlias = Annotated[
    str,
    typer.Argument(help='The key of the configuration object to retrieve', show_default=False),
]
OptionalKeyAnnotation: TypeAlias = Annotated[
    typing.Optional[typing.List[str]],
    typer.Argument(
        help='Apply the configuration object(s) with matching key(s)'
        ' (multiple values may be provided). If unspecified, all objects will be applied',
        show_default=False,
        metavar='[KEY...]',
    ),
]
PollAnnotation: TypeAlias = Annotated[
    typing.Optional[bool],
    typer.Option(
        '-p',
        '--poll',
        help='Enable polling; print the configuration on changes.',
        show_default=False,
    ),
]
PrintAnnotation: TypeAlias = Annotated[
    typing.Optional[bool],
    typer.Option(
        '-p',
        '--print-only',
        help='Just print the [bold cyan]config-ninja.service[/] file; do not write.',
        show_default=False,
    ),
]


def load_config(ctx: typer.Context, value: typing.Optional[Path]) -> None:
    """Load the settings file from the given path."""
    if ctx.resilient_parsing:  # pragma: no cover
        return

    ctx.ensure_object(dict)
    if not value and 'settings' in ctx.obj:
        logger.debug('already loaded settings')
        return

    try:
        settings_file = value or config_ninja.resolve_settings_path()
    except FileNotFoundError as exc:
        logger.warning(
            '%s%s',
            LOG_MISSING_SETTINGS_MESSAGE,
            (' at any of the following locations:\n  - ' + '\n  - '.join(f'{p}' for p in exc.args[1]))
            if len(exc.args) > 1
            else '',
            extra={'markup': True},
        )
        ctx.obj['settings'] = None

    else:
        ctx.obj['settings'] = config_ninja.load_settings(settings_file)


ConfigAnnotation: TypeAlias = Annotated[
    typing.Optional[Path],
    typer.Option(
        '-c',
        '--config',
        callback=load_config,
        help="Path to [bold blue]config-ninja[/]'s own configuration file.",
        rich_help_panel='Global',
        show_default=False,
    ),
]
UserAnnotation: TypeAlias = Annotated[
    bool,
    typer.Option(
        '-u',
        '--user',
        '--user-mode',
        help='User mode installation (does not require [bold orange3]sudo[/])',
        show_default=False,
    ),
]
WorkdirAnnotation: TypeAlias = Annotated[
    typing.Optional[Path],
    typer.Option('-w', '--workdir', help='Run the service from this directory.', show_default=False),
]


def parse_env(ctx: typer.Context, value: typing.Optional[typing.List[str]]) -> typing.List[str]:
    """Parse the environment variables from the command line."""
    if ctx.resilient_parsing or not value:
        return []

    return [v for val in value for v in val.split(',')]


EnvNamesAnnotation: TypeAlias = Annotated[
    typing.Optional[typing.List[str]],
    typer.Option(
        '-e',
        '--env',
        help='Embed these environment variables into the unit file. Can be used multiple times.',
        show_default=False,
        callback=parse_env,
        metavar='NAME[,NAME...]',
    ),
]


class UserGroup(typing.NamedTuple):
    """Run the service using this user (and optionally group)."""

    user: str
    """The user to run the service as."""

    group: typing.Optional[str] = None
    """The group to run the service as."""

    @classmethod
    def parse(cls, value: str) -> 'UserGroup':
        """Parse the `--run-as user[:group]` argument for the `systemd` service."""
        return cls(*value.split(':'))


RunAsAnnotation: TypeAlias = Annotated[
    typing.Optional[UserGroup],
    typer.Option(
        '--run-as',
        help='Configure the systemd unit to run the service as this user (and optionally group).',
        metavar='user[:group]',
        parser=UserGroup.parse,
    ),
]


class Variable(typing.NamedTuple):
    """Set this variable in the shell used to run the `systemd` service."""

    name: str
    """The name of the variable."""

    value: str
    """The value of the variable."""


def parse_var(value: str) -> Variable:
    """Parse the `--var VARIABLE=VALUE` arguments for setting variables in the `systemd` service."""
    try:
        parsed = Variable(*value.split('='))
    except TypeError as exc:
        rich.print(f'[red]ERROR[/]: Invalid argument (expected [yellow]VARIABLE=VALUE[/] pair): [purple]{value}[/]')
        raise typer.Exit(1) from exc

    return parsed


VariableAnnotation: TypeAlias = Annotated[
    typing.Optional[typing.List[Variable]],
    typer.Option(
        '--var',
        help='Embed the specified [yellow]VARIABLE=VALUE[/] into the unit file. Can be used multiple times.',
        metavar='VARIABLE=VALUE',
        show_default=False,
        parser=parse_var,
    ),
]


def configure_logging(ctx: typer.Context, verbose: typing.Optional[bool] = None) -> None:
    """Callback for the `--verbose` option to configure logging verbosity.

    By default, log messages at the `logging.INFO` level:

    >>> configure_logging(ctx)
    >>> caplog.messages
    ['logging verbosity set to [green]INFO[/green]']

    <!-- Clear the `caplog` fixture for the `doctest`, but exclude this from the docs
    >>> caplog.clear()

    -->
    When `verbose` is `True`, log messages at the `logging.DEBUG` level:

    >>> configure_logging(ctx, True)
    >>> caplog.messages
    ['logging verbosity set to [green]DEBUG[/green]']
    """
    if ctx.resilient_parsing:  # pragma: no cover  # this is for tab completions
        return

    verbosity = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=verbosity,
        format='%(message)s',
        force=True,
        datefmt='[%X]',
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger.debug(LOG_VERBOSITY_MESSAGE, logging.getLevelName(verbosity), extra={'markup': True})


VerbosityAnnotation = Annotated[
    typing.Optional[bool],
    typer.Option(
        '-v',
        '--verbose',
        callback=configure_logging,
        rich_help_panel='Global',
        help='Log messages at the [black]DEBUG[/] level.',
        is_eager=True,
        show_default=False,
    ),
]


def version_callback(ctx: typer.Context, value: typing.Optional[bool] = None) -> None:
    """Print the version of the package."""
    if ctx.resilient_parsing:  # pragma: no cover  # this is for tab completions
        return

    if value:
        rich.print(config_ninja.__version__)
        raise typer.Exit()


VersionAnnotation = Annotated[
    typing.Optional[bool],
    typer.Option(
        '-V',
        '--version',
        callback=version_callback,
        rich_help_panel='Global',
        show_default=False,
        is_eager=True,
        help='Print the version and exit.',
    ),
]


@contextlib.contextmanager
def handle_key_errors(objects: typing.Dict[str, typing.Any]) -> typing.Iterator[None]:
    """Handle KeyError exceptions within the managed context."""
    try:
        yield
    except KeyError as exc:  # pragma: no cover
        rich.print(f'[red]ERROR[/]: Missing key: [green]{exc.args[0]}[/]\n')
        rich.print(yaml.dump(objects))
        raise typer.Exit(1) from exc


async def poll_all(
    controllers: typing.List[controller.BackendController], get_or_write: typing.Literal['get', 'write']
) -> None:
    """Run the given controllers within an `asyncio` event loop to monitor and apply changes."""
    await asyncio.gather(*[ctrl.aget(rich.print) if get_or_write == 'get' else ctrl.awrite() for ctrl in controllers])


def _check_systemd() -> None:
    if not SYSTEMD_AVAILABLE:
        rich.print('[red]ERROR[/]: Missing [bold gray93]systemd[/]!')
        rich.print('Currently, this command only works on linux.')
        raise typer.Exit(1)


def _new_controller(settings: pyspry.Settings, key: str) -> controller.BackendController:
    ctrl = controller.BackendController(settings, key, handle_key_errors)
    ctrl.dest.path.parent.mkdir(parents=True, exist_ok=True)
    return ctrl


# ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
#                                             command definitions


@app.command()
def get(
    ctx: typer.Context,
    keys: OptionalKeyAnnotation = None,
    poll: PollAnnotation = False,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Print the value of the specified configuration object."""
    settings: pyspry.Settings = ctx.obj['settings']

    controllers = [_new_controller(settings, key) for key in keys or settings.OBJECTS]

    if poll:
        logger.debug(
            'Begin monitoring (read-only): %s',
            ', '.join(f'[yellow]{ctrl.key}[/yellow]' for ctrl in controllers),
            extra={'markup': True},
        )
        asyncio.run(poll_all(controllers, 'get'))
        return

    for ctrl in controllers:
        logger.debug('Get [yellow]%s[/yellow]: %s', ctrl.key, ctrl, extra={'markup': True})
        ctrl.get(rich.print)


@app.command()
def apply(
    ctx: typer.Context,
    keys: OptionalKeyAnnotation = None,
    poll: PollAnnotation = False,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Apply the specified configuration to the system."""
    settings: pyspry.Settings = ctx.obj['settings']

    controllers = [_new_controller(settings, key) for key in keys or settings.OBJECTS]

    if poll:
        rich.print('Begin monitoring: ' + ', '.join(f'[yellow]{ctrl.key}[/yellow]' for ctrl in controllers))
        asyncio.run(poll_all(controllers, 'write'))
        return

    for ctrl in controllers:
        rich.print(f'Apply [yellow]{ctrl.key}[/yellow]: {ctrl}')
        ctrl.write()


@app.command(
    deprecated=True,
    short_help='[dim]Apply all configuration objects to the filesystem, and poll for changes.[/] [red](deprecated)[/]',
    help='Use [bold blue]config-ninja apply --poll[/] instead.',
)
def monitor(ctx: typer.Context) -> None:
    """Apply all configuration objects to the filesystem, and poll for changes."""
    settings: pyspry.Settings = ctx.obj['settings']
    controllers = [controller.BackendController(settings, key, handle_key_errors) for key in settings.OBJECTS]
    for ctrl in controllers:
        ctrl.dest.path.parent.mkdir(parents=True, exist_ok=True)

    rich.print('Begin monitoring: ' + ', '.join(f'[yellow]{ctrl.key}[/yellow]' for ctrl in controllers))
    asyncio.run(poll_all(controllers, 'write'))


@self_app.command(name='print')
def self_print(
    ctx: typer.Context,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Print [bold blue]config-ninja[/]'s settings."""
    if not (settings := ctx.obj.get('settings')):
        raise typer.Exit(1)
    rich.print(yaml.dump(settings.OBJECTS))


@self_app.command()
def install(
    env_names: EnvNamesAnnotation = None,
    print_only: PrintAnnotation = None,
    run_as: RunAsAnnotation = None,
    user_mode: UserAnnotation = False,
    variables: VariableAnnotation = None,
    workdir: WorkdirAnnotation = None,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Install [bold blue]config-ninja[/] as a [bold gray93]systemd[/] service.

    Both --env and --var can be passed multiple times.

    Example:
            config-ninja self install --env FOO,BAR,BAZ --env SPAM --var EGGS=42

    The environment variables [purple]FOO[/], [purple]BAR[/], [purple]BAZ[/], and [purple]SPAM[/] will be read from the current shell and written to the service file, while [purple]EGGS[/] will be set to [yellow]42[/].
    """
    environ = {name: os.environ[name] for name in env_names or [] if name in os.environ}
    environ.update(variables or [])

    kwargs = {
        # the command to use when invoking config-ninja from systemd
        'config_ninja_cmd': sys.argv[0] if sys.argv[0].endswith('config-ninja') else f'{sys.executable} {sys.argv[0]}',
        # write these environment variables into the systemd service file
        'environ': environ,
        # run `config-ninja` from this directory (if specified)
        'workdir': workdir,
    }
    if run_as:
        kwargs['user'] = run_as.user
        if run_as.group:
            kwargs['group'] = run_as.group

    svc = systemd.Service('config_ninja', 'systemd.service.j2', user_mode)
    if print_only:
        rendered = svc.render(**kwargs)
        rich.print(Markdown(f'# {svc.path}\n```systemd\n{rendered}\n```'))
        raise typer.Exit(0)

    _check_systemd()

    rich.print(f'Installing {svc.path}')
    rich.print(svc.install(**kwargs))

    rich.print('[green]SUCCESS[/] :white_check_mark:')


@self_app.command()
def uninstall(
    print_only: PrintAnnotation = None,
    user: UserAnnotation = False,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Uninstall the [bold blue]config-ninja[/] [bold gray93]systemd[/] service."""
    svc = systemd.Service('config_ninja', 'systemd.service.j2', user or False)
    if print_only:
        rich.print(Markdown(f'# {svc.path}\n```systemd\n{svc.read()}\n```'))
        raise typer.Exit(0)

    _check_systemd()

    rich.print(f'Uninstalling {svc.path}')
    svc.uninstall()
    rich.print('[green]SUCCESS[/] :white_check_mark:')


@self_app.callback(
    invoke_without_command=True,
    name='self',
)
def self_main(
    ctx: typer.Context,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Print the help message for the `self` command."""
    if not ctx.invoked_subcommand:
        rich.print(ctx.get_help())


@app.command()
def version(
    ctx: typer.Context,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Print the version and exit."""
    version_callback(ctx, True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    get_help: HelpAnnotation = None,
    config: ConfigAnnotation = None,
    verbose: VerbosityAnnotation = None,
    version: VersionAnnotation = None,
) -> None:
    """Manage operating system configuration files based on data in the cloud."""
    ctx.ensure_object(dict)

    if not ctx.invoked_subcommand:  # pragma: no cover
        rich.print(ctx.get_help())


logger.debug('successfully imported %s', __name__)
