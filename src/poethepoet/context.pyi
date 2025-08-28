from collections.abc import Mapping
from pathlib import Path
from typing import Any

from poethepoet.config import PoeConfig as PoeConfig
from poethepoet.env.manager import EnvVarsManager as EnvVarsManager
from poethepoet.executor import PoeExecutor as PoeExecutor
from poethepoet.ui import PoeUi as PoeUi

class RunContext:
    config: PoeConfig
    ui: PoeUi
    env: EnvVarsManager
    dry: bool
    poe_active: str | None
    project_dir: Path
    multistage: bool
    exec_cache: dict[str, Any]
    captured_stdout: dict[tuple[str, ...], str]
    def __init__(
        self,
        config: PoeConfig,
        ui: PoeUi,
        env: Mapping[str, str],
        dry: bool,
        poe_active: str | None,
        multistage: bool = False,
        cwd: Path | str | None = None,
    ) -> None: ...
    def save_task_output(self, invocation: tuple[str, ...], captured_stdout: bytes) -> None: ...
    def get_task_output(self, invocation: tuple[str, ...]) -> str | None: ...
    def get_executor(
        self,
        invocation: tuple[str, ...],
        env: EnvVarsManager,
        working_dir: Path,
        *,
        executor_config: Mapping[str, str] | None = None,
        capture_stdout: str | bool = False,
        delegate_dry_run: bool = False,
    ) -> PoeExecutor: ...
