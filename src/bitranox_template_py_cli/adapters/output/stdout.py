"""Stdout output adapter.

Implements the OutputPort protocol by writing to stdout or a custom stream.

Example:
    >>> from io import StringIO
    >>> from bitranox_template_py_cli.adapters.output import StdoutAdapter
    >>> buffer = StringIO()
    >>> adapter = StdoutAdapter(stream=buffer)
    >>> adapter.write_line("Hello")
    >>> buffer.getvalue()
    'Hello\\n'
"""

import sys
from typing import TextIO


class StdoutAdapter:
    """Adapter that writes text to stdout or a custom stream.

    Implements the OutputPort protocol for use cases that need
    to write text output.

    Attributes:
        _stream: The text stream to write to.
    """

    def __init__(self, stream: TextIO | None = None) -> None:
        """Initialize the adapter with a stream.

        Args:
            stream: Optional text stream to write to.
                Defaults to sys.stdout if None.
        """
        self._stream = stream if stream is not None else sys.stdout

    def write(self, text: str) -> None:
        """Write text without a trailing newline.

        Args:
            text: The text to write.

        Example:
            >>> from io import StringIO
            >>> buffer = StringIO()
            >>> adapter = StdoutAdapter(stream=buffer)
            >>> adapter.write("Hello")
            >>> buffer.getvalue()
            'Hello'
        """
        self._stream.write(text)
        self._flush()

    def write_line(self, text: str) -> None:
        """Write text followed by a newline.

        Args:
            text: The text to write.

        Example:
            >>> from io import StringIO
            >>> buffer = StringIO()
            >>> adapter = StdoutAdapter(stream=buffer)
            >>> adapter.write_line("Hello")
            >>> buffer.getvalue()
            'Hello\\n'
        """
        self._stream.write(f"{text}\n")
        self._flush()

    def _flush(self) -> None:
        """Flush the stream if it supports flushing."""
        flush = getattr(self._stream, "flush", None)
        if callable(flush):
            flush()


__all__ = [
    "StdoutAdapter",
]
