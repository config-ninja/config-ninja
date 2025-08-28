from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

from poethepoet.context import RunContext as RunContext
from poethepoet.env.manager import EnvVarsManager as EnvVarsManager
from poethepoet.exceptions import ConfigValidationError as ConfigValidationError
from poethepoet.exceptions import ExecutionError as ExecutionError
from poethepoet.exceptions import PoeException as PoeException

POE_DEBUG: bool

class MetaPoeExecutor(type):
    def __init__(cls, *args: object) -> None: ...

class PoeExecutor(metaclass=MetaPoeExecutor):
    working_dir: Path | None
    __key__: ClassVar[str | None]
    invocation: tuple[str, ...]
    context: RunContext
    options: Mapping[str, str]
    env: EnvVarsManager
    capture_stdout: bool | str
    dry: bool
    def __init__(
        self,
        invocation: tuple[str, ...],
        context: RunContext,
        options: Mapping[str, str],
        env: EnvVarsManager,
        working_dir: Path | None = None,
        capture_stdout: str | bool = False,
        dry: bool = False,
    ) -> None: ...
    @classmethod
    def works_with_context(cls, context: RunContext) -> bool: ...
    @classmethod
    def get(
        cls,
        invocation: tuple[str, ...],
        context: RunContext,
        executor_config: Mapping[str, str],
        env: EnvVarsManager,
        working_dir: Path | None = None,
        capture_stdout: str | bool = False,
        dry: bool = False,
    ) -> PoeExecutor: ...
    def execute(self, cmd: Sequence[str], input: bytes | None = None, use_exec: bool = False) -> int: ...
    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> None: ...
    @classmethod
    def validate_executor_config(cls, config: dict[str, Any]) -> None: ...
