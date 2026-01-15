"""Composition layer for dependency wiring.

This layer is the outermost layer that wires adapters to ports. It creates
the concrete instances of use cases with their required dependencies.

Contents:
    * :mod:`.container` - Factory functions for creating wired use cases
"""

from . import container

__all__ = [
    "container",
]
