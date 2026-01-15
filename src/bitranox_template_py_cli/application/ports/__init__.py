"""Port interfaces for dependency injection.

Ports define the contracts that adapters must implement. They use
Python's Protocol for structural subtyping, enabling dependency
inversion without requiring explicit inheritance.

Contents:
    * :class:`.OutputPort` - Interface for text output operations
"""

from .output import OutputPort

__all__ = [
    "OutputPort",
]
