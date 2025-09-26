"""CLI adapter integration tests covering command dispatch and exit handling."""

from __future__ import annotations

from typing import Any

import pytest

import lib_cli_exit_tools

from bitranox_template_py_cli import cli as cli_mod
from bitranox_template_py_cli import __init__conf__


def test_traceback_preferences_round_trip(
    isolated_traceback_config: None,
) -> None:
    """Snapshot, flip, and restore the shared traceback configuration."""

    snapshot = cli_mod.snapshot_traceback_state()
    assert snapshot == (False, False)

    cli_mod.apply_traceback_preferences(True)
    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True

    cli_mod.restore_traceback_state(snapshot)
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


def test_cli_info_command_sets_traceback(
    monkeypatch: pytest.MonkeyPatch,
    isolated_traceback_config: None,
    preserve_traceback_state,
) -> None:
    """Invoking `info` toggles traceback preferences and restores them."""

    calls: list[tuple[bool, bool]] = []

    def record_traceback_flag() -> None:
        calls.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(cli_mod.__init__conf__, "print_info", record_traceback_flag)

    exit_code = cli_mod.main(["--traceback", "info"])

    assert exit_code == 0
    assert calls == [(True, True)]
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


def test_main_delegates_to_run_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """`cli.main` must pass through to `lib_cli_exit_tools.run_cli`."""

    recorded: list[dict[str, Any]] = []

    def fake_run_cli(command, argv=None, *, prog_name=None, signal_specs=None, install_signals=True):
        recorded.append(
            {
                "command": command,
                "argv": argv,
                "prog_name": prog_name,
                "signal_specs": signal_specs,
                "install_signals": install_signals,
            }
        )
        return 42

    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", fake_run_cli)

    result = cli_mod.main(["info"])

    assert result == 42
    assert recorded == [
        {
            "command": cli_mod.cli,
            "argv": ["info"],
            "prog_name": __init__conf__.shell_command,
            "signal_specs": None,
            "install_signals": True,
        }
    ]


def test_cli_without_subcommand_calls_domain_main(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner,
) -> None:
    """Bare CLI invocation should call the domain placeholder."""

    calls: list[str] = []

    def record_call() -> None:
        calls.append("called")

    monkeypatch.setattr(cli_mod, "_domain_main", record_call)
    result = cli_runner.invoke(cli_mod.cli, [])

    assert result.exit_code == 0
    assert calls == ["called"]
    assert result.output.strip() == ""


def test_main_without_subcommand_delegates_to_cli_main(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner,
    isolated_traceback_config: None,
) -> None:
    """Running `cli.main` without argv should exercise `cli.cli_main`."""

    calls: list[str] = []

    def record_call() -> None:
        calls.append("called")

    monkeypatch.setattr(cli_mod, "_domain_main", record_call)

    def fake_run_cli(command, argv=None, *, prog_name=None, signal_specs=None, install_signals=True):
        args = [] if argv is None else list(argv)
        result = cli_runner.invoke(command, args)
        if result.exception is not None:
            raise result.exception
        return result.exit_code

    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", fake_run_cli)

    exit_code = cli_mod.main([])

    assert exit_code == 0
    assert calls == ["called"]


def test_main_traceback_renders_rich(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_traceback_config: None,
    strip_ansi,
) -> None:
    """`--traceback` renders the full traceback without truncation."""

    exit_code = cli_mod.main(["--traceback", "fail"])

    captured = capsys.readouterr()
    plain_err = strip_ansi(captured.err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


def test_cli_hello_and_fail_commands(cli_runner) -> None:
    """Happy-path and failure commands behave as documented."""

    result_hello = cli_runner.invoke(cli_mod.cli, ["hello"])
    assert result_hello.exit_code == 0

    result_fail = cli_runner.invoke(cli_mod.cli, ["fail"])
    assert result_fail.exit_code != 0
    assert isinstance(result_fail.exception, RuntimeError)
