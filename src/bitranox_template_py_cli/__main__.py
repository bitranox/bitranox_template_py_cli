"""Module entry point for ``python -m bitranox_template_py_cli``.

Delegates to :func:`adapters.cli.main` so that module execution mirrors the
installed console script exactly, including traceback handling, exit-code
mapping, and logging shutdown.

System Role:
    Thin shim bridging CPython's ``-m`` invocation to the shared CLI entry point.
    Wires production services from composition layer.
"""

from __future__ import annotations

from .adapters.cli.main import main
from .composition import build_production

if __name__ == "__main__":
    raise SystemExit(main(services_factory=build_production))
