"""Module-entry regression tests ensuring `python -m` parity."""

from __future__ import annotations

import runpy
import sys

import pytest

import lib_cli_exit_tools

from bitranox_template_py_cli import cli as cli_mod


def test_module_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """`python -m` should return the exit code provided by the CLI helper."""

    monkeypatch.setattr("bitranox_template_py_cli.cli.main", lambda *_, **__: 0)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 0


def test_module_main_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exceptions raised by the CLI are normalised via exit helpers."""

    def raise_error() -> int:
        raise RuntimeError("boom")

    signals: list[str] = []

    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    def fake_print(*, trace_back: bool = False, length_limit: int = 500, stream=None) -> None:
        signals.append("printed")
        assert trace_back is False
        assert length_limit == 500

    def fake_code(exc: BaseException) -> int:
        signals.append(f"code:{exc}")
        return 88

    monkeypatch.setattr("bitranox_template_py_cli.cli.main", lambda *_, **__: raise_error())
    monkeypatch.setattr(lib_cli_exit_tools, "print_exception_message", fake_print)
    monkeypatch.setattr(lib_cli_exit_tools, "get_system_exit_code", fake_code)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 88
    assert signals == ["printed", "code:boom"]


def test_module_main_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi,
) -> None:
    """`--traceback` via module entry should produce rich output."""

    monkeypatch.setattr(sys, "argv", ["bitranox_template_py_cli", "--traceback", "fail"])
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    captured = capsys.readouterr()
    plain_err = strip_ansi(captured.err)

    assert exc.value.code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


def test_cli_alias_is_imported() -> None:
    """Sanity check that module entry continues to import the CLI module."""

    # Regression guard to ensure module entry keeps using the CLI module.
    assert cli_mod.cli.name == cli_mod.cli.name
