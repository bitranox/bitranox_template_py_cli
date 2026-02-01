"""Module entry stories ensuring `python -m` mirrors the CLI."""

from __future__ import annotations

import runpy
import subprocess
import sys
from collections.abc import Callable

import lib_cli_exit_tools
import pytest

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters import cli as cli_mod


@pytest.mark.os_agnostic
def test_module_entry_executes_cli_and_shows_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """python -m invocation with no args shows help and exits 0."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli"], raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "Usage:" in captured.out
    assert __init__conf__.shell_command in captured.out


@pytest.mark.os_agnostic
def test_module_entry_formats_exceptions_via_exit_helpers(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Exceptions during module entry are formatted by lib_cli_exit_tools."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "fail"], raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    plain_err = strip_ansi(capsys.readouterr().err)
    assert exc.value.code != 0
    assert "RuntimeError" in plain_err or "I should fail" in plain_err


@pytest.mark.os_agnostic
def test_module_entry_traceback_flag_prints_full_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """--traceback via module entry prints complete traceback on error."""
    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "--traceback", "fail"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    plain_err = strip_ansi(capsys.readouterr().err)

    assert exc.value.code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_module_entry_cli_exports_all_registered_commands() -> None:
    """CLI facade exports all registered commands."""
    expected_commands = {
        "cli_config",
        "cli_config_deploy",
        "cli_config_generate_examples",
        "cli_fail",
        "cli_hello",
        "cli_info",
        "cli_logdemo",
        "cli_send_email",
        "cli_send_notification",
    }
    exported = {name for name in dir(cli_mod) if name.startswith("cli_")}
    assert expected_commands.issubset(exported)


@pytest.mark.os_agnostic
def test_module_entry_subprocess_help() -> None:
    """Verify `python -m bitranox_template_py_cli --help` works via subprocess.

    This tests the true CLI invocation path that end-users would experience,
    complementing the runpy-based tests that run in-process.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "bitranox_template_py_cli", "--help"],
        capture_output=True,
        timeout=30,
        check=False,
        # Use UTF-8 with error replacement for Windows compatibility
        # (rich-click outputs Unicode that cp1252 can't decode)
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert __init__conf__.shell_command in result.stdout


@pytest.mark.os_agnostic
def test_module_entry_subprocess_version() -> None:
    """Verify `python -m bitranox_template_py_cli --version` outputs version."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "bitranox_template_py_cli", "--version"],
        capture_output=True,
        timeout=30,
        check=False,
        # Use UTF-8 with error replacement for Windows compatibility
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0
    assert __init__conf__.version in result.stdout
