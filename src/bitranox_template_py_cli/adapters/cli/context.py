"""Click context helpers for CLI state management.

Provides utilities to store and retrieve CLI state from Click's context object,
enabling subcommands to access shared configuration and flags.

Contents:
    * :class:`CLIContext` - Typed dataclass for CLI state.
    * :func:`store_cli_context` - Store CLI state in Click context.
    * :func:`get_cli_context` - Retrieve typed CLI state from Click context.
    * :func:`apply_traceback_preferences` - Enable/disable verbose tracebacks.
    * :func:`snapshot_traceback_state` - Capture current traceback config.
    * :func:`restore_traceback_state` - Restore previously captured config.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import lib_cli_exit_tools
import rich_click as click
from lib_layered_config import Config

if TYPE_CHECKING:
    from bitranox_template_py_cli.application.ports import (
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )

TracebackState = tuple[bool, bool]
"""Captured traceback configuration: (traceback_enabled, force_color)."""


@dataclass(slots=True)
class CLIContext:
    """Typed CLI context for Click subcommand access.

    Provides type-safe access to CLI state instead of using untyped dict.

    Attributes:
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object.
        profile: Optional configuration profile name.
        set_overrides: Raw ``--set`` override strings from CLI for reapplication.
        send_email: Optional email service override (None = use production).
        send_notification: Optional notification service override (None = use production).
        load_email_config_from_dict: Optional config loader override (None = use production).
    """

    traceback: bool
    config: Config
    profile: str | None = None
    set_overrides: tuple[str, ...] = ()
    # Service overrides for testing (None = use production defaults)
    send_email: SendEmail | None = None
    send_notification: SendNotification | None = None
    load_email_config_from_dict: LoadEmailConfigFromDict | None = None


def store_cli_context(
    ctx: click.Context,
    *,
    traceback: bool,
    config: Config,
    profile: str | None = None,
    set_overrides: tuple[str, ...] = (),
    send_email: SendEmail | None = None,
    send_notification: SendNotification | None = None,
    load_email_config_from_dict: LoadEmailConfigFromDict | None = None,
) -> None:
    """Store CLI state in the Click context for subcommand access.

    Args:
        ctx: Click context associated with the current invocation.
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object for all subcommands.
        profile: Optional configuration profile name.
        set_overrides: Raw ``--set`` override strings for reapplication when
            subcommands reload config with a different profile.
        send_email: Optional email service override for testing.
        send_notification: Optional notification service override for testing.
        load_email_config_from_dict: Optional config loader override for testing.

    Example:
        >>> from click.testing import CliRunner
        >>> from unittest.mock import MagicMock
        >>> ctx = MagicMock()
        >>> ctx.obj = None
        >>> mock_config = MagicMock()
        >>> store_cli_context(ctx, traceback=True, config=mock_config, profile="test")
        >>> ctx.obj.traceback
        True
    """
    ctx.obj = CLIContext(
        traceback=traceback,
        config=config,
        profile=profile,
        set_overrides=set_overrides,
        send_email=send_email,
        send_notification=send_notification,
        load_email_config_from_dict=load_email_config_from_dict,
    )


def get_cli_context(ctx: click.Context) -> CLIContext:
    """Retrieve typed CLI state from Click context.

    Args:
        ctx: Click context containing CLI state.

    Returns:
        CLIContext dataclass with typed access to CLI state.

    Raises:
        RuntimeError: If CLI context was not properly initialized.

    Example:
        >>> from unittest.mock import MagicMock
        >>> ctx = MagicMock()
        >>> mock_config = MagicMock()
        >>> ctx.obj = CLIContext(traceback=False, config=mock_config)
        >>> cli_ctx = get_cli_context(ctx)
        >>> cli_ctx.traceback
        False
    """
    if not isinstance(ctx.obj, CLIContext):
        raise RuntimeError("CLI context not initialized. Call store_cli_context first.")
    return ctx.obj


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
        Tuple of (traceback_enabled, force_color) booleans.

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
        state: Tuple from :func:`snapshot_traceback_state`.

    Example:
        >>> original = snapshot_traceback_state()
        >>> apply_traceback_preferences(True)
        >>> restore_traceback_state(original)
        >>> lib_cli_exit_tools.config.traceback == original[0]
        True
    """
    lib_cli_exit_tools.config.traceback = state[0]
    lib_cli_exit_tools.config.traceback_force_color = state[1]


__all__ = [
    "CLIContext",
    "TracebackState",
    "apply_traceback_preferences",
    "get_cli_context",
    "restore_traceback_state",
    "snapshot_traceback_state",
    "store_cli_context",
]
