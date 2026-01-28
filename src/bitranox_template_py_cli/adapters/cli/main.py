"""CLI entry point and execution wrapper.

Provides the main entry point used by console scripts and ``python -m``
execution, ensuring consistent error handling and traceback restoration.

Contents:
    * :func:`main` - Primary entry point for CLI execution.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import lib_cli_exit_tools
import lib_log_rich.runtime

from bitranox_template_py_cli import __init__conf__

from .constants import TRACEBACK_SUMMARY_LIMIT, TRACEBACK_VERBOSE_LIMIT
from .context import (
    apply_traceback_preferences,
    restore_traceback_state,
    snapshot_traceback_state,
)

if TYPE_CHECKING:
    from bitranox_template_py_cli.composition import AppServices

# Module-level service factory container (list to avoid global statement).
# Set by main() before CLI runs, accessed by get_services_factory().
_services_factory_holder: list[Callable[[], AppServices]] = []


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


def get_services_factory() -> Callable[[], AppServices]:
    """Return the current services factory.

    Returns:
        The services factory set by main().

    Raises:
        RuntimeError: If no factory has been set (should not happen in normal use).
    """
    if not _services_factory_holder:
        raise RuntimeError("Services factory not initialized. Call main() first.")
    return _services_factory_holder[0]


def set_services_factory_for_testing(factory: Callable[[], AppServices] | None) -> None:
    """Set or clear the services factory for testing.

    This function allows tests to inject a services factory without going
    through main(). Pass None to clear the factory.

    Args:
        factory: Services factory to set, or None to clear.

    Note:
        This is intended for test use only. Production code should use main().
    """
    _services_factory_holder.clear()
    if factory is not None:
        _services_factory_holder.append(factory)


def main(
    argv: Sequence[str] | None = None,
    *,
    restore_traceback: bool = True,
    services_factory: Callable[[], AppServices] | None = None,
) -> int:
    """Execute the CLI with error handling and return the exit code.

    Provides the single entry point used by console scripts and
    ``python -m`` execution so that behaviour stays identical across transports.

    Args:
        argv: Optional sequence of CLI arguments. None uses sys.argv.
        restore_traceback: Whether to restore prior traceback configuration after execution.
        services_factory: Factory function returning AppServices. Required.
            Callers outside the adapters layer should pass ``build_production``.

    Returns:
        Exit code reported by the CLI run.

    Raises:
        ValueError: If services_factory is not provided.

    Example:
        >>> from bitranox_template_py_cli.composition import build_production
        >>> exit_code = main(["--help"], services_factory=build_production)  # doctest: +SKIP
        >>> exit_code == 0  # doctest: +SKIP
        True
    """
    if services_factory is None:
        raise ValueError("services_factory is required. Pass build_production from composition layer.")

    _services_factory_holder.clear()
    _services_factory_holder.append(services_factory)

    previous_state = snapshot_traceback_state()
    try:
        return _run_cli(argv)
    finally:
        if restore_traceback:
            restore_traceback_state(previous_state)
        if lib_log_rich.runtime.is_initialised():
            lib_log_rich.runtime.shutdown()


__all__ = ["get_services_factory", "main", "set_services_factory_for_testing"]
