from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from poethepoet.exceptions import ConfigValidationError as ConfigValidationError
from poethepoet.options import NoValue as NoValue
from poethepoet.options import PoeOptions as PoeOptions

KNOWN_SHELL_INTERPRETERS: tuple[str, ...]

class ConfigPartition:
    options: PoeOptions
    full_config: Mapping[str, Any]
    poe_options: Mapping[str, Any]
    path: Path
    project_dir: Path
    ConfigOptions: type[PoeOptions]
    is_primary: bool
    def __init__(
        self,
        full_config: Mapping[str, Any],
        path: Path,
        project_dir: Path | None = None,
        cwd: Path | None = None,
        strict: bool = True,
    ) -> None: ...
    @property
    def cwd(self) -> Path: ...
    @property
    def config_dir(self) -> Path: ...
    def get(self, key: str, default: Any = ...) -> Any: ...

EmptyDict: Mapping[Any, Any] = ...

class ProjectConfig(ConfigPartition):
    is_primary: bool
    class ConfigOptions(PoeOptions):
        default_task_type: str
        default_array_task_type: str
        default_array_item_task_type: str
        env: Mapping[str, str]
        envfile: str | Sequence[str]
        executor: Mapping[str, str]
        include: Sequence[str]
        poetry_command: str
        poetry_hooks: Mapping[str, str]
        shell_interpreter: str | Sequence[str]
        verbosity: int
        tasks: Mapping[str, Any]

    @classmethod
    def normalize(cls, config: Any, strict: bool = True) -> Any: ...
    def validate(self) -> None: ...
    @classmethod
    def validate_env(cls, env: Mapping[str, str]) -> Any: ...

class IncludedConfig(ConfigPartition):
    class ConfigOptions(PoeOptions):
        env: Mapping[str, str]
        envfile: str | Sequence[str]
        tasks: Mapping[str, Any]
        def validate(self) -> None: ...
