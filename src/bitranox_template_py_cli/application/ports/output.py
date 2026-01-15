"""Output port interface for text output operations.

Defines the protocol that output adapters must implement to handle
text output from use cases.

Example:
    >>> from bitranox_template_py_cli.application.ports import OutputPort
    >>> class MyAdapter:
    ...     def write(self, text: str) -> None:
    ...         print(text, end='')
    ...     def write_line(self, text: str) -> None:
    ...         print(text)
    >>> adapter: OutputPort = MyAdapter()
"""

from typing import Protocol


class OutputPort(Protocol):
    """Port for writing text output.

    Adapters implementing this protocol handle text output from use cases.
    This enables dependency inversion - use cases depend on this abstract
    protocol rather than concrete implementations.
    """

    def write(self, text: str) -> None:
        """Write text without a trailing newline.

        Args:
            text: The text to write.
        """
        ...

    def write_line(self, text: str) -> None:
        """Write text followed by a newline.

        Args:
            text: The text to write.
        """
        ...


__all__ = [
    "OutputPort",
]
