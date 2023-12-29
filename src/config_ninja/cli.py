"""Define the project's CLI.

Note: Typer currently does not support future annotations.
"""
import contextlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Dict, Iterator, Optional, Type

import typer
import yaml
from rich import print

import config_ninja
from config_ninja.backend import AbstractBackend
from config_ninja.contrib import get_backend

if TYPE_CHECKING:  # pragma: no cover
    import pyspry

app_kwargs: Dict[str, Any] = dict(
    context_settings={'help_option_names': ['-h', '--help']},
    no_args_is_help=True,
    rich_markup_mode='rich',
)

app = typer.Typer(**app_kwargs)
self_app = typer.Typer(**app_kwargs)

app.add_typer(
    self_app, name='self', help="Operate on [bold blue]config-ninja[/]'s own configuration file."
)

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def handle_key_errors(objects: Dict[str, Any]) -> Iterator[None]:
    """Handle KeyError exceptions within the managed context."""
    try:
        yield
    except KeyError as exc:  # pragma: no cover
        print(f'[red]ERROR[/]: Invalid key: [green]{exc.args[0]}[/]\n')
        print(yaml.dump(objects))
        typer.Exit(1)


def version_callback(ctx: typer.Context, value: Optional[bool] = None) -> None:
    """Print the version of the package."""
    if ctx.resilient_parsing:  # pragma: no cover  # this is for tab completions
        return

    if value:
        print(config_ninja.__version__)
        typer.Exit()


@app.command(name='get', help='Get the value of a configuration object.')
def print_obj_config(
    ctx: typer.Context,
    key: Annotated[str, typer.Argument(help='The key of the configuration object to retrieve')],
) -> None:
    """Print the value of the specified configuration object."""
    settings: pyspry.Settings = ctx.obj['settings']
    if not settings:  # pragma: no cover
        print('[red]ERROR[/]: Could not load settings.')
        typer.Exit(1)

    objects = settings.OBJECTS
    with handle_key_errors(objects):
        source = objects[key]['source']
        backend_class: Type[AbstractBackend] = get_backend(source['backend'])
        if 'new' in source:
            backend = backend_class.new(**source['new']['kwargs'])
        else:
            backend = backend_class(**source['init']['kwargs'])

    print(backend.get_raw())


@app.command(name='poll')
def poll_obj_config(
    ctx: typer.Context,
    key: Annotated[str, typer.Argument(help='The key of the configuration object to retrieve')],
) -> None:
    """Poll for changes to a configuration object.

    Each time the configuration changes, print the new value to stdout.
    """
    settings: pyspry.Settings = ctx.obj['settings']
    if not settings:  # pragma: no cover
        print('[red]ERROR[/]: Could not load settings.')
        typer.Exit(1)

    objects = settings.OBJECTS
    with handle_key_errors(objects):
        source = objects[key]['source']
        backend_class: Type[AbstractBackend] = get_backend(source['backend'])
        if 'new' in source:
            backend = backend_class.new(**source['new']['kwargs'])
        else:
            backend = backend_class(**source['init']['kwargs'])

    for content in backend.poll():
        print(content)


@self_app.command(name='print')
def print_self_config(ctx: typer.Context) -> None:
    """Print the configuration file."""
    if settings := ctx.obj['settings']:
        print(yaml.dump(settings.OBJECTS))
    else:
        print('[yellow]WARNING[/]: No settings file found.')


@app.command()
def version(ctx: typer.Context) -> None:
    """Print the version and exit."""
    version_callback(ctx, True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    settings_file: Annotated[
        Optional[Path],
        typer.Option(
            '-c',
            '--config',
            help="Path to [bold blue]config-ninja[/]'s own configuration file.",
            show_default=False,
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            '-v',
            '--version',
            callback=version_callback,
            show_default=False,
            is_eager=True,
            help='Print the version and exit.',
        ),
    ] = None,
) -> None:
    """Manage system configuration files in the cloud."""
    ctx.ensure_object(dict)

    try:
        settings_file = settings_file or config_ninja.resolve_settings_path()
    except FileNotFoundError as exc:
        message = "[yellow]WARNING[/]: Could not find [bold blue]config-ninja[/]'s settings file"
        if len(exc.args) > 1:
            message += ' at any of the following locations:\n' + '\n'.join(
                f'    {p}' for p in exc.args[1]
            )
        print(message)
        ctx.obj['settings'] = None

    else:
        ctx.obj['settings'] = config_ninja.load_settings(settings_file)

    if not ctx.invoked_subcommand:  # pragma: no cover
        print(ctx.get_help())


logger.debug('successfully imported %s', __name__)
