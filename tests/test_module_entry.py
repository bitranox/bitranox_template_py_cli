"""Module entry stories ensuring `python -m` mirrors the CLI."""

from __future__ import annotations

from collections.abc import Callable
import runpy
import sys
from typing import TextIO

import pytest

import lib_cli_exit_tools

from bitranox_template_py_cli import cli as cli_mod


@pytest.mark.os_agnostic
def test_when_module_entry_returns_zero_the_story_matches_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    def return_zero(*_args: object, **_kwargs: object) -> int:
        return 0

    monkeypatch.setattr("bitranox_template_py_cli.cli.main", return_zero)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 0


@pytest.mark.os_agnostic
def test_when_module_entry_raises_the_exit_helpers_format_the_song(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_error() -> int:
        raise RuntimeError("boom")

    signals: list[str] = []

    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

    def fake_print(
        *,
        trace_back: bool = False,
        length_limit: int = 500,
        stream: TextIO | None = None,
    ) -> None:
        signals.append(f"printed:{trace_back}:{length_limit}:{stream is not None}")

    def fake_code(exc: BaseException) -> int:
        signals.append(f"code:{exc}")
        return 88

    def trigger_error(*_args: object, **_kwargs: object) -> int:
        return raise_error()

    monkeypatch.setattr("bitranox_template_py_cli.cli.main", trigger_error)
    monkeypatch.setattr(lib_cli_exit_tools, "print_exception_message", fake_print)
    monkeypatch.setattr(lib_cli_exit_tools, "get_system_exit_code", fake_code)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("bitranox_template_py_cli.__main__", run_name="__main__")

    assert exc.value.code == 88
    assert signals == ["printed:False:500:False", "code:boom"]


@pytest.mark.os_agnostic
def test_when_traceback_flag_is_used_via_module_entry_the_full_poem_is_printed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
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
def test_when_module_entry_imports_cli_the_alias_stays_intact() -> None:
    assert cli_mod.cli.name == cli_mod.cli.name
