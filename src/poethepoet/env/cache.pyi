from pathlib import Path

from poethepoet.exceptions import ExecutionError as ExecutionError
from poethepoet.ui import PoeUi as PoeUi

POE_DEBUG: bool

class EnvFileCache:
    def __init__(self, project_dir: Path, ui: PoeUi | None) -> None: ...
    def get(self, envfile: str | Path) -> dict[str, str]: ...
