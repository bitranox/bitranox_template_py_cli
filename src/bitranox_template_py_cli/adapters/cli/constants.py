"""Shared CLI constants.

Centralizes configuration values used across CLI modules to ensure consistency.

Contents:
    * :class:`ClickContextSettings` - TypedDict for Click context settings.
    * :data:`CLICK_CONTEXT_SETTINGS` - Shared Click settings for help display.
    * :data:`TRACEBACK_SUMMARY_LIMIT` - Character budget for truncated tracebacks.
    * :data:`TRACEBACK_VERBOSE_LIMIT` - Character budget for verbose tracebacks.
"""

from typing import Final, TypedDict


class ClickContextSettings(TypedDict):
    """Typed dictionary for Click context settings."""

    help_option_names: list[str]


#: Shared Click context flags so help output stays consistent across commands.
CLICK_CONTEXT_SETTINGS: Final[ClickContextSettings] = {"help_option_names": ["-h", "--help"]}

#: Character budget used when printing truncated tracebacks.
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500

#: Character budget used when verbose tracebacks are enabled.
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000

__all__ = [
    "CLICK_CONTEXT_SETTINGS",
    "TRACEBACK_SUMMARY_LIMIT",
    "TRACEBACK_VERBOSE_LIMIT",
]
