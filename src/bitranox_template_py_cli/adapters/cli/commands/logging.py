"""Logging demonstration CLI command.

Provides a command to preview log output using lib_log_rich's logdemo facility.

Contents:
    * :func:`cli_logdemo` - Run a logging demonstration.
"""

from __future__ import annotations

import rich_click as click

from .. import safe_console
from ..constants import CLICK_CONTEXT_SETTINGS
from ..typed_click import option


@click.command("logdemo", context_settings=CLICK_CONTEXT_SETTINGS)
@option("--theme", default="classic", help="Logging theme to preview")
@click.pass_context
def cli_logdemo(ctx: click.Context, theme: str) -> None:
    """Run a logging demonstration to preview log output.

    \f
    Example:
        >>> from click.testing import CliRunner
        >>> from bitranox_template_py_cli.adapters.cli.root import cli
        >>> from bitranox_template_py_cli.composition import build_testing
        >>> result = CliRunner().invoke(cli, ["logdemo"], obj=build_testing)
        >>> result.exit_code, result.output.splitlines()[-1]
        (0, 'Log demo completed (theme: classic)')
    """
    import lib_log_rich  # noqa: PLC0415 - deferred: logdemo needs an uninitialised runtime, imported only when invoked
    import lib_log_rich.runtime  # noqa: PLC0415 - deferred: logdemo needs an uninitialised runtime, imported only when invoked

    # logdemo() requires uninitialized runtime
    if lib_log_rich.runtime.is_initialised():
        lib_log_rich.runtime.shutdown()

    result = lib_log_rich.logdemo(theme=theme)
    safe_console.echo(f"\nLog demo completed (theme: {result.theme})")


__all__ = ["cli_logdemo"]
