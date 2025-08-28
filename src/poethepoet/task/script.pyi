from typing import Any

from poethepoet.helpers.python import FunctionCall
from poethepoet.task.base import PoeTask

class ScriptTask(PoeTask):
    content: str
    class TaskOptions(PoeTask.TaskOptions):
        use_exec: bool
        print_result: bool
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: str  # pyright: ignore[reportIncompatibleVariableOverride]
        options: ScriptTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]
    def parse_content(self, args: dict[str, Any] | None) -> tuple[str, FunctionCall]: ...
