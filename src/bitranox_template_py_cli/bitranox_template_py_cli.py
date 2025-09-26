"""Legacy aggregation module kept for import compatibility.

Purpose
-------
Historically this file hosted the greeting and intentional failure helpers. The
behaviors now live in :mod:`bitranox_template_py_cli.behaviors`. Retaining this
module lets existing imports keep working while clarifying where the
single-responsibility implementations reside.

System Role
-----------
Acts as an adapter that re-exports the behavior helpers so that documentation,
CLI code, and third-party consumers can upgrade incrementally without breaking
imports. New code should depend on :mod:`bitranox_template_py_cli.behaviors`
when possible.
"""

from __future__ import annotations

from .behaviors import (
    CANONICAL_GREETING,
    emit_greeting,
    hello_world,
    i_should_fail,
    main,
    noop_main,
    raise_intentional_failure,
)

__all__ = [
    "CANONICAL_GREETING",
    "emit_greeting",
    "hello_world",
    "i_should_fail",
    "main",
    "noop_main",
    "raise_intentional_failure",
]
