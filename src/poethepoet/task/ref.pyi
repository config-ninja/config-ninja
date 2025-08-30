from poethepoet.task.base import PoeTask

class RefTask(PoeTask):
    class TaskOptions(PoeTask.TaskOptions):
        def validate(self) -> None: ...

    class TaskSpec(PoeTask.TaskSpec):
        content: str  # pyright: ignore[reportIncompatibleVariableOverride]
        options: RefTask.TaskOptions  # pyright: ignore[reportIncompatibleVariableOverride]

    spec: TaskSpec  # pyright: ignore[reportIncompatibleVariableOverride]
