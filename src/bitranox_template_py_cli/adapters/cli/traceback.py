"""Traceback state management for CLI error handling.

Provides helpers to synchronize and preserve traceback configuration with
``lib_cli_exit_tools`` so error output remains consistent across invocations.

Contents:
    * :func:`apply_traceback_preferences` - Enable/disable verbose tracebacks.
    * :func:`snapshot_traceback_state` - Capture current traceback config.
    * :func:`restore_traceback_state` - Restore previously captured config.
    * :data:`TracebackState` - Type alias for captured state tuple.
"""

import lib_cli_exit_tools

#: Type alias for traceback configuration state (traceback_enabled, force_color).
TracebackState = tuple[bool, bool]


def apply_traceback_preferences(enabled: bool) -> None:
    """Synchronise shared traceback flags with the requested preference.

    Args:
        enabled: ``True`` enables full tracebacks with colour.

    Example:
        >>> apply_traceback_preferences(True)
        >>> bool(lib_cli_exit_tools.config.traceback)
        True
    """
    lib_cli_exit_tools.config.traceback = bool(enabled)
    lib_cli_exit_tools.config.traceback_force_color = bool(enabled)


def snapshot_traceback_state() -> TracebackState:
    """Capture the current traceback configuration for later restoration.

    Returns:
        Tuple of ``(traceback_enabled, force_color)``.

    Example:
        >>> state = snapshot_traceback_state()
        >>> isinstance(state, tuple) and len(state) == 2
        True
    """
    return (
        bool(getattr(lib_cli_exit_tools.config, "traceback", False)),
        bool(getattr(lib_cli_exit_tools.config, "traceback_force_color", False)),
    )


def restore_traceback_state(state: TracebackState) -> None:
    """Reapply a previously captured traceback configuration.

    Args:
        state: Tuple returned by :func:`snapshot_traceback_state`.

    Example:
        >>> original = snapshot_traceback_state()
        >>> apply_traceback_preferences(True)
        >>> restore_traceback_state(original)
        >>> lib_cli_exit_tools.config.traceback == original[0]
        True
    """
    lib_cli_exit_tools.config.traceback = bool(state[0])
    lib_cli_exit_tools.config.traceback_force_color = bool(state[1])


__all__ = [
    "TracebackState",
    "apply_traceback_preferences",
    "restore_traceback_state",
    "snapshot_traceback_state",
]
