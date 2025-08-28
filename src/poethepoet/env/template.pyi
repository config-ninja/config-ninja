from collections.abc import Iterable, Mapping
from typing import Callable, TypeVar

KT = TypeVar('KT')
VT = TypeVar('VT')

class SpyDict(dict[KT, VT]):
    def __init__(
        self, content: Iterable[tuple[KT, VT]] = ..., *, getitem_spy: Callable[[dict[KT, VT], KT, VT], VT] | None = None
    ) -> None: ...
    def __getitem__(self, key: KT) -> VT: ...
    def get(self, key: KT, default: VT | None = None) -> VT: ...  # type: ignore[override]

def apply_envvars_to_template(content: str, env: Mapping[str, str], require_braces: bool = False) -> str: ...
