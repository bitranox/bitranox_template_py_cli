"""Pure greeting domain logic.

Contains the canonical greeting string and pure functions to retrieve it.
No I/O operations are performed in this module.

Example:
    >>> from bitranox_template_py_cli.domain.greeting import get_greeting
    >>> get_greeting()
    'Hello World'
"""

from typing import Final


CANONICAL_GREETING: Final[str] = "Hello World"
"""The canonical greeting message used throughout the application."""


def get_greeting() -> str:
    """Return the canonical greeting string.

    This is a pure function that returns the greeting without any I/O.

    Returns:
        The canonical greeting message.

    Example:
        >>> get_greeting()
        'Hello World'
    """
    return CANONICAL_GREETING


__all__ = [
    "CANONICAL_GREETING",
    "get_greeting",
]
