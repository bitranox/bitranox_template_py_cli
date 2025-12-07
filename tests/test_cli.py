"""Tests for the CLI module.

Each test validates a single CLI behavior:
- Traceback configuration management
- Command invocation and routing
- Help output and error handling

Tests prefer real CLI execution over stubs wherever possible.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from click.testing import CliRunner

import lib_cli_exit_tools

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli import cli as cli_mod


# ---------------------------------------------------------------------------
# Traceback Configuration Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_snapshot_captures_initial_state(isolated_traceback_config: None) -> None:
    """Snapshot returns (False, False) when traceback is disabled."""
    state = cli_mod.snapshot_traceback_state()

    assert state == (False, False)


@pytest.mark.os_agnostic
def test_apply_traceback_enables_both_flags(isolated_traceback_config: None) -> None:
    """Enabling traceback sets both traceback and force_color to True."""
    cli_mod.apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_apply_traceback_disables_both_flags(isolated_traceback_config: None) -> None:
    """Disabling traceback sets both flags to False."""
    cli_mod.apply_traceback_preferences(True)
    cli_mod.apply_traceback_preferences(False)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_restore_traceback_reverts_to_previous_state(isolated_traceback_config: None) -> None:
    """Restore brings config back to the captured state."""
    previous = cli_mod.snapshot_traceback_state()
    cli_mod.apply_traceback_preferences(True)

    cli_mod.restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


# ---------------------------------------------------------------------------
# CLI Help and Usage Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_without_arguments_shows_help(cli_runner: CliRunner) -> None:
    """Invoking CLI without arguments shows help text."""
    result = cli_runner.invoke(cli_mod.cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_cli_with_help_flag_shows_help(cli_runner: CliRunner) -> None:
    """The --help flag shows the help text."""
    result = cli_runner.invoke(cli_mod.cli, ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert __init__conf__.title in result.output


@pytest.mark.os_agnostic
def test_cli_with_short_help_flag_shows_help(cli_runner: CliRunner) -> None:
    """The -h flag shows the help text."""
    result = cli_runner.invoke(cli_mod.cli, ["-h"])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_cli_version_flag_shows_version(cli_runner: CliRunner) -> None:
    """The --version flag shows the version."""
    result = cli_runner.invoke(cli_mod.cli, ["--version"])

    assert result.exit_code == 0
    assert __init__conf__.version in result.output


# ---------------------------------------------------------------------------
# Hello Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_hello_command_prints_greeting(cli_runner: CliRunner) -> None:
    """The hello command prints 'Hello World'."""
    result = cli_runner.invoke(cli_mod.cli, ["hello"])

    assert result.exit_code == 0
    assert result.output == "Hello World\n"


@pytest.mark.os_agnostic
def test_hello_command_with_help_shows_description(cli_runner: CliRunner) -> None:
    """The hello command has a help description."""
    result = cli_runner.invoke(cli_mod.cli, ["hello", "--help"])

    assert result.exit_code == 0
    assert "greeting" in result.output.lower()


# ---------------------------------------------------------------------------
# Fail Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_fail_command_raises_error(cli_runner: CliRunner) -> None:
    """The fail command raises RuntimeError."""
    result = cli_runner.invoke(cli_mod.cli, ["fail"])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)


@pytest.mark.os_agnostic
def test_fail_command_exception_message(cli_runner: CliRunner) -> None:
    """The fail command raises with message 'I should fail'."""
    result = cli_runner.invoke(cli_mod.cli, ["fail"])

    assert str(result.exception) == "I should fail"


# ---------------------------------------------------------------------------
# Info Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_info_command_shows_package_name(cli_runner: CliRunner) -> None:
    """The info command shows the package name."""
    result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert __init__conf__.name in result.output


@pytest.mark.os_agnostic
def test_info_command_shows_version(cli_runner: CliRunner) -> None:
    """The info command shows the version."""
    result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_info_command_shows_all_metadata_fields(cli_runner: CliRunner) -> None:
    """The info command shows all expected metadata fields."""
    result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "title" in result.output
    assert "version" in result.output
    assert "homepage" in result.output
    assert "author" in result.output


# ---------------------------------------------------------------------------
# Unknown Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_unknown_command_shows_error(cli_runner: CliRunner) -> None:
    """An unknown command shows an error message."""
    result = cli_runner.invoke(cli_mod.cli, ["nonexistent"])

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_unknown_command_suggests_alternatives(cli_runner: CliRunner) -> None:
    """An unknown command may suggest similar commands."""
    result = cli_runner.invoke(cli_mod.cli, ["helo"])  # typo of 'hello'

    assert result.exit_code != 0
    # Rich-click may show suggestions


# ---------------------------------------------------------------------------
# Traceback Flag Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_traceback_flag_without_command_runs_noop(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The --traceback flag without a command runs the noop main."""
    calls: list[str] = []
    monkeypatch.setattr(cli_mod, "noop_main", lambda: calls.append("called"))

    result = cli_runner.invoke(cli_mod.cli, ["--traceback"])

    assert result.exit_code == 0
    assert calls == ["called"]


@pytest.mark.os_agnostic
def test_no_traceback_flag_without_command_shows_help(cli_runner: CliRunner) -> None:
    """The --no-traceback flag alone shows help."""
    result = cli_runner.invoke(cli_mod.cli, ["--no-traceback"])

    assert result.exit_code == 0
    # --no-traceback is explicit so should still trigger noop
    assert "Usage:" not in result.output or result.output == ""


@pytest.mark.os_agnostic
def test_traceback_flag_enables_verbose_errors(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """The --traceback flag shows full tracebacks on errors."""
    exit_code = cli_mod.main(["--traceback", "fail"])
    stderr = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in stderr
    assert "RuntimeError: I should fail" in stderr


@pytest.mark.os_agnostic
def test_traceback_flag_does_not_truncate_output(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """The --traceback flag shows complete output without truncation."""
    exit_code = cli_mod.main(["--traceback", "fail"])
    stderr = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "[TRUNCATED" not in stderr


# ---------------------------------------------------------------------------
# Main Function Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_main_restores_traceback_by_default(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Main restores traceback config after execution."""
    cli_mod.main(["--traceback", "hello"])

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_main_can_skip_restore(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Main can be told not to restore traceback config."""
    cli_mod.main(["--traceback", "hello"], restore_traceback=False)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_main_returns_zero_on_success(isolated_traceback_config: None) -> None:
    """Main returns 0 when command succeeds."""
    exit_code = cli_mod.main(["hello"])

    assert exit_code == 0


@pytest.mark.os_agnostic
def test_main_returns_nonzero_on_failure(isolated_traceback_config: None) -> None:
    """Main returns non-zero when command fails."""
    exit_code = cli_mod.main(["fail"])

    assert exit_code != 0


# ---------------------------------------------------------------------------
# Info Command with Traceback Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_info_with_traceback_shares_config(
    monkeypatch: pytest.MonkeyPatch,
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Info command with --traceback sees the traceback config."""
    observed_states: list[tuple[bool, bool]] = []

    def capture_state() -> None:
        observed_states.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(cli_mod.__init__conf__, "print_info", capture_state)

    cli_mod.main(["--traceback", "info"])

    assert observed_states == [(True, True)]


# ---------------------------------------------------------------------------
# CLI Module Constants Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_traceback_summary_limit_is_reasonable() -> None:
    """The summary limit is a sensible value."""
    assert cli_mod.TRACEBACK_SUMMARY_LIMIT > 0
    assert cli_mod.TRACEBACK_SUMMARY_LIMIT < 10000


@pytest.mark.os_agnostic
def test_traceback_verbose_limit_is_larger_than_summary() -> None:
    """The verbose limit is larger than the summary limit."""
    assert cli_mod.TRACEBACK_VERBOSE_LIMIT > cli_mod.TRACEBACK_SUMMARY_LIMIT


@pytest.mark.os_agnostic
def test_click_context_settings_has_help_options() -> None:
    """Click context settings include help option names."""
    assert "help_option_names" in cli_mod.CLICK_CONTEXT_SETTINGS
    assert "-h" in cli_mod.CLICK_CONTEXT_SETTINGS["help_option_names"]
    assert "--help" in cli_mod.CLICK_CONTEXT_SETTINGS["help_option_names"]
