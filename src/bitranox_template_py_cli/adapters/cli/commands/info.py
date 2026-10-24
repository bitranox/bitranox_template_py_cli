"""Basic CLI commands for info, greeting, and failure testing.

Provides simple commands that demonstrate success and failure paths.

Contents:
    * :func:`cli_info` - Display package metadata.
    * :func:`cli_hello` - Emit canonical greeting.
    * :func:`cli_fail` - Trigger intentional failure for testing.
"""

from __future__ import annotations

import logging

import lib_log_rich.runtime
import rich_click as click

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.domain.behaviors import build_greeting

from .. import safe_console
from ..constants import CLICK_CONTEXT_SETTINGS

logger = logging.getLogger(__name__)


@click.command("info", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_info() -> None:
    """Print resolved metadata so users can inspect installation details.

    \f
    Example:
        >>> from click.testing import CliRunner
        >>> from bitranox_template_py_cli.adapters.cli.root import cli
        >>> from bitranox_template_py_cli.composition import build_testing
        >>> result = CliRunner().invoke(cli, ["info"], obj=build_testing)
        >>> result.exit_code
        0
        >>> result.output.splitlines()[0]
        'Info for bitranox-template-py-cli:'
    """
    with lib_log_rich.runtime.bind(job_id="cli-info", extra={"command": "info"}):
        logger.info("Displaying package information")
        __init__conf__.print_info()


@click.command("hello", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_hello() -> None:
    """Demonstrate the success path by emitting the canonical greeting.

    \f
    Example:
        >>> from click.testing import CliRunner
        >>> from bitranox_template_py_cli.adapters.cli.root import cli
        >>> from bitranox_template_py_cli.composition import build_testing
        >>> result = CliRunner().invoke(cli, ["hello"], obj=build_testing)
        >>> result.exit_code, result.output.strip()
        (0, 'Hello World')
    """
    with lib_log_rich.runtime.bind(job_id="cli-hello", extra={"command": "hello"}):
        logger.info("Executing hello command")
        safe_console.echo(build_greeting())


@click.command("fail", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_fail() -> None:
    """Trigger the intentional failure helper to test error handling.

    \f
    Example:
        >>> from click.testing import CliRunner
        >>> from bitranox_template_py_cli.adapters.cli.root import cli
        >>> from bitranox_template_py_cli.composition import build_testing
        >>> result = CliRunner().invoke(cli, ["fail"], obj=build_testing)
        >>> result.exit_code, type(result.exception).__name__, str(result.exception)
        (1, 'RuntimeError', 'I should fail')
    """
    with lib_log_rich.runtime.bind(job_id="cli-fail", extra={"command": "fail"}):
        logger.warning("Executing intentional failure command")
        raise RuntimeError("I should fail")


__all__ = ["cli_fail", "cli_hello", "cli_info"]
