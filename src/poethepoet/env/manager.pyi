from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from poethepoet.config import PoeConfig as PoeConfig
from poethepoet.env.cache import EnvFileCache as EnvFileCache
from poethepoet.env.template import apply_envvars_to_template as apply_envvars_to_template
from poethepoet.ui import PoeUi as PoeUi

class EnvVarsManager(Mapping[str, str]):
    envfiles: EnvFileCache
    cwd: str
    def __init__(
        self,
        config: PoeConfig,
        ui: PoeUi | None,
        parent_env: EnvVarsManager | None = None,
        base_env: Mapping[str, str] | None = None,
        cwd: Path | str | None = None,
    ) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __iter__(self) -> Iterator[str]: ...
    def __len__(self) -> int: ...
    def get(self, key: Any, /, default: Any = None) -> str | None: ...  # type: ignore[override]
    def set(self, key: str, value: str) -> None: ...
    def apply_env_config(
        self,
        envfile: str | list[str] | None,
        config_env: Mapping[str, str | Mapping[str, str]] | None,
        config_dir: Path,
        config_working_dir: Path,
    ) -> None: ...
    def update(self, env_vars: Mapping[str, Any]) -> EnvVarsManager: ...
    def clone(self) -> EnvVarsManager: ...
    def to_dict(self) -> dict[str, str]: ...
    def fill_template(self, template: str) -> str: ...
