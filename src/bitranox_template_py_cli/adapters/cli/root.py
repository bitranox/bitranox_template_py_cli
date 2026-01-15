"""Root CLI command group and global option handling.

Defines the top-level Click command group that serves as the entry point for
all subcommands. Handles global flags like --traceback.

Contents:
    * :func:`cli` - Root command group with global options.
    * :func:`cli_main` - Domain entry when no subcommand is specified.
"""

import rich_click as click
from click.core import ParameterSource

from ... import __init__conf__
from ...composition import container
from .constants import CLICK_CONTEXT_SETTINGS
from .context import store_cli_context
from .traceback import apply_traceback_preferences


@click.group(
    help=__init__conf__.title,
    context_settings=CLICK_CONTEXT_SETTINGS,
    invoke_without_command=True,
)
@click.version_option(
    version=__init__conf__.version,
    prog_name=__init__conf__.shell_command,
    message=f"{__init__conf__.shell_command} version {__init__conf__.version}",
)
@click.option(
    "--traceback/--no-traceback",
    is_flag=True,
    default=False,
    help="Show full Python traceback on errors",
)
@click.pass_context
def cli(ctx: click.Context, traceback: bool) -> None:
    """Root command storing global flags and syncing shared traceback state.

    Stores the traceback flag in the Click context and mirrors it into
    ``lib_cli_exit_tools.config`` so downstream helpers observe the preference.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli, ["hello"])
        >>> result.exit_code
        0
        >>> "Hello World" in result.output
        True
    """
    store_cli_context(ctx, traceback=traceback)
    apply_traceback_preferences(traceback)

    if ctx.invoked_subcommand is None:
        _handle_no_subcommand(ctx)


def _handle_no_subcommand(ctx: click.Context) -> None:
    """Handle invocation when no subcommand is provided.

    Shows help unless --traceback was explicitly passed.

    Args:
        ctx: Click context with parameter source information.
    """
    source = ctx.get_parameter_source("traceback")
    if source not in (ParameterSource.DEFAULT, None):
        cli_main()
    else:
        click.echo(ctx.get_help())


def cli_main() -> None:
    """Run the placeholder domain entry when callers opt into execution.

    Example:
        >>> cli_main()  # No output, just runs noop
    """
    container.noop()


def _register_commands() -> None:
    """Register all subcommands with the root CLI group."""
    from .commands import cli_fail, cli_hello, cli_info

    cli.add_command(cli_info)
    cli.add_command(cli_hello)
    cli.add_command(cli_fail)


_register_commands()


__all__ = ["cli", "cli_main"]
