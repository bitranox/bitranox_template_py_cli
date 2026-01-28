"""Domain error types for typed exception handling.

Provides domain-specific exceptions that replace generic stdlib exceptions
at architectural boundaries, enabling precise ``except`` clauses in CLI
error-handling code.

Contents:
    * :class:`ConfigurationError` - Missing, invalid, or incomplete configuration.
    * :class:`DeliveryError` - Email/notification delivery failed at SMTP level.
    * :class:`InvalidRecipientError` - Email address validation failure.
"""

from __future__ import annotations


class ConfigurationError(Exception):
    """Missing, invalid, or incomplete configuration."""


class DeliveryError(Exception):
    """Email/notification delivery failed at SMTP level."""


class InvalidRecipientError(ValueError):
    """Email address validation failure.

    Inherits from ValueError so existing ``except ValueError`` handlers
    continue to catch it during the migration period.
    """


__all__ = [
    "ConfigurationError",
    "DeliveryError",
    "InvalidRecipientError",
]
