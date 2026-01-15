"""Adapters layer containing framework implementations.

This layer implements the ports defined in the application layer and
provides concrete implementations for external interactions. It contains:
- Output adapters (stdout, file, etc.)
- CLI transport (rich-click commands)
- Any other infrastructure implementations

All code in this layer:
- Can import from domain and application layers
- Implements port interfaces from application layer
- Contains framework-specific code

Contents:
    * :mod:`.output` - Output adapters (stdout, etc.)
    * :mod:`.cli` - CLI transport using rich-click
"""

__all__: list[str] = []
