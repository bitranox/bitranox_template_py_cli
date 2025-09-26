"""CLI adapter wiring the behavior helpers into a rich-click interface.

Purpose
-------
Expose a stable command-line surface so tooling, documentation, and packaging
automation can be exercised while the richer logging helpers are being built.
By delegating to :mod:`bitranox_template_py_cli.behaviors` the transport stays
aligned with the Clean Code rules captured in
``docs/systemdesign/module_reference.md``.

Contents
--------
* :data:`CLICK_CONTEXT_SETTINGS` – shared Click settings ensuring consistent
  ``--help`` behavior across commands.
* :func:`apply_traceback_preferences` – helper that synchronises the shared
  traceback configuration flags.
* :func:`snapshot_traceback_state` / :func:`restore_traceback_state` – utilities
  for preserving and reapplying the global traceback preference.
* :func:`cli` – root command group wiring the global options.
* :func:`cli_main` – default action when no subcommand is provided.
* :func:`cli_info`, :func:`cli_hello`, :func:`cli_fail` – subcommands covering
  metadata printing, success path, and failure path.
* :func:`main` – composition helper delegating to ``lib_cli_exit_tools`` while
  honouring the shared traceback preferences.

System Role
-----------
The CLI is the primary adapter for local development workflows; packaging
targets register the console script defined in :mod:`bitranox_template_py_cli.__init__conf__`.
Other transports (including ``python -m`` execution) reuse the same helpers so
behaviour remains consistent regardless of entry point.
"""

from __future__ import annotations

from typing import Final, Optional, Sequence, Tuple

import rich_click as click

import lib_cli_exit_tools

from . import __init__conf__
from .behaviors import emit_greeting, noop_main, raise_intentional_failure

# Backwards-compat alias retained for existing tests and integrations.
_domain_main = noop_main

CLICK_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}  # noqa: C408
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000
TracebackState = Tuple[bool, bool]


def apply_traceback_preferences(enabled: bool) -> None:
    """Synchronise shared traceback flags with the requested preference.

    Why
        ``lib_cli_exit_tools`` inspects global flags to decide whether tracebacks
        should be truncated and whether colour should be forced. Updating both
        attributes together ensures the ``--traceback`` flag behaves the same for
        console scripts and ``python -m`` execution.

    Parameters
    ----------
    enabled:
        ``True`` enables full tracebacks with colour. ``False`` restores the
        compact summary mode.

    Examples
    --------
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

    Returns
    -------
    TracebackState
        Tuple of ``(traceback_enabled, force_color)``.

    Examples
    --------
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

    Parameters
    ----------
    state:
        Tuple returned by :func:`snapshot_traceback_state`.

    Examples
    --------
    >>> prev = snapshot_traceback_state()
    >>> apply_traceback_preferences(True)
    >>> restore_traceback_state(prev)
    >>> snapshot_traceback_state() == prev
    True
    """

    lib_cli_exit_tools.config.traceback = bool(state[0])
    lib_cli_exit_tools.config.traceback_force_color = bool(state[1])


def _invoke_cli(
    argv: Optional[Sequence[str]],
    *,
    summary_limit: int,
    verbose_limit: int,
) -> int:
    """Run the click application and normalise exit codes.

    Why
        ``lib_cli_exit_tools`` centralises exit-code translation and pretty
        printing. Wrapping the call keeps exception handling identical for both
        console scripts and ``python -m`` execution.

    Parameters
    ----------
    argv:
        Optional argument vector. ``None`` defers to ``sys.argv``.
    summary_limit:
        Character budget for truncated tracebacks when ``--traceback`` is not
        set.
    verbose_limit:
        Character budget for full tracebacks when ``--traceback`` is set.

    Returns
    -------
    int
        Exit code produced by the command execution.

    Examples
    --------
    >>> saved_run_cli = lib_cli_exit_tools.run_cli
    >>> calls = {}
    >>> def fake_run_cli(command, argv=None, *, prog_name=None, signal_specs=None, install_signals=True):
    ...     calls['argv'] = argv
    ...     calls['prog_name'] = prog_name
    ...     return 0
    >>> lib_cli_exit_tools.run_cli = fake_run_cli
    >>> try:
    ...     _invoke_cli(['hello'], summary_limit=10, verbose_limit=20)
    ... finally:
    ...     lib_cli_exit_tools.run_cli = saved_run_cli
    0
    >>> calls['argv']
    ['hello']
    >>> calls['prog_name'] == __init__conf__.shell_command
    True
    """

    try:
        return lib_cli_exit_tools.run_cli(
            cli,
            argv=list(argv) if argv is not None else None,
            prog_name=__init__conf__.shell_command,
        )
    except BaseException as exc:  # noqa: BLE001 - funnel through shared printers
        traceback_enabled = bool(getattr(lib_cli_exit_tools.config, "traceback", False))
        apply_traceback_preferences(traceback_enabled)
        limit = verbose_limit if traceback_enabled else summary_limit
        lib_cli_exit_tools.print_exception_message(
            trace_back=traceback_enabled,
            length_limit=limit,
        )
        return lib_cli_exit_tools.get_system_exit_code(exc)


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

    Why
        The CLI must provide a switch for verbose tracebacks so developers can
        toggle diagnostic depth without editing configuration files.

    What
        Ensures a dict-based context, stores the ``traceback`` flag, and mirrors
        the value into ``lib_cli_exit_tools.config`` so downstream helpers observe
        the preference. When no subcommand is requested the function delegates to
        :func:`cli_main` to exercise the sanctioned default behaviour.

    Side Effects
        Mutates :mod:`lib_cli_exit_tools.config` to reflect the requested
        traceback mode, including ``traceback_force_color`` when tracebacks are
        enabled.

    Examples
    --------
    >>> from click.testing import CliRunner
    >>> runner = CliRunner()
    >>> result = runner.invoke(cli, ["hello"])
    >>> result.exit_code
    0
    >>> "Hello World" in result.output
    True
    """

    ctx.ensure_object(dict)
    ctx.obj["traceback"] = traceback
    apply_traceback_preferences(traceback)
    if ctx.invoked_subcommand is None:
        cli_main()


def cli_main() -> None:
    """Run the placeholder domain entry when no subcommand is provided.

    Examples
    --------
    >>> cli_main()
    """

    _domain_main()


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
    """Execute the CLI with shared exit handling and return the exit code.

    Parameters
    ----------
    argv:
        Optional argument vector. ``None`` means defer to ``sys.argv``.
    restore_traceback:
        Whether to reset :mod:`lib_cli_exit_tools.config` after the CLI finishes.
    summary_limit:
        Character budget for truncated tracebacks when ``--traceback`` is ``False``.
    verbose_limit:
        Character budget for verbose tracebacks when ``--traceback`` is ``True``.

    Returns
    -------
    int
        Exit code produced by the CLI.

    Examples
    --------
    >>> main(["hello"])
    Hello World
    0
    """

    previous = snapshot_traceback_state()
    try:
        return _invoke_cli(argv, summary_limit=summary_limit, verbose_limit=verbose_limit)
    finally:
        if restore_traceback:
            restore_traceback_state(previous)
