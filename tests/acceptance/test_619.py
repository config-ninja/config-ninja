"""Define acceptance tests for better logging (#619)."""

from __future__ import annotations

import functools

import pytest

try:
    import sh
except ImportError:
    pytest.skip('the tests in this module require `sh`', allow_module_level=True)


config_ninja = functools.partial(
    sh.config_ninja,
    _tty_size=(20, 1000),  # prevent the tty width from influencing the number of lines in the output
)


def test_output_message_per_config() -> None:
    """Verify that `config-ninja apply` prints a single message for each applied controller."""
    # Arrange
    config_objects = ['example-local', 'example-local-template']

    # Act
    out = config_ninja('apply', *config_objects)

    # Assert
    assert len(config_objects) == len(out.strip().split('\n')), out.strip()
