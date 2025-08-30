from poethepoet.context import RunContext as RunContext
from poethepoet.exceptions import CyclicDependencyError as CyclicDependencyError
from poethepoet.task.base import PoeTask as PoeTask

class TaskExecutionNode:
    task: PoeTask
    direct_dependants: list[TaskExecutionNode]
    direct_dependencies: set[tuple[str, ...]]
    path_dependants: tuple[str, ...]
    capture_stdout: bool
    def __init__(
        self,
        task: PoeTask,
        direct_dependants: list[TaskExecutionNode],
        path_dependants: tuple[str, ...],
        capture_stdout: bool = False,
    ) -> None: ...
    def is_source(self) -> bool: ...
    @property
    def identifier(self) -> tuple[str, ...]: ...

class TaskExecutionGraph:
    sink: TaskExecutionNode
    sources: list[TaskExecutionNode]
    captured_tasks: dict[tuple[str, ...], TaskExecutionNode]
    uncaptured_tasks: dict[tuple[str, ...], TaskExecutionNode]
    def __init__(self, sink_task: PoeTask, context: RunContext) -> None: ...
    def get_execution_plan(self) -> list[list[PoeTask]]: ...
