from poethepoet.task.base import PoeTask

class CmdTask(PoeTask):
    class TaskOptions(PoeTask.TaskOptions):
        use_exec: bool
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: str  # pyright: ignore[reportIncompatibleVariableOverride]
        options: CmdTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]
