"""Metadata tales celebrating the pinned project portrait."""

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
def test_the_metadata_constants_match_the_project() -> None:
    assert __init__conf__.name == "bitranox_template_py_cli"
    assert __init__conf__.title == "Template for python apps with registered cli commands"
    assert __init__conf__.version == "1.7.0"
    assert __init__conf__.homepage == "https://github.com/bitranox/bitranox_template_py_cli"
    assert __init__conf__.author == "bitranox"
    assert __init__conf__.author_email == "bitranox@gmail.com"
    assert __init__conf__.shell_command == "bitranox-template-py-cli"
