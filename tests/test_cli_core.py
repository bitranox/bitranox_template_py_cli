"""CLI core stories: traceback, main entry, help, hello, fail, info, unknown command."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import lib_cli_exit_tools
import pytest
from click.testing import CliRunner, Result

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters import cli as cli_mod
from bitranox_template_py_cli.adapters.cli.traceback import TracebackState


@dataclass(slots=True)
class CapturedRun:
    """Record of a single ``lib_cli_exit_tools.run_cli`` invocation.

    Attributes:
        command: Command object passed to ``run_cli``.
        argv: Argument vector forwarded to the command, when any.
        prog_name: Program name announced in the help output.
        signal_specs: Signal handlers registered by the runner.
        install_signals: ``True`` when the runner installed default signal handlers.
    """

    command: Any
    argv: Sequence[str] | None
    prog_name: str | None
    signal_specs: Any
    install_signals: bool


def capture_run_cli(target: list[CapturedRun]) -> Callable[..., int]:
    """Return a stub that records lib_cli_exit_tools.run_cli invocations."""

    def _run(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        target.append(
            CapturedRun(
                command=command,
                argv=argv,
                prog_name=prog_name,
                signal_specs=signal_specs,
                install_signals=install_signals,
            )
        )
        return 42

    return _run


@pytest.mark.os_agnostic
def test_when_we_snapshot_traceback_the_initial_state_is_quiet(isolated_traceback_config: None) -> None:
    """Verify snapshot_traceback_state returns disabled state initially."""
    assert cli_mod.snapshot_traceback_state() == TracebackState(traceback_enabled=False, force_color=False)


@pytest.mark.os_agnostic
def test_when_we_enable_traceback_the_config_sings_true(isolated_traceback_config: None) -> None:
    """Verify apply_traceback_preferences enables traceback flags."""
    cli_mod.apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_when_we_restore_traceback_the_config_whispers_false(isolated_traceback_config: None) -> None:
    """Verify restore_traceback_state resets traceback flags to previous values."""
    previous = cli_mod.snapshot_traceback_state()
    cli_mod.apply_traceback_preferences(True)

    cli_mod.restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_info_runs_with_traceback_the_choice_is_shared(
    monkeypatch: pytest.MonkeyPatch,
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify traceback flag is active during info command then restored."""
    notes: list[tuple[bool, bool]] = []

    def record() -> None:
        notes.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(__init__conf__, "print_info", record)

    exit_code = cli_mod.main(["--traceback", "info"])

    assert exit_code == 0
    assert notes == [(True, True)]
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_main_is_called_it_delegates_to_run_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() delegates to lib_cli_exit_tools.run_cli with correct args."""
    ledger: list[CapturedRun] = []
    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", capture_run_cli(ledger))

    result = cli_mod.main(["info"])

    assert result == 42
    assert ledger == [
        CapturedRun(
            command=cli_mod.cli,
            argv=["info"],
            prog_name=__init__conf__.shell_command,
            signal_specs=None,
            install_signals=True,
        )
    ]


@pytest.mark.os_agnostic
def test_when_cli_runs_without_arguments_help_is_printed(
    cli_runner: CliRunner,
) -> None:
    """Verify CLI with no arguments displays help text."""
    result = cli_runner.invoke(cli_mod.cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_when_main_receives_no_arguments_help_is_shown(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    isolated_traceback_config: None,
) -> None:
    """Verify main with no args shows help."""
    outputs: list[str] = []

    def fake_run_cli(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        args = [] if argv is None else list(argv)
        result: Result = cli_runner.invoke(command, args)
        if result.exception is not None:
            raise result.exception
        outputs.append(result.output)
        return result.exit_code

    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", fake_run_cli)

    exit_code = cli_mod.main([])

    assert exit_code == 0
    assert outputs and "Usage:" in outputs[0]


@pytest.mark.os_agnostic
def test_when_traceback_is_requested_without_command_help_is_shown(
    cli_runner: CliRunner,
) -> None:
    """Verify --traceback without command still shows help."""
    result = cli_runner.invoke(cli_mod.cli, ["--traceback"])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_when_traceback_flag_is_passed_the_full_story_is_printed(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Verify --traceback displays full exception traceback on failure."""
    exit_code = cli_mod.main(["--traceback", "fail"])

    plain_err = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_hello_is_invoked_the_cli_smiles(cli_runner: CliRunner) -> None:
    """Verify hello command outputs Hello World greeting."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["hello"])

    assert result.exit_code == 0
    assert "Hello World" in result.output


@pytest.mark.os_agnostic
def test_when_fail_is_invoked_the_cli_raises(cli_runner: CliRunner) -> None:
    """Verify fail command raises RuntimeError."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["fail"])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)


@pytest.mark.os_agnostic
def test_when_info_is_invoked_the_metadata_is_displayed(cli_runner: CliRunner) -> None:
    """Verify info command displays project metadata."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert f"Info for {__init__conf__.name}:" in result.output
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_when_an_unknown_command_is_used_a_helpful_error_appears(cli_runner: CliRunner) -> None:
    """Verify unknown command shows No such command error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"])

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_when_restore_is_disabled_the_traceback_choice_remains(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify restore_traceback=False keeps traceback flags enabled."""
    cli_mod.apply_traceback_preferences(False)

    cli_mod.main(["--traceback", "hello"], restore_traceback=False)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_when_logdemo_is_invoked_it_completes_successfully(
    cli_runner: CliRunner,
) -> None:
    """Verify logdemo command runs and exits with code 0."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["logdemo"])

    assert result.exit_code == 0
    assert "Log demo completed" in result.output
