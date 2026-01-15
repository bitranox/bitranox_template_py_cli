"""Output adapters implementing the OutputPort protocol.

Contains concrete implementations for text output operations.

Contents:
    * :class:`.StdoutAdapter` - Writes to stdout or custom stream
"""

from .stdout import StdoutAdapter

__all__ = [
    "StdoutAdapter",
]
