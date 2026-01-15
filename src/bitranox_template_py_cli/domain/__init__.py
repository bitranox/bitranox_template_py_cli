"""Domain layer containing pure business logic.

This layer is the innermost layer of the clean architecture. It contains:
- Value objects and entities
- Domain errors
- Pure functions with no I/O or framework dependencies

All code in this layer must be:
- Pure (no side effects, no I/O)
- Synchronous
- Free from framework dependencies
- Free from logging

Contents:
    * :mod:`.greeting` - Greeting domain logic
    * :mod:`.errors` - Domain-specific exceptions
"""

from .greeting import CANONICAL_GREETING, get_greeting
from .errors import IntentionalFailure

__all__ = [
    "CANONICAL_GREETING",
    "get_greeting",
    "IntentionalFailure",
]
