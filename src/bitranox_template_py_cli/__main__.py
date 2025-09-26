"""Module entry point ensuring SystemExit semantics match project standards.

Purpose
-------
Provide the ``python -m bitranox_template_py_cli`` path mandated by the
project's packaging guidelines. The wrapper delegates to
:func:`bitranox_template_py_cli.cli.main` so that module execution mirrors the
installed console script, including traceback handling and exit-code mapping.

System Role
-----------
Lives in the adapters layer. It bridges CPython's module execution entry point
to the shared CLI helper while preserving the previous traceback preference as
captured in ``docs/systemdesign/module_reference.md``.
"""

from __future__ import annotations

from typing import Final

import lib_cli_exit_tools

from . import cli

# Match the CLI defaults so truncation behaviour stays consistent across entry
# points regardless of whether users call the console script or ``python -m``.
TRACEBACK_SUMMARY_LIMIT: Final[int] = cli.TRACEBACK_SUMMARY_LIMIT
TRACEBACK_VERBOSE_LIMIT: Final[int] = cli.TRACEBACK_VERBOSE_LIMIT


def _module_main() -> int:
    """Execute the CLI entry point and return a normalised exit code.

    Returns
    -------
    int
        Exit code derived from the CLI run.

    Examples
    --------
    >>> from unittest.mock import patch
    >>> with patch("bitranox_template_py_cli.cli.main", return_value=0):
    ...     _module_main()
    0
    """

    previous = cli.snapshot_traceback_state()
    try:
        try:
            return int(
                cli.main(
                    restore_traceback=False,
                    summary_limit=TRACEBACK_SUMMARY_LIMIT,
                    verbose_limit=TRACEBACK_VERBOSE_LIMIT,
                )
            )
        except BaseException as exc:  # noqa: BLE001 - keep parity with console script
            traceback_enabled = bool(getattr(lib_cli_exit_tools.config, "traceback", False))
            cli.apply_traceback_preferences(traceback_enabled)
            limit = TRACEBACK_VERBOSE_LIMIT if traceback_enabled else TRACEBACK_SUMMARY_LIMIT
            lib_cli_exit_tools.print_exception_message(
                trace_back=traceback_enabled,
                length_limit=limit,
            )
            return lib_cli_exit_tools.get_system_exit_code(exc)
    finally:
        cli.restore_traceback_state(previous)


if __name__ == "__main__":
    raise SystemExit(_module_main())
