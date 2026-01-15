"""Domain-specific exceptions.

Contains exceptions that represent domain-level error conditions.
These exceptions are raised by domain logic and mapped to appropriate
responses by adapters.

Example:
    >>> from bitranox_template_py_cli.domain.errors import IntentionalFailure
    >>> raise IntentionalFailure()
    Traceback (most recent call last):
    ...
    bitranox_template_py_cli.domain.errors.IntentionalFailure: I should fail
"""


class IntentionalFailure(Exception):
    """Deterministic error for testing failure flows.

    Raised by the failure use case to provide a guaranteed error scenario
    for testing traceback handling and error display.

    Example:
        >>> raise IntentionalFailure()
        Traceback (most recent call last):
        ...
        bitranox_template_py_cli.domain.errors.IntentionalFailure: I should fail
    """

    def __init__(self) -> None:
        """Initialize with the canonical failure message."""
        super().__init__("I should fail")


__all__ = [
    "IntentionalFailure",
]
