"""Define the project's CLI.

Note: Typer currently does not support future annotations.
"""
import contextlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Dict, Iterator, Optional, Tuple, Type

import jinja2
import pyspry
import typer
import yaml
from rich import print

import config_ninja
from config_ninja.backend import Backend, FormatT, dumps, loads
from config_ninja.contrib import get_backend

logger = logging.getLogger(__name__)

app_kwargs: Dict[str, Any] = {
    'context_settings': {'help_option_names': ['-h', '--help']},
    'no_args_is_help': True,
    'rich_markup_mode': 'rich',
}

app = typer.Typer(**app_kwargs)
self_app = typer.Typer(**app_kwargs)

app.add_typer(
    self_app, name='self', help="Operate on [bold blue]config-ninja[/]'s own configuration file."
)

KeyAnnotation = Annotated[
    str,
    typer.Argument(help='The key of the configuration object to retrieve', show_default=False),
]

PollAnnotation = Annotated[
    Optional[bool],
    typer.Option(
        '-p',
        '--poll',
        help='Enable polling; print the configuration on changes.',
        show_default=False,
    ),
]


@dataclass
class DestSpec:
    """Container for the destination spec parsed from settings."""

    path: Path
    output: Optional[FormatT] = None
    template: Optional[jinja2.Template] = None


@contextlib.contextmanager
def handle_key_errors(objects: Dict[str, Any]) -> Iterator[None]:
    """Handle KeyError exceptions within the managed context."""
    try:
        yield
    except KeyError as exc:  # pragma: no cover
        print(f'[red]ERROR[/]: Missing key: [green]{exc.args[0]}[/]\n')
        print(yaml.dump(objects))
        typer.Exit(1)


def version_callback(ctx: typer.Context, value: Optional[bool] = None) -> None:
    """Print the version of the package."""
    if ctx.resilient_parsing:  # pragma: no cover  # this is for tab completions
        return

    if value:
        print(config_ninja.__version__)
        typer.Exit()


def init_backend(settings: Optional[pyspry.Settings], key: str) -> Tuple[FormatT, Backend]:
    """Get the backend for the specified configuration object."""
    if not settings:  # pragma: no cover
        print('[red]ERROR[/]: Could not load settings.')
        typer.Exit(1)

    objects = settings.OBJECTS  # type: ignore[union-attr]

    with handle_key_errors(objects):
        source = objects[key]['source']
        backend_class: Type[Backend] = get_backend(source['backend'])
        fmt = source.get('format', 'raw')
        if 'new' in source:
            backend = backend_class.new(**source['new']['kwargs'])
        else:
            backend = backend_class(**source['init']['kwargs'])

    return fmt, backend


def get_dest(settings: pyspry.Settings, key: str) -> DestSpec:
    """Read the destination spec from the settings file."""
    objects = settings.OBJECTS
    with handle_key_errors(objects):
        dest = objects[key]['dest']
        path = Path(dest['path'])
        try:
            template_path = Path(dest.get('template'))
        except TypeError:
            return DestSpec(output=dest['output'], path=path)

        if output := dest.get('output'):
            print(
                f"[yellow]WARNING[/]: Ignoring output format '{output}'; "
                f"using 'template={template_path!s}' instead"
            )
        loader = jinja2.FileSystemLoader(template_path.parent)
        env = jinja2.Environment(autoescape=jinja2.select_autoescape(default=True), loader=loader)

        return DestSpec(path=path, template=env.get_template(template_path.name))


@app.command(name='get', help='Print the value of the specified configuration object.')
def print_obj_config(ctx: typer.Context, key: KeyAnnotation, poll: PollAnnotation = False) -> None:
    """Print the value of the specified configuration object."""
    _, backend = init_backend(ctx.obj['settings'], key)

    if poll:
        for content in backend.poll():
            print(content)
    else:
        print(backend.get())


@app.command()
def apply(ctx: typer.Context, key: KeyAnnotation, poll: PollAnnotation = False) -> None:
    """Apply the specified configuration to the system."""
    fmt, backend = init_backend(ctx.obj['settings'], key)
    dest = get_dest(ctx.obj['settings'], key)
    dest.path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)

    if poll:
        for content in backend.poll():
            data = loads(fmt, content)
            if dest.template:
                dest.path.write_text(dest.template.render(data))
            else:
                assert dest.output is not None  # noqa: S101  # 👈 for static analysis
                dest.path.write_text(dumps(dest.output, data))
    else:
        data = loads(fmt, backend.get())
        if dest.template:
            dest.path.write_text(dest.template.render(data))
        else:
            assert dest.output is not None  # noqa: S101  # 👈 for static analysis
            dest.path.write_text(dumps(dest.output, data))


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
