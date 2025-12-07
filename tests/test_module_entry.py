"""Tests for module entry point (`python -m bitranox_template_py_cli`).

Validates that module execution mirrors the CLI behavior.
Uses real execution where possible, with minimal stubbing for isolation.
"""

from __future__ import annotations

import runpy
import sys
from collections.abc import Callable

import pytest

import lib_cli_exit_tools

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli import cli as cli_mod
from bitranox_template_py_cli import __main__ as main_mod


# ---------------------------------------------------------------------------
# Module Constants Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_traceback_summary_limit_matches_cli() -> None:
    """Module entry traceback summary limit matches CLI."""
    assert main_mod.TRACEBACK_SUMMARY_LIMIT == cli_mod.TRACEBACK_SUMMARY_LIMIT


@pytest.mark.os_agnostic
def test_traceback_verbose_limit_matches_cli() -> None:
    """Module entry traceback verbose limit matches CLI."""
    assert main_mod.TRACEBACK_VERBOSE_LIMIT == cli_mod.TRACEBACK_VERBOSE_LIMIT


# ---------------------------------------------------------------------------
# Helper Function Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_command_to_run_returns_cli_command() -> None:
    """_command_to_run returns the CLI command."""
    command = main_mod._command_to_run()  # pyright: ignore[reportPrivateUsage]

    assert command is cli_mod.cli


@pytest.mark.os_agnostic
def test_command_name_returns_shell_command() -> None:
    """_command_name returns the shell command from __init__conf__."""
    name = main_mod._command_name()  # pyright: ignore[reportPrivateUsage]

    assert name == __init__conf__.shell_command


@pytest.mark.os_agnostic
def test_open_cli_session_returns_context_manager() -> None:
    """_open_cli_session returns a context manager."""
    session = main_mod._open_cli_session()  # pyright: ignore[reportPrivateUsage]

    assert hasattr(session, "__enter__")
    assert hasattr(session, "__exit__")


# ---------------------------------------------------------------------------
# Real Module Entry Tests (via runpy)
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_module_entry_with_hello_prints_greeting(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running the module with 'hello' prints the greeting."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "hello"])

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 0
    assert "Hello World" in capsys.readouterr().out


@pytest.mark.os_agnostic
def test_module_entry_with_info_shows_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running the module with 'info' shows metadata."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "info"])

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert __init__conf__.name in output


@pytest.mark.os_agnostic
def test_module_entry_with_fail_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running the module with 'fail' exits with non-zero."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "fail"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code != 0


@pytest.mark.os_agnostic
def test_module_entry_with_traceback_shows_full_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Running the module with --traceback shows full traceback."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "--traceback", "fail"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    stderr = strip_ansi(capsys.readouterr().err)

    assert exc.value.code != 0
    assert "Traceback (most recent call last)" in stderr
    assert "RuntimeError: I should fail" in stderr


@pytest.mark.os_agnostic
def test_module_entry_does_not_truncate_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Module entry with --traceback does not truncate output."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "--traceback", "fail"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit):
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    stderr = strip_ansi(capsys.readouterr().err)

    assert "[TRUNCATED" not in stderr


@pytest.mark.os_agnostic
def test_module_entry_preserves_traceback_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Module entry restores traceback config after execution."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "--traceback", "hello"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit):
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    # After execution, config should be restored
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


# ---------------------------------------------------------------------------
# CLI Command Identity Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_command_has_expected_name() -> None:
    """The CLI command has the expected name."""
    assert cli_mod.cli.name == "cli"


@pytest.mark.os_agnostic
def test_cli_command_is_a_click_group() -> None:
    """The CLI command is a Click group."""
    import click

    assert isinstance(cli_mod.cli, click.core.Group)


@pytest.mark.os_agnostic
def test_cli_has_expected_subcommands() -> None:
    """The CLI has the expected subcommands."""
    expected = {"hello", "fail", "info"}
    actual = set(cli_mod.cli.commands.keys())

    assert expected.issubset(actual)
