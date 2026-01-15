"""Failure use case.

Raises the intentional failure for testing error handling flows.

Example:
    >>> from bitranox_template_py_cli.application.use_cases import FailureUseCase
    >>> use_case = FailureUseCase()
    >>> use_case.execute()
    Traceback (most recent call last):
    ...
    bitranox_template_py_cli.domain.errors.IntentionalFailure: I should fail
"""

from ...domain.errors import IntentionalFailure


class FailureUseCase:
    """Use case that triggers an intentional failure.

    Raises the domain IntentionalFailure exception to test
    error handling and traceback display.
    """

    def execute(self) -> None:
        """Execute the use case by raising IntentionalFailure.

        Raises:
            IntentionalFailure: Always raised to trigger error handling.

        Example:
            >>> FailureUseCase().execute()
            Traceback (most recent call last):
            ...
            bitranox_template_py_cli.domain.errors.IntentionalFailure: I should fail
        """
        raise IntentionalFailure()


__all__ = [
    "FailureUseCase",
]
