"""Public package surface exposing domain, application, and adapter layers.

This package follows clean architecture with four layers:
- Domain: Pure business logic (greeting, errors)
- Application: Use cases and ports
- Adapters: Framework implementations (CLI, output)
- Composition: Dependency wiring

Commonly used symbols are re-exported at package level for convenience.
"""

# Domain exports
from .domain.greeting import CANONICAL_GREETING, get_greeting
from .domain.errors import IntentionalFailure

# Composition exports
from .composition import container

# Metadata exports
from .__init__conf__ import print_info


__all__ = [
    # Domain
    "CANONICAL_GREETING",
    "get_greeting",
    "IntentionalFailure",
    # Composition
    "container",
    # Metadata
    "print_info",
]
