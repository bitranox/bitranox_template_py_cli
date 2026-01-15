"""CLI package providing the command-line interface.

Exports all public CLI symbols from submodules.

Contents:
    * Constants from :mod:`.constants`
    * Traceback state management from :mod:`.traceback`
    * Click context helpers from :mod:`.context`
    * Root command group from :mod:`.root`
    * Entry point from :mod:`.main`
    * All command functions from :mod:`.commands`

System Role:
    Acts as the public facade for the CLI subsystem. Consumers import from here
    and remain insulated from internal module boundaries.
"""

from .constants import CLICK_CONTEXT_SETTINGS, TRACEBACK_SUMMARY_LIMIT, TRACEBACK_VERBOSE_LIMIT
from .traceback import (
    TracebackState,
    apply_traceback_preferences,
    restore_traceback_state,
    snapshot_traceback_state,
)
from .context import CLIContextData, get_cli_context, store_cli_context
from .root import cli, cli_main
from .main import main
from .commands import cli_fail, cli_hello, cli_info

__all__ = [
    # Constants
    "CLICK_CONTEXT_SETTINGS",
    "TRACEBACK_SUMMARY_LIMIT",
    "TRACEBACK_VERBOSE_LIMIT",
    # Traceback management
    "TracebackState",
    "apply_traceback_preferences",
    "restore_traceback_state",
    "snapshot_traceback_state",
    # Context helpers
    "CLIContextData",
    "get_cli_context",
    "store_cli_context",
    # Root command
    "cli",
    "cli_main",
    # Entry point
    "main",
    # Commands
    "cli_fail",
    "cli_hello",
    "cli_info",
]
