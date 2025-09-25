"""Public package surface exposing the stable greeting, failure, and metadata hooks.

The project intentionally keeps the runtime surface area tiny while the richer
logging utilities are designed. Exporting :func:`hello_world`, :func:`i_should_fail`,
and :func:`print_info` here allows both ``import bitranox_template_py_cli`` and
``python -m bitranox_template_py_cli`` flows to exercise the documented functions
referenced in ``docs/systemdesign/module_reference.md``.
"""

from __future__ import annotations

from .bitranox_template_py_cli import hello_world, i_should_fail
from .__init__conf__ import print_info

__all__ = ["hello_world", "i_should_fail", "print_info"]
