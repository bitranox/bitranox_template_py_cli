"""Metadata tales ensuring fallbacks stay true."""

from __future__ import annotations

import pytest

from bitranox_template_py_cli import __init__conf__


@pytest.mark.os_agnostic
def test_when_print_info_runs_it_lists_every_field(capsys: pytest.CaptureFixture[str]) -> None:
    __init__conf__.print_info()

    captured = capsys.readouterr().out

    for label in ("name", "title", "version", "homepage", "author", "author_email", "shell_command"):
        assert f"{label}" in captured


@pytest.mark.os_agnostic
def test_when_metadata_is_missing_fallback_values_hold(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FailingMeta:
        def __call__(self, _dist: str) -> None:
            raise __init__conf__._im.PackageNotFoundError  # type: ignore[attr-defined]

    class FailingVersion:
        def __call__(self, _dist: str) -> str:
            raise __init__conf__._im.PackageNotFoundError  # type: ignore[attr-defined]

    monkeypatch.setattr(__init__conf__._im, "metadata", FailingMeta())  # type: ignore[attr-defined]
    monkeypatch.setattr(__init__conf__._im, "version", FailingVersion())  # type: ignore[attr-defined]

    __init__conf__.print_info()

    captured = capsys.readouterr().out

    assert "0.0.0.dev0" in captured
    assert "https://github.com/bitranox/bitranox_template_py_cli" in captured
