"""Public package surface exposing the stable greeting, failure, and metadata hooks.

The module re-exports the behaviour helpers maintained in
:mod:`bitranox_template_py_cli.behaviors` so both library consumers and CLI
transports rely on the same single source of truth.
"""

from __future__ import annotations

from .behaviors import (
    CANONICAL_GREETING,
    emit_greeting,
    hello_world,
    i_should_fail,
    noop_main,
    raise_intentional_failure,
)
from .__init__conf__ import print_info

__all__ = [
    "CANONICAL_GREETING",
    "emit_greeting",
    "hello_world",
    "i_should_fail",
    "noop_main",
    "print_info",
    "raise_intentional_failure",
]
