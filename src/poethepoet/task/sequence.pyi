from collections.abc import Sequence
from typing import Any, Literal

from poethepoet.config import ConfigPartition
from poethepoet.task.base import PoeTask, TaskContext, TaskSpecFactory

class SequenceTask(PoeTask):
    content: list[str | dict[str, Any]]

    class TaskOptions(PoeTask.TaskOptions):
        ignore_fail: Literal[True, False, 'return_zero', 'return_non_zero']
        default_item_type: str | None
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: list[Any]  # pyright: ignore[reportIncompatibleVariableOverride]
        options: SequenceTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]
        subtasks: Sequence[PoeTask.TaskSpec]
        def __init__(
            self,
            name: str,
            task_def: dict[str, Any],
            factory: TaskSpecFactory,
            source: ConfigPartition,
            parent: PoeTask.TaskSpec | None = None,
        ) -> None: ...

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]
    subtasks: list[PoeTask.TaskSpec]
    def __init__(
        self, spec: TaskSpec, invocation: tuple[str, ...], ctx: TaskContext, capture_stdout: bool = False
    ) -> None: ...
