"""Domain layer - pure business logic with no I/O or framework dependencies.

Contains entities, value objects, and domain services that form the core
business logic of the application.

Contents:
    * :mod:`.behaviors` - Core domain behaviors (greeting)
    * :mod:`.enums` - Domain enumerations (OutputFormat, DeployTarget)
"""

from __future__ import annotations

from .behaviors import (
    CANONICAL_GREETING,
    build_greeting,
)
from .enums import DeployTarget, OutputFormat

__all__ = [
    # Behaviors
    "CANONICAL_GREETING",
    "build_greeting",
    # Enums
    "DeployTarget",
    "OutputFormat",
]
