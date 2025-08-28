from collections.abc import Iterable, Sequence
from typing import Any

from poethepoet.env.manager import EnvVarsManager
from poethepoet.task.base import PoeTask

class ExprTask(PoeTask):
    content: str
    class TaskOptions(PoeTask.TaskOptions):
        imports: Sequence[str]
        assert_: bool | int
        use_exec: bool
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: str  # pyright: ignore[reportIncompatibleVariableOverride]
        options: ExprTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]

    def parse_content(
        self, args: dict[str, Any] | None, env: EnvVarsManager, imports: Iterable[str] = ...
    ) -> tuple[str, dict[str, str]]: ...
