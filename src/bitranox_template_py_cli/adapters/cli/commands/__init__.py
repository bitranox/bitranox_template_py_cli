"""CLI command implementations.

Contains the Click command functions for the CLI.

Contents:
    * :func:`cli_info` - Display package metadata.
    * :func:`cli_hello` - Emit canonical greeting.
    * :func:`cli_fail` - Trigger intentional failure for testing.
"""

from .info import cli_fail, cli_hello, cli_info

__all__ = [
    "cli_fail",
    "cli_hello",
    "cli_info",
]
