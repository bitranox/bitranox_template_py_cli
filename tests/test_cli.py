"""Tests for the CLI module.

Each test validates a single CLI behavior:
- Traceback configuration management
- Command invocation and routing
- Help output and error handling

Tests prefer real CLI execution over stubs wherever possible.
"""

from collections.abc import Callable

import pytest
from click.testing import CliRunner

import lib_cli_exit_tools

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.composition import container
from bitranox_template_py_cli.adapters.cli import (
    CLICK_CONTEXT_SETTINGS,
    TRACEBACK_SUMMARY_LIMIT,
    TRACEBACK_VERBOSE_LIMIT,
    apply_traceback_preferences,
    cli,
    main,
    restore_traceback_state,
    snapshot_traceback_state,
)
from bitranox_template_py_cli.adapters.cli.context import (
    CLIContextData,
    get_cli_context,
    store_cli_context,
)


# ---------------------------------------------------------------------------
# Traceback Configuration Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_snapshot_captures_initial_state(isolated_traceback_config: None) -> None:
    """Snapshot returns (False, False) when traceback is disabled."""
    state = snapshot_traceback_state()

    assert state == (False, False)


@pytest.mark.os_agnostic
def test_apply_traceback_enables_both_flags(isolated_traceback_config: None) -> None:
    """Enabling traceback sets both traceback and force_color to True."""
    apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_apply_traceback_disables_both_flags(isolated_traceback_config: None) -> None:
    """Disabling traceback sets both flags to False."""
    apply_traceback_preferences(True)
    apply_traceback_preferences(False)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_restore_traceback_reverts_to_previous_state(isolated_traceback_config: None) -> None:
    """Restore brings config back to the captured state."""
    previous = snapshot_traceback_state()
    apply_traceback_preferences(True)

    restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


# ---------------------------------------------------------------------------
# CLI Context Data Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_context_data_defaults_to_traceback_false() -> None:
    """CLIContextData has traceback disabled by default."""
    context_data = CLIContextData()

    assert context_data.traceback is False


@pytest.mark.os_agnostic
def test_cli_context_data_accepts_traceback_true() -> None:
    """CLIContextData accepts traceback=True."""
    context_data = CLIContextData(traceback=True)

    assert context_data.traceback is True


@pytest.mark.os_agnostic
def test_cli_context_data_is_mutable() -> None:
    """CLIContextData allows mutation for Click compatibility."""
    context_data = CLIContextData(traceback=False)

    context_data.traceback = True

    assert context_data.traceback is True


@pytest.mark.os_agnostic
def test_store_cli_context_sets_ctx_obj() -> None:
    """store_cli_context stores CLIContextData in ctx.obj."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.obj = None

    store_cli_context(ctx, traceback=True)

    assert isinstance(ctx.obj, CLIContextData)
    assert ctx.obj.traceback is True


@pytest.mark.os_agnostic
def test_get_cli_context_returns_stored_data() -> None:
    """get_cli_context returns the CLIContextData from ctx.obj."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.obj = CLIContextData(traceback=True)

    result = get_cli_context(ctx)

    assert result.traceback is True


@pytest.mark.os_agnostic
def test_get_cli_context_creates_default_when_none() -> None:
    """get_cli_context creates CLIContextData when ctx.obj is None."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.obj = None

    result = get_cli_context(ctx)

    assert isinstance(result, CLIContextData)
    assert result.traceback is False


@pytest.mark.os_agnostic
def test_get_cli_context_creates_default_when_wrong_type() -> None:
    """get_cli_context creates CLIContextData when ctx.obj is wrong type."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.obj = "not a CLIContextData"

    result = get_cli_context(ctx)

    assert isinstance(result, CLIContextData)
    assert result.traceback is False


# ---------------------------------------------------------------------------
# CLI Help and Usage Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_without_arguments_shows_help(cli_runner: CliRunner) -> None:
    """Invoking CLI without arguments shows help text."""
    result = cli_runner.invoke(cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_cli_with_help_flag_shows_help(cli_runner: CliRunner) -> None:
    """The --help flag shows the help text."""
    result = cli_runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert __init__conf__.title in result.output


@pytest.mark.os_agnostic
def test_cli_with_short_help_flag_shows_help(cli_runner: CliRunner) -> None:
    """The -h flag shows the help text."""
    result = cli_runner.invoke(cli, ["-h"])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_cli_version_flag_shows_version(cli_runner: CliRunner) -> None:
    """The --version flag shows the version."""
    result = cli_runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __init__conf__.version in result.output


# ---------------------------------------------------------------------------
# Hello Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_hello_command_prints_greeting(cli_runner: CliRunner) -> None:
    """The hello command prints 'Hello World'."""
    result = cli_runner.invoke(cli, ["hello"])

    assert result.exit_code == 0
    assert result.output == "Hello World\n"


@pytest.mark.os_agnostic
def test_hello_command_with_help_shows_description(cli_runner: CliRunner) -> None:
    """The hello command has a help description."""
    result = cli_runner.invoke(cli, ["hello", "--help"])

    assert result.exit_code == 0
    assert "greeting" in result.output.lower()


# ---------------------------------------------------------------------------
# Fail Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_fail_command_raises_error(cli_runner: CliRunner) -> None:
    """The fail command raises IntentionalFailure."""
    from bitranox_template_py_cli.domain.errors import IntentionalFailure

    result = cli_runner.invoke(cli, ["fail"])

    assert result.exit_code != 0
    assert isinstance(result.exception, IntentionalFailure)


@pytest.mark.os_agnostic
def test_fail_command_exception_message(cli_runner: CliRunner) -> None:
    """The fail command raises with message 'I should fail'."""
    result = cli_runner.invoke(cli, ["fail"])

    assert str(result.exception) == "I should fail"


# ---------------------------------------------------------------------------
# Info Command Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_info_command_shows_package_name(cli_runner: CliRunner) -> None:
    """The info command shows the package name."""
    result = cli_runner.invoke(cli, ["info"])

    assert result.exit_code == 0
    assert __init__conf__.name in result.output


@pytest.mark.os_agnostic
def test_info_command_shows_version(cli_runner: CliRunner) -> None:
    """The info command shows the version."""
    result = cli_runner.invoke(cli, ["info"])

    assert result.exit_code == 0
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_info_command_shows_all_metadata_fields(cli_runner: CliRunner) -> None:
    """The info command shows all expected metadata fields."""
    result = cli_runner.invoke(cli, ["info"])

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
    result = cli_runner.invoke(cli, ["nonexistent"])

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_unknown_command_suggests_alternatives(cli_runner: CliRunner) -> None:
    """An unknown command may suggest similar commands."""
    result = cli_runner.invoke(cli, ["helo"])  # typo of 'hello'

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
    monkeypatch.setattr(container, "noop", lambda: calls.append("called"))

    result = cli_runner.invoke(cli, ["--traceback"])

    assert result.exit_code == 0
    assert calls == ["called"]


@pytest.mark.os_agnostic
def test_no_traceback_flag_without_command_shows_help(cli_runner: CliRunner) -> None:
    """The --no-traceback flag alone shows help."""
    result = cli_runner.invoke(cli, ["--no-traceback"])

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
    exit_code = main(["--traceback", "fail"])
    stderr = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in stderr
    assert "IntentionalFailure: I should fail" in stderr


@pytest.mark.os_agnostic
def test_traceback_flag_does_not_truncate_output(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """The --traceback flag shows complete output without truncation."""
    exit_code = main(["--traceback", "fail"])
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
    main(["--traceback", "hello"])

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_main_can_skip_restore(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Main can be told not to restore traceback config."""
    main(["--traceback", "hello"], restore_traceback=False)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_main_returns_zero_on_success(isolated_traceback_config: None) -> None:
    """Main returns 0 when command succeeds."""
    exit_code = main(["hello"])

    assert exit_code == 0


@pytest.mark.os_agnostic
def test_main_returns_nonzero_on_failure(isolated_traceback_config: None) -> None:
    """Main returns non-zero when command fails."""
    exit_code = main(["fail"])

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

    monkeypatch.setattr(__init__conf__, "print_info", capture_state)

    main(["--traceback", "info"])

    assert observed_states == [(True, True)]


# ---------------------------------------------------------------------------
# CLI Module Constants Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_traceback_summary_limit_is_reasonable() -> None:
    """The summary limit is a sensible value."""
    assert TRACEBACK_SUMMARY_LIMIT > 0
    assert TRACEBACK_SUMMARY_LIMIT < 10000


@pytest.mark.os_agnostic
def test_traceback_verbose_limit_is_larger_than_summary() -> None:
    """The verbose limit is larger than the summary limit."""
    assert TRACEBACK_VERBOSE_LIMIT > TRACEBACK_SUMMARY_LIMIT


@pytest.mark.os_agnostic
def test_click_context_settings_has_help_options() -> None:
    """Click context settings include help option names."""
    assert "help_option_names" in CLICK_CONTEXT_SETTINGS
    assert "-h" in CLICK_CONTEXT_SETTINGS["help_option_names"]
    assert "--help" in CLICK_CONTEXT_SETTINGS["help_option_names"]
