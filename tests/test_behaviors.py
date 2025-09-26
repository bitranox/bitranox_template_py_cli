"""Behaviour-layer regression tests for the greeting and failure helpers."""

from __future__ import annotations

from io import StringIO

import pytest

from bitranox_template_py_cli import behaviors
from bitranox_template_py_cli import hello_world


def test_emit_greeting_writes_to_stream() -> None:
    """Emit the canonical greeting to a custom buffer."""

    buffer = StringIO()
    behaviors.emit_greeting(stream=buffer)
    assert buffer.getvalue() == "Hello World\n"


def test_hello_world_defaults_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """`hello_world` forwards to stdout when no stream is provided."""

    hello_world()
    captured = capsys.readouterr()
    assert captured.out == "Hello World\n"
    assert captured.err == ""


def test_hello_world_accepts_custom_stream() -> None:
    """`hello_world` accepts alternate streams while preserving output."""

    buffer = StringIO()
    behaviors.hello_world(stream=buffer)
    assert buffer.getvalue() == "Hello World\n"


def test_raise_intentional_failure() -> None:
    """The failure hook raises RuntimeError with the documented message."""

    with pytest.raises(RuntimeError, match="I should fail"):
        behaviors.raise_intentional_failure()


def test_noop_main_returns_none() -> None:
    """Placeholder main returns `None` to signal no work performed."""

    assert behaviors.noop_main() is None


@pytest.mark.parametrize(
    "alias",
    [behaviors.hello_world, hello_world],
)
def test_aliases_point_to_behavior(alias) -> None:
    """Both public access paths reach the same greeting implementation."""

    buffer = StringIO()
    alias(stream=buffer)
    assert buffer.getvalue() == "Hello World\n"
