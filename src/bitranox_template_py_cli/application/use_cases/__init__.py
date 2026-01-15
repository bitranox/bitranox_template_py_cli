"""Application use cases.

Use cases represent application-specific business rules. They orchestrate
domain entities and interact with ports to produce results.

Contents:
    * :class:`.GreetingUseCase` - Emit the canonical greeting
    * :class:`.FailureUseCase` - Trigger intentional failure for testing
    * :class:`.InfoUseCase` - Output package metadata
"""

from .greeting import GreetingUseCase
from .failure import FailureUseCase
from .info import InfoUseCase

__all__ = [
    "GreetingUseCase",
    "FailureUseCase",
    "InfoUseCase",
]
