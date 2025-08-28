from typing import Any, ClassVar, Literal

from poethepoet.config import ConfigPartition
from poethepoet.task.base import PoeTask, TaskContext, TaskSpecFactory

DEFAULT_CASE: str
SUBTASK_OPTIONS_BLOCKLIST: tuple[str, ...]

class SwitchTask(PoeTask):
    __content_type__: ClassVar[type]
    class TaskOptions(PoeTask.TaskOptions):
        control: str | dict[str, Any]
        default: Literal['pass', 'fail']

        @classmethod
        def normalize(cls, config: Any, strict: bool = True) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        control_task_spec: PoeTask.TaskSpec
        case_task_specs: tuple[tuple[tuple[Any, ...], PoeTask.TaskSpec], ...]
        def __init__(
            self,
            name: str,
            task_def: dict[str, Any],
            factory: TaskSpecFactory,
            source: ConfigPartition,
            parent: PoeTask.TaskSpec | None = None,
        ) -> None: ...

    control_task: PoeTask
    switch_tasks: dict[str, PoeTask]
    def __init__(
        self, spec: TaskSpec, invocation: tuple[str, ...], ctx: TaskContext, capture_stdout: bool = False
    ) -> None: ...
