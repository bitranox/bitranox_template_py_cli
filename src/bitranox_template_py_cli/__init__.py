"""Public package surface exposing the stable greetings helper.

The project intentionally keeps the runtime surface area tiny while the richer
logging utilities are designed. Exporting :func:`hello_world` here allows both
``import bitranox_template_py_cli`` and ``python -m bitranox_template_py_cli``
flows to exercise the same domain function, as documented in
``docs/systemdesign/module_reference.md``.
"""

from __future__ import annotations

from .bitranox_template_py_cli import hello_world

__all__ = ["hello_world"]
