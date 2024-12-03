"""Type stubs for the `sh` package."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

# pylint: disable=unused-argument

__all__ = ['ErrorReturnCode', 'contrib', 'mkdir', 'systemctl']

class Contrib:
    """Interface for the `sh.contrib` module."""

    @property
    @contextmanager
    def sudo(self) -> Iterator[None]:
        """Run the wrapped code as root."""

class ErrorReturnCode(Exception):  # noqa: N818
    """Base class for all exceptions as a result of a command's exit status being deemed an error.

    This base class is dynamically subclassed into derived classes with the format:
    `ErrorReturnCode_NNN`, where `NNN` is the exit code number. The reason for this is it reduces
    boiler plate code when testing error return codes:

    ```py
    try:
        some_cmd()
    except ErrorReturnCode_12:
        print("couldn't do X")
    ```

    vs:

    ```py
    try:
        some_cmd()
    except ErrorReturnCode as e:
        if e.exit_code == 12:
            print("couldn't do X")
    ```

    It's not much of a savings, but i believe it makes the code easier to read.
    """

    stderr: bytes

class CommandNotFound(AttributeError):  # noqa: N818
    """Raised when a command is not found on the system."""

class SystemCtl:
    """Interface for the `systemctl` command."""

    def __call__(self, *args: str) -> str: ...
    def disable(self, *args: str) -> str:
        """Disables one or more units.

        This removes all symlinks to the unit files backing the specified units from the unit
        configuration directory, and hence undoes any changes made by enable or link. Note that this
        removes all symlinks to matching unit files, including manually created symlinks, and not
        just those actually created by enable or link. Note that while disable undoes the effect of
        enable, the two commands are otherwise not symmetric, as disable may remove more symlinks
        than a prior enable invocation of the same unit created.
        """

    def start(self, *args: str) -> str:
        """Start (activate) one or more units specified on the command line."""

    def status(self, *args: str) -> str:
        """Show terse runtime status information about one or more units, followed by most recent log data from the journal."""

contrib = Contrib()
systemctl = SystemCtl()

def config_ninja(*args: str, _tty_size: tuple[int, int] = ...) -> str:
    """Run the `config-ninja` command."""

def mkdir(*args: str) -> str:
    """Make directories."""

def rm(*args: str) -> str:
    """Remove files or directories."""

def tee(*args: str, _in: str | None = None, _out: str | None = None) -> str:
    """Read from standard input and write to standard output and files."""
