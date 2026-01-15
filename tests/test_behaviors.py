"""Tests for the domain and application layers.

Tests the clean architecture layers:
- Domain: Pure greeting and error logic
- Application: Use cases with ports
- Composition: Container wiring
- Package exports: Public API verification
"""

from dataclasses import dataclass, field
from io import StringIO

import pytest

# Domain imports
from bitranox_template_py_cli.domain.greeting import CANONICAL_GREETING, get_greeting
from bitranox_template_py_cli.domain.errors import IntentionalFailure

# Application imports
from bitranox_template_py_cli.application.use_cases import (
    GreetingUseCase,
    FailureUseCase,
    InfoUseCase,
)

# Adapters imports
from bitranox_template_py_cli.adapters.output import StdoutAdapter

# Composition imports
from bitranox_template_py_cli.composition import container

# Package-level imports
import bitranox_template_py_cli


# ---------------------------------------------------------------------------
# Domain Layer Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_domain_greeting_constant_exists() -> None:
    """The CANONICAL_GREETING constant is defined."""
    assert CANONICAL_GREETING == "Hello World"


@pytest.mark.os_agnostic
def test_domain_get_greeting_returns_canonical() -> None:
    """The get_greeting function returns the canonical greeting."""
    result = get_greeting()

    assert result == "Hello World"


@pytest.mark.os_agnostic
def test_domain_intentional_failure_message() -> None:
    """IntentionalFailure has the expected message."""
    exc = IntentionalFailure()

    assert str(exc) == "I should fail"


@pytest.mark.os_agnostic
def test_domain_intentional_failure_is_exception() -> None:
    """IntentionalFailure is an Exception subclass."""
    assert issubclass(IntentionalFailure, Exception)


# ---------------------------------------------------------------------------
# Application Layer Tests - Greeting Use Case
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_greeting_use_case_writes_to_output() -> None:
    """GreetingUseCase writes greeting through the output port."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)
    use_case = GreetingUseCase(output=adapter)

    use_case.execute()

    assert buffer.getvalue() == "Hello World\n"


@pytest.mark.os_agnostic
def test_greeting_use_case_is_frozen_dataclass() -> None:
    """GreetingUseCase is a frozen dataclass."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)
    use_case = GreetingUseCase(output=adapter)

    with pytest.raises(AttributeError):
        use_case.output = adapter  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Application Layer Tests - Failure Use Case
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_failure_use_case_raises_intentional_failure() -> None:
    """FailureUseCase raises IntentionalFailure."""
    use_case = FailureUseCase()

    with pytest.raises(IntentionalFailure, match="I should fail"):
        use_case.execute()


# ---------------------------------------------------------------------------
# Application Layer Tests - Info Use Case
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_info_use_case_executes_and_produces_output(capsys: pytest.CaptureFixture[str]) -> None:
    """InfoUseCase writes package metadata to stdout."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)
    use_case = InfoUseCase(output=adapter)

    use_case.execute()

    captured = capsys.readouterr()
    assert captured.out  # Produces output


@pytest.mark.os_agnostic
def test_info_use_case_is_frozen_dataclass() -> None:
    """InfoUseCase is immutable after creation."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)
    use_case = InfoUseCase(output=adapter)

    with pytest.raises(AttributeError):
        use_case.output = adapter  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Adapters Layer Tests - Stdout Adapter
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_stdout_adapter_write_line() -> None:
    """StdoutAdapter.write_line adds newline."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)

    adapter.write_line("test")

    assert buffer.getvalue() == "test\n"


@pytest.mark.os_agnostic
def test_stdout_adapter_write_no_newline() -> None:
    """StdoutAdapter.write does not add newline."""
    buffer = StringIO()
    adapter = StdoutAdapter(stream=buffer)

    adapter.write("test")

    assert buffer.getvalue() == "test"


@pytest.mark.os_agnostic
def test_stdout_adapter_flushes_stream() -> None:
    """StdoutAdapter flushes streams that support flushing."""

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
    adapter = StdoutAdapter(stream=stream)  # type: ignore[arg-type]

    adapter.write_line("test")

    assert stream.was_flushed is True


@pytest.mark.os_agnostic
def test_stdout_adapter_works_without_flush() -> None:
    """StdoutAdapter tolerates streams without a flush method."""

    @dataclass
    class NoFlushStream:
        """A stream without flush capability."""

        content: list[str] = field(default_factory=lambda: [])

        def write(self, text: str) -> None:
            self.content.append(text)

    stream = NoFlushStream()
    adapter = StdoutAdapter(stream=stream)  # type: ignore[arg-type]

    adapter.write_line("test")

    assert stream.content == ["test\n"]


# ---------------------------------------------------------------------------
# Composition Layer Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_container_create_greeting_use_case() -> None:
    """Container creates functional greeting use case."""
    buffer = StringIO()
    use_case = container.create_greeting_use_case(stream=buffer)

    use_case.execute()

    assert buffer.getvalue() == "Hello World\n"


@pytest.mark.os_agnostic
def test_container_create_failure_use_case() -> None:
    """Container creates functional failure use case."""
    use_case = container.create_failure_use_case()

    with pytest.raises(IntentionalFailure):
        use_case.execute()


@pytest.mark.os_agnostic
def test_container_noop_returns_none() -> None:
    """Container noop returns None."""
    result = container.noop()

    assert result is None


@pytest.mark.os_agnostic
def test_container_noop_produces_no_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Container noop produces no output."""
    container.noop()

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


# ---------------------------------------------------------------------------
# Package Exports Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_package_exports_canonical_greeting() -> None:
    """Package-level CANONICAL_GREETING is accessible."""
    assert bitranox_template_py_cli.CANONICAL_GREETING == "Hello World"
