"""Dependency container for wiring adapters to ports.

Provides factory functions that create use cases with their required
adapter implementations. This is the only place where concrete adapters
are instantiated.

Example:
    >>> from bitranox_template_py_cli.composition import container
    >>> use_case = container.create_greeting_use_case()
    >>> use_case.execute()  # Writes greeting to stdout
    Hello World
"""

from typing import TextIO

from ..adapters.output.stdout import StdoutAdapter
from ..application.use_cases.greeting import GreetingUseCase
from ..application.use_cases.failure import FailureUseCase
from ..application.use_cases.info import InfoUseCase


def create_greeting_use_case(stream: TextIO | None = None) -> GreetingUseCase:
    """Create a GreetingUseCase with stdout output adapter.

    Args:
        stream: Optional text stream for output. Defaults to stdout.

    Returns:
        A wired GreetingUseCase instance.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> use_case = create_greeting_use_case(stream=buffer)
        >>> use_case.execute()
        >>> buffer.getvalue()
        'Hello World\\n'
    """
    return GreetingUseCase(output=StdoutAdapter(stream=stream))


def create_failure_use_case() -> FailureUseCase:
    """Create a FailureUseCase.

    Returns:
        A FailureUseCase instance.

    Example:
        >>> use_case = create_failure_use_case()
        >>> use_case.execute()
        Traceback (most recent call last):
        ...
        bitranox_template_py_cli.domain.errors.IntentionalFailure: I should fail
    """
    return FailureUseCase()


def create_info_use_case(stream: TextIO | None = None) -> InfoUseCase:
    """Create an InfoUseCase with stdout output adapter.

    Args:
        stream: Optional text stream for output. Defaults to stdout.

    Returns:
        A wired InfoUseCase instance.
    """
    return InfoUseCase(output=StdoutAdapter(stream=stream))


def noop() -> None:
    """Placeholder callable for transports without domain logic yet.

    Some tools expect a module-level ``main`` even when the underlying feature
    set is still stubbed out. Exposing this helper makes that contract obvious
    and easy to replace later. Performs no work and returns immediately.

    Example:
        >>> noop()
    """
    return None


__all__ = [
    "create_greeting_use_case",
    "create_failure_use_case",
    "create_info_use_case",
    "noop",
]
