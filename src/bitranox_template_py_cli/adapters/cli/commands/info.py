"""Basic CLI commands for info, greeting, and failure testing.

Provides simple commands that demonstrate success and failure paths.

Contents:
    * :func:`cli_info` - Display package metadata.
    * :func:`cli_hello` - Emit canonical greeting.
    * :func:`cli_fail` - Trigger intentional failure for testing.
"""

import rich_click as click

from ....composition import container
from ..constants import CLICK_CONTEXT_SETTINGS


@click.command("info", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_info() -> None:
    """Print resolved metadata so users can inspect installation details.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli_info)
        >>> result.exit_code == 0
        True
    """
    use_case = container.create_info_use_case()
    use_case.execute()


@click.command("hello", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_hello() -> None:
    """Demonstrate the success path by emitting the canonical greeting.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli_hello)
        >>> "Hello World" in result.output
        True
    """
    use_case = container.create_greeting_use_case()
    use_case.execute()


@click.command("fail", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_fail() -> None:
    """Trigger the intentional failure helper to test error handling.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli_fail)
        >>> result.exit_code != 0
        True
    """
    use_case = container.create_failure_use_case()
    use_case.execute()


__all__ = ["cli_fail", "cli_hello", "cli_info"]
