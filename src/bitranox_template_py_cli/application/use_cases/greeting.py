"""Greeting use case.

Emits the canonical greeting via the output port.

Example:
    >>> from io import StringIO
    >>> from bitranox_template_py_cli.application.use_cases import GreetingUseCase
    >>> class TestAdapter:
    ...     def __init__(self):
    ...         self.buffer = StringIO()
    ...     def write(self, text: str) -> None:
    ...         self.buffer.write(text)
    ...     def write_line(self, text: str) -> None:
    ...         self.buffer.write(f"{text}\\n")
    >>> adapter = TestAdapter()
    >>> use_case = GreetingUseCase(output=adapter)
    >>> use_case.execute()
    >>> adapter.buffer.getvalue()
    'Hello World\\n'
"""

from dataclasses import dataclass

from ..ports.output import OutputPort
from ...domain.greeting import get_greeting


@dataclass(frozen=True, slots=True)
class GreetingUseCase:
    """Use case that emits the canonical greeting.

    Retrieves the greeting from the domain layer and writes it
    to the output port.

    Attributes:
        output: The output port to write the greeting to.
    """

    output: OutputPort

    def execute(self) -> None:
        """Execute the use case by writing the greeting.

        Example:
            >>> from io import StringIO
            >>> class TestAdapter:
            ...     def __init__(self):
            ...         self.buffer = StringIO()
            ...     def write(self, text: str) -> None:
            ...         self.buffer.write(text)
            ...     def write_line(self, text: str) -> None:
            ...         self.buffer.write(f"{text}\\n")
            >>> adapter = TestAdapter()
            >>> GreetingUseCase(output=adapter).execute()
            >>> "Hello World" in adapter.buffer.getvalue()
            True
        """
        self.output.write_line(get_greeting())


__all__ = [
    "GreetingUseCase",
]
