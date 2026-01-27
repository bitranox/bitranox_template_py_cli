"""Domain-level behaviors — pure functions with no I/O or framework dependencies.

Contents:
    * :func:`build_greeting` – returns the canonical scaffold greeting string.

System Role:
    Acts as the temporary domain surface for this template. Other modules import
    from here instead of duplicating literals so the public API stays coherent as
    features evolve.
"""

from __future__ import annotations


CANONICAL_GREETING = "Hello World"


def build_greeting() -> str:
    r"""Return the canonical greeting string.

    Provide a deterministic success path that the documentation, smoke
    tests, and packaging checks can rely on while the real domain logic
    is developed.

    Returns:
        The canonical greeting string.

    Example:
        >>> build_greeting()
        'Hello World'
    """
    return CANONICAL_GREETING


__all__ = [
    "CANONICAL_GREETING",
    "build_greeting",
]
