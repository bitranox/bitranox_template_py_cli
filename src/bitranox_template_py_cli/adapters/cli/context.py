"""Click context helpers for CLI state management.

Provides utilities to store and retrieve CLI state from Click's context object,
enabling subcommands to access shared configuration and flags.

Contents:
    * :class:`CLIContextData` - Pydantic model for CLI context data.
    * :func:`store_cli_context` - Store CLI state in Click context.
    * :func:`get_cli_context` - Retrieve CLI state from Click context.
"""

from pydantic import BaseModel
import rich_click as click


class CLIContextData(BaseModel):
    """Pydantic model for CLI context data stored in Click's ctx.obj.

    Uses Pydantic for boundary validation as CLI context is a system boundary.

    Attributes:
        traceback: Whether verbose tracebacks are enabled.
    """

    traceback: bool = False

    model_config = {"frozen": False}  # Click may mutate context


def store_cli_context(ctx: click.Context, *, traceback: bool) -> None:
    """Store CLI state in the Click context for subcommand access.

    Args:
        ctx: Click context associated with the current invocation.
        traceback: Whether verbose tracebacks were requested.

    Example:
        >>> from unittest.mock import MagicMock
        >>> ctx = MagicMock()
        >>> ctx.obj = None
        >>> store_cli_context(ctx, traceback=True)
        >>> ctx.obj.traceback
        True
    """
    ctx.obj = CLIContextData(traceback=traceback)


def get_cli_context(ctx: click.Context) -> CLIContextData:
    """Retrieve CLI state from the Click context.

    Args:
        ctx: Click context associated with the current invocation.

    Returns:
        The CLIContextData instance stored in ctx.obj.

    Example:
        >>> from unittest.mock import MagicMock
        >>> ctx = MagicMock()
        >>> ctx.obj = CLIContextData(traceback=True)
        >>> data = get_cli_context(ctx)
        >>> data.traceback
        True
    """
    if ctx.obj is None or not isinstance(ctx.obj, CLIContextData):
        ctx.obj = CLIContextData()
    return ctx.obj


__all__ = [
    "CLIContextData",
    "get_cli_context",
    "store_cli_context",
]
