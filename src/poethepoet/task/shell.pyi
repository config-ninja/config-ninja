from poethepoet.task.base import PoeTask

class ShellTask(PoeTask):
    content: str
    class TaskOptions(PoeTask.TaskOptions):
        interpreter: str | list[str] | None
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: str  # pyright: ignore[reportIncompatibleVariableOverride]
        options: ShellTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]
    def resolve_interpreter_cmd(self) -> list[str] | None: ...
