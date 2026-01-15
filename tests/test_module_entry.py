"""Tests for module entry point (`python -m bitranox_template_py_cli`).

Validates that module execution mirrors the CLI behavior.
Uses real execution where possible, with minimal stubbing for isolation.
"""

import runpy
import sys
from collections.abc import Callable

import click
import pytest

import lib_cli_exit_tools

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters.cli import cli


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
    assert "IntentionalFailure: I should fail" in stderr


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
    assert cli.name == "cli"


@pytest.mark.os_agnostic
def test_cli_command_is_a_click_group() -> None:
    """The CLI command is a Click group."""
    assert isinstance(cli, click.core.Group)


@pytest.mark.os_agnostic
def test_cli_has_expected_subcommands() -> None:
    """The CLI has the expected subcommands."""
    expected = {"hello", "fail", "info"}
    actual = set(cli.commands.keys())

    assert expected.issubset(actual)
