"""CLI entry point and execution wrapper.

Provides the main entry point used by console scripts and ``python -m``
execution, ensuring consistent error handling and traceback restoration.

Contents:
    * :func:`main` - Primary entry point for CLI execution.
"""

from __future__ import annotations

from collections.abc import Sequence

import lib_cli_exit_tools
import lib_log_rich.runtime

from bitranox_template_py_cli import __init__conf__

from .constants import TRACEBACK_SUMMARY_LIMIT, TRACEBACK_VERBOSE_LIMIT
from .traceback import (
    apply_traceback_preferences,
    restore_traceback_state,
    snapshot_traceback_state,
)


def _run_cli(argv: Sequence[str] | None) -> int:
    """Execute the CLI via lib_cli_exit_tools with exception handling.

    Args:
        argv: Optional sequence of CLI arguments. None uses sys.argv.

    Returns:
        Exit code produced by the command.
    """
    from .root import cli

    try:
        return lib_cli_exit_tools.run_cli(
            cli,
            argv=list(argv) if argv is not None else None,
            prog_name=__init__conf__.shell_command,
        )
    except BaseException as exc:
        tracebacks_enabled = bool(getattr(lib_cli_exit_tools.config, "traceback", False))
        apply_traceback_preferences(tracebacks_enabled)
        length_limit = TRACEBACK_VERBOSE_LIMIT if tracebacks_enabled else TRACEBACK_SUMMARY_LIMIT
        lib_cli_exit_tools.print_exception_message(trace_back=tracebacks_enabled, length_limit=length_limit)
        return lib_cli_exit_tools.get_system_exit_code(exc)


def main(argv: Sequence[str] | None = None, *, restore_traceback: bool = True) -> int:
    """Execute the CLI with error handling and return the exit code.

    Provides the single entry point used by console scripts and
    ``python -m`` execution so that behaviour stays identical across transports.

    Args:
        argv: Optional sequence of CLI arguments. None uses sys.argv.
        restore_traceback: Whether to restore prior traceback configuration after execution.

    Returns:
        Exit code reported by the CLI run.

    Example:
        >>> exit_code = main(["--help"])  # doctest: +SKIP
        >>> exit_code == 0  # doctest: +SKIP
        True
    """
    previous_state = snapshot_traceback_state()
    try:
        return _run_cli(argv)
    finally:
        if restore_traceback:
            restore_traceback_state(previous_state)
        if lib_log_rich.runtime.is_initialised():
            lib_log_rich.runtime.shutdown()


__all__ = ["main"]
