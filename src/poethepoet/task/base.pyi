from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, NamedTuple

from typing_extensions import Self

from poethepoet.config import ConfigPartition as ConfigPartition
from poethepoet.config import PoeConfig as PoeConfig
from poethepoet.context import RunContext as RunContext
from poethepoet.env.manager import EnvVarsManager as EnvVarsManager
from poethepoet.exceptions import ConfigValidationError as ConfigValidationError
from poethepoet.exceptions import PoeException as PoeException
from poethepoet.options import PoeOptions as PoeOptions
from poethepoet.task.args import PoeTaskArgs as PoeTaskArgs
from poethepoet.ui import PoeUi as PoeUi

class MetaPoeTask(type):
    def __init__(cls, *args: Any) -> None: ...

TaskContent = str | Sequence[str | Mapping[str, Any]]
TaskDef = str | Mapping[str, Any] | Sequence[str | Mapping[str, Any]]

class TaskSpecFactory:
    config: PoeConfig
    def __init__(self, config: PoeConfig) -> None: ...
    def __contains__(self, other: object) -> bool: ...
    def get(
        self,
        task_name: str,
        task_def: TaskDef | None = None,
        task_type: str | None = None,
        parent: PoeTask.TaskSpec | None = None,
    ) -> PoeTask.TaskSpec: ...
    def create(
        self,
        task_name: str,
        task_type: str,
        task_def: TaskDef,
        source: ConfigPartition,
        parent: PoeTask.TaskSpec | None = None,
    ) -> PoeTask.TaskSpec: ...
    def load_all(self) -> list[PoeTask.TaskSpec]: ...
    def load(self, task_name: str) -> PoeTask.TaskSpec: ...
    def __iter__(self) -> Iterator[PoeTask.TaskSpec]: ...

class TaskContext(NamedTuple):
    config: PoeConfig
    cwd: str
    ui: PoeUi
    specs: TaskSpecFactory
    @classmethod
    def from_task(cls, parent_task: PoeTask) -> Self: ...

class PoeTask(metaclass=MetaPoeTask):
    __key__: ClassVar[str]
    __content_type__: ClassVar[type]
    class TaskOptions(PoeOptions):
        args: dict[str, Any] | list[Any] | None
        capture_stdout: str | None
        cwd: str | None
        deps: Sequence[str] | None
        env: dict[str, Any] | None
        envfile: str | list[str] | None
        executor: dict[str, Any] | None
        help: str | None
        uses: dict[str, Any] | None
        def validate(self) -> None: ...

    class TaskSpec:
        name: str
        content: TaskContent
        options: PoeTask.TaskOptions
        task_type: type[PoeTask]
        source: ConfigPartition
        def validate(self, config: PoeConfig, task_specs: TaskSpecFactory) -> None: ...
        def create_task(
            self, invocation: tuple[str, ...], ctx: TaskContext, capture_stdout: str | bool = False
        ) -> PoeTask: ...

    parent: PoeTask.TaskSpec | None
    def __init__(
        self,
        name: str,
        task_def: dict[str, Any],
        factory: TaskSpecFactory,
        source: ConfigPartition,
        parent: PoeTask.TaskSpec | None = None,
    ) -> None: ...
    def get_task_env(
        self, parent_env: EnvVarsManager, uses_values: Mapping[str, str] | None = None
    ) -> EnvVarsManager: ...
    @property
    def args(self) -> PoeTaskArgs | None: ...
    def create_task(
        self, invocation: tuple[str, ...], ctx: TaskContext, capture_stdout: str | bool = False
    ) -> PoeTask: ...
    def validate(self, config: PoeConfig, task_specs: TaskSpecFactory) -> None: ...
    spec: TaskSpec
    ctx: TaskContext
    invocation: Any
    capture_stdout: Any
    @property
    def name(self) -> str: ...
    @classmethod
    def lookup_task_spec_cls(cls, task_key: str) -> type[TaskSpec]: ...
    @classmethod
    def resolve_task_type(cls, task_def: TaskDef, config: PoeConfig, array_item: bool | str = False) -> str | None: ...
    def get_parsed_arguments(self, env: EnvVarsManager) -> tuple[dict[str, str], tuple[str, ...]]: ...
    def run(self, context: RunContext, parent_env: EnvVarsManager | None = None) -> int: ...
    def get_working_dir(self, env: EnvVarsManager) -> Path: ...
    def iter_upstream_tasks(self, context: RunContext) -> Iterator[tuple[str, PoeTask]]: ...
    def has_deps(self) -> bool: ...
    @classmethod
    def is_task_type(cls, task_def_key: str, content_type: type | None = None) -> bool: ...
    @classmethod
    def get_task_types(cls, content_type: type | None = None) -> tuple[str, ...]: ...
    class Error(Exception): ...
