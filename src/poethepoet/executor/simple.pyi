from poethepoet.executor.base import PoeExecutor as PoeExecutor

class SimpleExecutor(PoeExecutor):
    __options__: dict[str, type]
