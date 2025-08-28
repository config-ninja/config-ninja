from collections.abc import Sequence
from typing import Any

from poethepoet.context import RunContext as RunContext
from poethepoet.exceptions import ConfigValidationError as ConfigValidationError
from poethepoet.exceptions import ExecutionError as ExecutionError
from poethepoet.executor.base import PoeExecutor as PoeExecutor
from poethepoet.virtualenv import Virtualenv as Virtualenv

class VirtualenvExecutor(PoeExecutor):
    __options__: dict[str, type]
    @classmethod
    def works_with_context(cls, context: RunContext) -> bool: ...
    def execute(self, cmd: Sequence[str], input: bytes | None = None, use_exec: bool = False) -> int: ...
    @classmethod
    def validate_executor_config(cls, config: dict[str, Any]) -> None: ...
