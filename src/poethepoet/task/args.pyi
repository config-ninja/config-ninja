from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from poethepoet.env.manager import EnvVarsManager
from poethepoet.options import PoeOptions

ArgParams = dict[str, Any]
ArgsDef = list[str] | list[ArgParams] | dict[str, ArgParams]
arg_param_schema: dict[str, type | tuple[type, ...]]
arg_types: dict[str, type]

class ArgSpec(PoeOptions):
    default: str | int | float | bool | None
    help: str
    name: str
    options: list[Any] | tuple[Any, ...]
    positional: bool | str
    required: bool
    type: Literal['string', 'float', 'integer', 'boolean']
    multiple: bool | int
    @classmethod
    def parse(
        cls, source: Mapping[str, Any] | list[Any], strict: bool = True, extra_keys: Sequence[str] = ...
    ) -> None: ...
    def validate(self) -> None: ...

class PoeTaskArgs:
    def __init__(self, args_def: ArgsDef, task_name: str) -> None: ...
    @classmethod
    def get_help_content(cls, args_def: ArgsDef | None) -> list[tuple[tuple[str, ...], str, str]]: ...
    def build_parser(self, env: EnvVarsManager, program_name: str) -> ArgumentParser: ...
    def parse(
        self, args: Sequence[str], env: EnvVarsManager, program_name: str
    ) -> tuple[dict[str, str], tuple[str, ...]]: ...
