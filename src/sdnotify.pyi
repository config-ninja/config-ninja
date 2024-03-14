"""Stub the module `sdnotify`."""

import socket

class SystemdNotifier:
    """This class holds a connection to the systemd notification socket.

    It can be used to send messages to systemd using its notify method.
    """

    debug: bool
    socket: socket.socket

    def __init__(self, debug: bool = False) -> None:
        """Instantiate a new notifier object.

        This will initiate a connection to the systemd notification socket.

        Normally this method silently ignores exceptions (for example, if the systemd notification
        socket is not available) to allow applications to function on non-systemd based systems.
        However, setting debug=True will cause this method to raise any exceptions generated to the
        caller, to aid in debugging.
        """

    def notify(self, state: str) -> None:
        """Send a notification to systemd.

        state is a string; see the man page of sd_notify (http://www.freedesktop.org/software/systemd/man/sd_notify.html)
        for a description of the allowable values.

        Normally this method silently ignores exceptions (for example, if the systemd notification
        socket is not available) to allow applications to function on non-systemd based systems.
        However, setting debug=True will cause this method to raise any exceptions generated to the
        caller, to aid in debugging.
        """
