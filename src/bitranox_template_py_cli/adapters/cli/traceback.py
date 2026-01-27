"""Traceback state management for CLI error handling.

Provides helpers to synchronize and preserve traceback configuration with
``lib_cli_exit_tools`` so error output remains consistent across invocations.

Contents:
    * :func:`apply_traceback_preferences` - Enable/disable verbose tracebacks.
    * :func:`snapshot_traceback_state` - Capture current traceback config.
    * :func:`restore_traceback_state` - Restore previously captured config.
    * :class:`TracebackState` - Captured traceback configuration.
"""

from __future__ import annotations

from dataclasses import dataclass

import lib_cli_exit_tools


@dataclass(frozen=True, slots=True)
class TracebackState:
    """Captured traceback configuration for later restoration."""

    traceback_enabled: bool
    force_color: bool


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
        TracebackState with current configuration.

    Example:
        >>> state = snapshot_traceback_state()
        >>> isinstance(state, TracebackState)
        True
    """
    return TracebackState(
        traceback_enabled=bool(getattr(lib_cli_exit_tools.config, "traceback", False)),
        force_color=bool(getattr(lib_cli_exit_tools.config, "traceback_force_color", False)),
    )


def restore_traceback_state(state: TracebackState) -> None:
    """Reapply a previously captured traceback configuration.

    Args:
        state: TracebackState from :func:`snapshot_traceback_state`.

    Example:
        >>> original = snapshot_traceback_state()
        >>> apply_traceback_preferences(True)
        >>> restore_traceback_state(original)
        >>> lib_cli_exit_tools.config.traceback == original.traceback_enabled
        True
    """
    lib_cli_exit_tools.config.traceback = state.traceback_enabled
    lib_cli_exit_tools.config.traceback_force_color = state.force_color


__all__ = [
    "TracebackState",
    "apply_traceback_preferences",
    "restore_traceback_state",
    "snapshot_traceback_state",
]
