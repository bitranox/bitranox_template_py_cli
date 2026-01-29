"""Domain-specific exceptions for typed error handling at boundaries."""

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
