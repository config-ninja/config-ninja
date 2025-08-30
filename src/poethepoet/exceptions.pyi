from typing import Any

class PoeException(RuntimeError):
    cause: str | None
    msg: Any
    args: Any
    def __init__(self, msg: str, *args: Any) -> None: ...

class CyclicDependencyError(PoeException): ...
class ExpressionParseError(PoeException): ...

class ConfigValidationError(PoeException):
    context: str | None
    task_name: str | None
    index: int | None
    global_option: str | None
    filename: str | None
    def __init__(
        self,
        msg: str,
        *args: Any,
        context: str | None = None,
        task_name: str | None = None,
        index: int | None = None,
        global_option: str | None = None,
        filename: str | None = None,
    ) -> None: ...

class ExecutionError(RuntimeError):
    cause: str | None
    msg: Any
    args: Any
    def __init__(self, msg: str, *args: Any) -> None: ...

class PoePluginException(PoeException): ...
