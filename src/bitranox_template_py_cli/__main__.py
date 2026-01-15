"""Module entry point ensuring SystemExit semantics match project standards.

Provides the ``python -m bitranox_template_py_cli`` path mandated by the
project's packaging guidelines. The wrapper delegates to
``bitranox_template_py_cli.adapters.cli.main`` so that module execution mirrors the
installed console script, including traceback handling and exit-code mapping.

Note:
    Lives in the composition layer. It bridges CPython's module execution entry
    point to the shared CLI helper.
"""

from .adapters.cli import main


def _module_main() -> int:
    """Execute the CLI entry point and return a normalised exit code.

    Returns:
        Exit code reported by the CLI run.
    """
    return main()


if __name__ == "__main__":
    raise SystemExit(_module_main())
