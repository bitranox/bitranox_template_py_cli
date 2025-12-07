"""CLI adapter wiring the behavior helpers into a rich-click interface.

Exposes a stable command-line surface so tooling, documentation, and packaging
automation can be exercised while the richer logging helpers are being built.
By delegating to ``bitranox_template_py_cli.behaviors`` the transport stays
aligned with the Clean Code rules captured in
``docs/systemdesign/module_reference.md``.

Attributes:
    CLICK_CONTEXT_SETTINGS: Shared Click settings ensuring consistent ``--help``
        behavior across commands.
    TRACEBACK_SUMMARY_LIMIT: Character budget for truncated tracebacks.
    TRACEBACK_VERBOSE_LIMIT: Character budget for verbose tracebacks.

Functions:
    apply_traceback_preferences: Helper that synchronises the shared traceback
        configuration flags.
    snapshot_traceback_state: Captures traceback configuration for preservation.
    restore_traceback_state: Reapplies previously captured traceback config.
    cli: Root command group wiring the global options.
    cli_main: Default action when no subcommand is provided.
    cli_info: Subcommand for metadata printing.
    cli_hello: Subcommand for success path.
    cli_fail: Subcommand for failure path.
    main: Composition helper delegating to ``lib_cli_exit_tools`` while
        honouring the shared traceback preferences.

Note:
    The CLI is the primary adapter for local development workflows; packaging
    targets register the console script defined in
    ``bitranox_template_py_cli.__init__conf__``. Other transports (including
    ``python -m`` execution) reuse the same helpers so behaviour remains
    consistent regardless of entry point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Optional, Sequence, Tuple

import rich_click as click

import lib_cli_exit_tools
from click.core import ParameterSource

from . import __init__conf__
from .behaviors import emit_greeting, noop_main, raise_intentional_failure


@dataclass(slots=True)
class ClickContextSettings:
    """Typed container for Click context settings.

    Attributes:
        help_option_names: List of option names that trigger help output.
    """

    help_option_names: list[str] = field(default_factory=lambda: ["-h", "--help"])

    def as_dict(self) -> dict[str, list[str]]:
        """Convert to dict for Click compatibility.

        Returns:
            Dictionary representation for Click's context_settings parameter.
        """
        return {"help_option_names": self.help_option_names}


@dataclass(slots=True)
class CLIContextData:
    """Typed container for CLI context data stored in Click's ctx.obj.

    Attributes:
        traceback: Whether verbose tracebacks are enabled.
    """

    traceback: bool = False


#: Shared Click context flags so help output stays consistent across commands.
_CLICK_CONTEXT_SETTINGS_MODEL = ClickContextSettings()
CLICK_CONTEXT_SETTINGS: dict[str, list[str]] = _CLICK_CONTEXT_SETTINGS_MODEL.as_dict()
#: Character budget used when printing truncated tracebacks.
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500
#: Character budget used when verbose tracebacks are enabled.
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000
TracebackState = Tuple[bool, bool]


def apply_traceback_preferences(enabled: bool) -> None:
    """Synchronise shared traceback flags with the requested preference.

    ``lib_cli_exit_tools`` inspects global flags to decide whether tracebacks
    should be truncated and whether colour should be forced. Updating both
    attributes together ensures the ``--traceback`` flag behaves the same for
    console scripts and ``python -m`` execution.

    Args:
        enabled: ``True`` enables full tracebacks with colour. ``False`` restores
            the compact summary mode.

    Example:
        >>> apply_traceback_preferences(True)
        >>> bool(lib_cli_exit_tools.config.traceback)
        True
        >>> bool(lib_cli_exit_tools.config.traceback_force_color)
        True
    """
    lib_cli_exit_tools.config.traceback = bool(enabled)
    lib_cli_exit_tools.config.traceback_force_color = bool(enabled)


def snapshot_traceback_state() -> TracebackState:
    """Capture the current traceback configuration for later restoration.

    Returns:
        Tuple of ``(traceback_enabled, force_color)``.

    Example:
        >>> snapshot = snapshot_traceback_state()
        >>> isinstance(snapshot, tuple)
        True
    """
    return (
        bool(getattr(lib_cli_exit_tools.config, "traceback", False)),
        bool(getattr(lib_cli_exit_tools.config, "traceback_force_color", False)),
    )


def restore_traceback_state(state: TracebackState) -> None:
    """Reapply a previously captured traceback configuration.

    Args:
        state: Tuple returned by ``snapshot_traceback_state()``.

    Example:
        >>> prev = snapshot_traceback_state()
        >>> apply_traceback_preferences(True)
        >>> restore_traceback_state(prev)
        >>> snapshot_traceback_state() == prev
        True
    """
    lib_cli_exit_tools.config.traceback = bool(state[0])
    lib_cli_exit_tools.config.traceback_force_color = bool(state[1])


def _get_or_create_context_data(ctx: click.Context) -> CLIContextData:
    """Retrieve or create the typed context data object.

    Args:
        ctx: Click context associated with the current invocation.

    Returns:
        The CLIContextData instance stored in ctx.obj.
    """
    if ctx.obj is None or not isinstance(ctx.obj, CLIContextData):
        ctx.obj = CLIContextData()
    return ctx.obj


def _record_traceback_choice(ctx: click.Context, *, enabled: bool) -> None:
    """Remember the chosen traceback mode inside the Click context.

    Downstream commands need to know whether verbose tracebacks were requested
    so they can honour the user's preference without re-parsing flags. Ensures
    the context has a typed CLIContextData backing store and persists the
    boolean in the traceback field.

    Args:
        ctx: Click context associated with the current invocation.
        enabled: ``True`` when verbose tracebacks were requested; ``False``
            otherwise.

    Note:
        Mutates ``ctx.obj``.
    """
    context_data = _get_or_create_context_data(ctx)
    context_data.traceback = enabled


def _announce_traceback_choice(enabled: bool) -> None:
    """Keep ``lib_cli_exit_tools`` in sync with the selected traceback mode.

    ``lib_cli_exit_tools`` reads global configuration to decide how to print
    tracebacks; we mirror the user's choice into that configuration.

    Args:
        enabled: ``True`` when verbose tracebacks should be shown; ``False``
            when the summary view is desired.

    Note:
        Mutates ``lib_cli_exit_tools.config``.
    """
    apply_traceback_preferences(enabled)


def _no_subcommand_requested(ctx: click.Context) -> bool:
    """Return ``True`` when the invocation did not name a subcommand.

    The CLI defaults to calling ``noop_main`` when no subcommand appears; we
    need a readable predicate to capture that intent.

    Args:
        ctx: Click context describing the current CLI invocation.

    Returns:
        ``True`` when no subcommand was invoked; ``False`` otherwise.
    """
    return ctx.invoked_subcommand is None


def _invoke_cli(argv: Optional[Sequence[str]]) -> int:
    """Ask ``lib_cli_exit_tools`` to execute the Click command.

    ``lib_cli_exit_tools`` normalises exit codes and exception handling; we
    centralise the call so tests can stub it cleanly.

    Args:
        argv: Optional sequence of command-line arguments. ``None`` delegates to
            ``sys.argv`` inside ``lib_cli_exit_tools``.

    Returns:
        Exit code returned by the CLI execution.
    """
    return lib_cli_exit_tools.run_cli(
        cli,
        argv=list(argv) if argv is not None else None,
        prog_name=__init__conf__.shell_command,
    )


def _current_traceback_mode() -> bool:
    """Return the global traceback preference as a boolean.

    Error handling logic needs to know whether verbose tracebacks are active so
    it can pick the right character budget and ensure colouring is consistent.

    Returns:
        ``True`` when verbose tracebacks are enabled; ``False`` otherwise.
    """
    return bool(getattr(lib_cli_exit_tools.config, "traceback", False))


def _traceback_limit(tracebacks_enabled: bool, *, summary_limit: int, verbose_limit: int) -> int:
    """Return the character budget that matches the current traceback mode.

    Verbose tracebacks should show the full story while compact ones keep the
    terminal tidy. This helper makes that decision explicit.

    Args:
        tracebacks_enabled: ``True`` when verbose tracebacks are active.
        summary_limit: Character budget for truncated output.
        verbose_limit: Character budget for the full traceback.

    Returns:
        The applicable character limit.
    """
    return verbose_limit if tracebacks_enabled else summary_limit


def _print_exception(exc: BaseException, *, tracebacks_enabled: bool, length_limit: int) -> int:
    """Render the exception through ``lib_cli_exit_tools`` and return its exit code.

    All transports funnel errors through ``lib_cli_exit_tools`` so that exit
    codes and formatting stay consistent; this helper keeps the plumbing in one
    place.

    Args:
        exc: Exception raised by the CLI.
        tracebacks_enabled: ``True`` when verbose tracebacks should be shown.
        length_limit: Maximum number of characters to print.

    Returns:
        Exit code to surface to the shell.

    Note:
        Writes the formatted exception to stderr via ``lib_cli_exit_tools``.
    """
    lib_cli_exit_tools.print_exception_message(
        trace_back=tracebacks_enabled,
        length_limit=length_limit,
    )
    return lib_cli_exit_tools.get_system_exit_code(exc)


def _traceback_option_requested(ctx: click.Context) -> bool:
    """Return ``True`` when the user explicitly requested ``--traceback``.

    Determines whether a no-command invocation should run the default behaviour
    or display the help screen.

    Args:
        ctx: Click context associated with the current invocation.

    Returns:
        ``True`` when the user provided ``--traceback`` or ``--no-traceback``;
        ``False`` when the default value is in effect.
    """
    source = ctx.get_parameter_source("traceback")
    return source not in (ParameterSource.DEFAULT, None)


def _show_help(ctx: click.Context) -> None:
    """Render the command help to stdout.

    Args:
        ctx: Click context containing the help information.
    """
    click.echo(ctx.get_help())


def _run_cli_via_exit_tools(
    argv: Optional[Sequence[str]],
    *,
    summary_limit: int,
    verbose_limit: int,
) -> int:
    """Run the command while narrating the failure path with care.

    Consolidates the call to ``lib_cli_exit_tools`` so happy paths and error
    handling remain consistent across the application and tests.

    Args:
        argv: Optional sequence of CLI arguments.
        summary_limit: Character budget for truncated exception output.
        verbose_limit: Character budget for verbose exception output.

    Returns:
        Exit code produced by the command.

    Note:
        Delegates to ``lib_cli_exit_tools`` which may write to stderr.
    """
    try:
        return _invoke_cli(argv)
    except BaseException as exc:  # noqa: BLE001 - handled by shared printers
        tracebacks_enabled = _current_traceback_mode()
        apply_traceback_preferences(tracebacks_enabled)
        return _print_exception(
            exc,
            tracebacks_enabled=tracebacks_enabled,
            length_limit=_traceback_limit(
                tracebacks_enabled,
                summary_limit=summary_limit,
                verbose_limit=verbose_limit,
            ),
        )


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

    The CLI must provide a switch for verbose tracebacks so developers can
    toggle diagnostic depth without editing configuration files. Ensures a
    typed CLIContextData context, stores the ``traceback`` flag, and mirrors
    the value into ``lib_cli_exit_tools.config`` so downstream helpers observe
    the preference. When no subcommand (or options) are provided, the command
    prints help instead of running the domain stub; otherwise the default
    action delegates to ``cli_main``.

    Args:
        ctx: Click context for the current invocation.
        traceback: ``True`` to enable verbose tracebacks; ``False`` for summary.

    Note:
        Mutates ``lib_cli_exit_tools.config`` to reflect the requested traceback
        mode, including ``traceback_force_color`` when tracebacks are enabled.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli, ["hello"])
        >>> result.exit_code
        0
        >>> "Hello World" in result.output
        True
    """
    _record_traceback_choice(ctx, enabled=traceback)
    _announce_traceback_choice(traceback)
    if _no_subcommand_requested(ctx):
        if _traceback_option_requested(ctx):
            cli_main()
        else:
            _show_help(ctx)


def cli_main() -> None:
    """Run the placeholder domain entry when callers opt into execution.

    Maintains compatibility with tooling that expects the original "do-nothing"
    behaviour by explicitly opting in via options (e.g. ``--traceback`` without
    subcommands). Delegates to ``noop_main``.

    Example:
        >>> cli_main()
    """
    noop_main()


@cli.command("info", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_info() -> None:
    """Print resolved metadata so users can inspect installation details."""
    __init__conf__.print_info()


@cli.command("hello", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_hello() -> None:
    """Demonstrate the success path by emitting the canonical greeting."""
    emit_greeting()


@cli.command("fail", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_fail() -> None:
    """Trigger the intentional failure helper to test error handling."""
    raise_intentional_failure()


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    restore_traceback: bool = True,
    summary_limit: int = TRACEBACK_SUMMARY_LIMIT,
    verbose_limit: int = TRACEBACK_VERBOSE_LIMIT,
) -> int:
    """Execute the CLI with deliberate error handling and return the exit code.

    Provides the single entry point used by console scripts and ``python -m``
    execution so that behaviour stays identical across transports.

    Args:
        argv: Optional sequence of CLI arguments. ``None`` lets Click consume
            ``sys.argv`` directly.
        restore_traceback: ``True`` to restore the prior ``lib_cli_exit_tools``
            traceback configuration after execution.
        summary_limit: Character budget for truncated exceptions.
        verbose_limit: Character budget for verbose exceptions.

    Returns:
        Exit code reported by the CLI run.

    Note:
        Mutates the global traceback configuration while the CLI runs.
    """
    previous_state = snapshot_traceback_state()
    try:
        return _run_cli_via_exit_tools(
            argv,
            summary_limit=summary_limit,
            verbose_limit=verbose_limit,
        )
    finally:
        _restore_when_requested(previous_state, restore_traceback)


def _restore_when_requested(state: TracebackState, should_restore: bool) -> None:
    """Restore the prior traceback configuration when requested.

    CLI execution may toggle verbose tracebacks for the duration of the run.
    Once the command ends we restore the previous configuration so other code
    paths continue with their expected defaults.

    Args:
        state: Tuple captured by ``snapshot_traceback_state()`` describing the
            prior configuration.
        should_restore: ``True`` to reapply the stored configuration; ``False``
            to keep the current settings.

    Note:
        May mutate ``lib_cli_exit_tools.config``.
    """
    if should_restore:
        restore_traceback_state(state)
