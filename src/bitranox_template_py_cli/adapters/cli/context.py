"""Click context helpers for CLI state management.

Provides utilities to store and retrieve CLI state from Click's context object,
enabling subcommands to access shared configuration and flags.

Contents:
    * :class:`CLIContext` - Typed dataclass for CLI state.
    * :func:`store_cli_context` - Store CLI state in Click context.
    * :func:`get_cli_context` - Retrieve typed CLI state from Click context.
"""

from __future__ import annotations

from dataclasses import dataclass

import rich_click as click
from lib_layered_config import Config


@dataclass(slots=True)
class CLIContext:
    """Typed CLI context for Click subcommand access.

    Provides type-safe access to CLI state instead of using untyped dict.

    Attributes:
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object.
        profile: Optional configuration profile name.
        set_overrides: Raw ``--set`` override strings from CLI for reapplication.
    """

    traceback: bool
    config: Config
    profile: str | None = None
    set_overrides: tuple[str, ...] = ()


def store_cli_context(
    ctx: click.Context,
    *,
    traceback: bool,
    config: Config,
    profile: str | None = None,
    set_overrides: tuple[str, ...] = (),
) -> None:
    """Store CLI state in the Click context for subcommand access.

    Args:
        ctx: Click context associated with the current invocation.
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object for all subcommands.
        profile: Optional configuration profile name.
        set_overrides: Raw ``--set`` override strings for reapplication when
            subcommands reload config with a different profile.

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
    ctx.obj = CLIContext(traceback=traceback, config=config, profile=profile, set_overrides=set_overrides)


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


__all__ = ["CLIContext", "store_cli_context", "get_cli_context"]
