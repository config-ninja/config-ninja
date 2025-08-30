from collections.abc import Sequence

from poethepoet.context import RunContext as RunContext
from poethepoet.exceptions import ExecutionError as ExecutionError
from poethepoet.executor.base import PoeExecutor as PoeExecutor

class PoetryExecutor(PoeExecutor):
    __options__: dict[str, type]
    @classmethod
    def works_with_context(cls, context: RunContext) -> bool: ...
    def execute(self, cmd: Sequence[str], input: bytes | None = None, use_exec: bool = False) -> int: ...
