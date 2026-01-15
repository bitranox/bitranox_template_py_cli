"""Application layer containing use cases and ports.

This layer orchestrates domain logic and defines the ports (interfaces)
that adapters must implement. It contains:
- Use cases (application-specific business rules)
- Ports (Protocol interfaces for dependency injection)
- DTOs (Data Transfer Objects) if needed

All code in this layer:
- Can import from domain layer
- Cannot import from adapters layer
- Must not contain framework-specific types

Contents:
    * :mod:`.ports` - Protocol interfaces for dependency injection
    * :mod:`.use_cases` - Application use cases
"""

from .ports import OutputPort
from .use_cases import FailureUseCase, GreetingUseCase, InfoUseCase

__all__ = [
    # Ports
    "OutputPort",
    # Use cases
    "FailureUseCase",
    "GreetingUseCase",
    "InfoUseCase",
]
