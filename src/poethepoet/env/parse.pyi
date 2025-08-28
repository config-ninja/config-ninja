from collections.abc import Iterable, Sequence
from enum import Enum

class ParseError(ValueError):
    def __init__(self, issue: str, offset: int, lines: Iterable[str]) -> None: ...

class ParserState(Enum):
    SCAN_VAR_NAME = 0
    SCAN_VALUE = 1
    IN_SINGLE_QUOTE = 2
    IN_DOUBLE_QUOTE = 3

VARNAME_PATTERN: str
ASSIGNMENT_PATTERN: str
COMMENT_SUFFIX_PATTERN: str
WHITESPACE_PATTERN: str
UNQUOTED_VALUE_PATTERN: str
SINGLE_QUOTE_VALUE_PATTERN: str
DOUBLE_QUOTE_VALUE_PATTERN: str

def parse_env_file(content_lines: Sequence[str]) -> dict[str, str]: ...
