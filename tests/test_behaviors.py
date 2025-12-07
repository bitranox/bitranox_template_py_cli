"""Tests for the behaviors module.

Each test reads like a simple statement of intent:
- Greetings reach their destination
- Streams flush when they can
- Failures raise when asked
- Placeholders do nothing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO

import pytest

from bitranox_template_py_cli import behaviors


# ---------------------------------------------------------------------------
# Greeting Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_greeting_writes_hello_world_to_buffer() -> None:
    """The greeting writes 'Hello World' followed by a newline."""
    buffer = StringIO()

    behaviors.emit_greeting(stream=buffer)

    assert buffer.getvalue() == "Hello World\n"


@pytest.mark.os_agnostic
def test_greeting_defaults_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """When no stream is given, greeting goes to stdout."""
    behaviors.emit_greeting()

    captured = capsys.readouterr()

    assert captured.out == "Hello World\n"
    assert captured.err == ""


@pytest.mark.os_agnostic
def test_greeting_flushes_stream_when_possible() -> None:
    """The greeting flushes streams that support flushing."""

    @dataclass
    class FlushableStream:
        """A stream that tracks whether it was flushed."""

        content: list[str] = field(default_factory=lambda: [])
        was_flushed: bool = False

        def write(self, text: str) -> None:
            self.content.append(text)

        def flush(self) -> None:
            self.was_flushed = True

    stream = FlushableStream()

    behaviors.emit_greeting(stream=stream)  # type: ignore[arg-type]

    assert stream.content == ["Hello World\n"]
    assert stream.was_flushed is True


@pytest.mark.os_agnostic
def test_greeting_works_without_flush_method() -> None:
    """The greeting tolerates streams without a flush method."""

    @dataclass
    class NoFlushStream:
        """A stream without flush capability."""

        content: list[str] = field(default_factory=lambda: [])

        def write(self, text: str) -> None:
            self.content.append(text)

    stream = NoFlushStream()

    behaviors.emit_greeting(stream=stream)  # type: ignore[arg-type]

    assert stream.content == ["Hello World\n"]


# ---------------------------------------------------------------------------
# Failure Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_intentional_failure_raises_runtime_error() -> None:
    """Intentional failure always raises RuntimeError."""
    with pytest.raises(RuntimeError, match="I should fail"):
        behaviors.raise_intentional_failure()


@pytest.mark.os_agnostic
def test_intentional_failure_message_is_deterministic() -> None:
    """The failure message is exactly 'I should fail'."""
    try:
        behaviors.raise_intentional_failure()
    except RuntimeError as exc:
        assert str(exc) == "I should fail"


# ---------------------------------------------------------------------------
# Placeholder Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_noop_main_returns_none() -> None:
    """The placeholder main returns None."""
    result = behaviors.noop_main()

    assert result is None


@pytest.mark.os_agnostic
def test_noop_main_produces_no_output(capsys: pytest.CaptureFixture[str]) -> None:
    """The placeholder main produces no output."""
    behaviors.noop_main()

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


# ---------------------------------------------------------------------------
# Module Constants Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_canonical_greeting_constant_exists() -> None:
    """The CANONICAL_GREETING constant is defined."""
    assert behaviors.CANONICAL_GREETING == "Hello World"


@pytest.mark.os_agnostic
def test_module_exports_expected_names() -> None:
    """The module exports all expected public names."""
    expected = {"CANONICAL_GREETING", "emit_greeting", "raise_intentional_failure", "noop_main"}

    assert set(behaviors.__all__) == expected
