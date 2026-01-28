"""Domain error types: instantiation, messages, and inheritance chains."""

from __future__ import annotations

import pytest

from bitranox_template_py_cli.domain.errors import (
    ConfigurationError,
    DeliveryError,
    InvalidRecipientError,
)

# ======================== ConfigurationError ========================


@pytest.mark.os_agnostic
def test_configuration_error_inherits_from_exception() -> None:
    """ConfigurationError is a direct subclass of Exception."""
    assert issubclass(ConfigurationError, Exception)


@pytest.mark.os_agnostic
def test_configuration_error_preserves_message() -> None:
    """Instantiation stores the message for display."""
    exc = ConfigurationError("SMTP hosts not configured")
    assert str(exc) == "SMTP hosts not configured"


@pytest.mark.os_agnostic
def test_configuration_error_is_catchable_as_exception() -> None:
    """ConfigurationError can be caught by a generic except Exception clause."""
    with pytest.raises(Exception, match="missing config"):
        raise ConfigurationError("missing config")


# ======================== DeliveryError ========================


@pytest.mark.os_agnostic
def test_delivery_error_inherits_from_exception() -> None:
    """DeliveryError is a direct subclass of Exception."""
    assert issubclass(DeliveryError, Exception)


@pytest.mark.os_agnostic
def test_delivery_error_preserves_message() -> None:
    """Instantiation stores the SMTP failure detail."""
    exc = DeliveryError("Connection refused on smtp.example.com:587")
    assert str(exc) == "Connection refused on smtp.example.com:587"


@pytest.mark.os_agnostic
def test_delivery_error_is_catchable_as_exception() -> None:
    """DeliveryError can be caught by a generic except Exception clause."""
    with pytest.raises(Exception, match="SMTP timeout"):
        raise DeliveryError("SMTP timeout")


# ======================== InvalidRecipientError ========================


@pytest.mark.os_agnostic
def test_invalid_recipient_error_inherits_from_value_error() -> None:
    """InvalidRecipientError is a subclass of ValueError for backward compat."""
    assert issubclass(InvalidRecipientError, ValueError)


@pytest.mark.os_agnostic
def test_invalid_recipient_error_inherits_from_exception() -> None:
    """InvalidRecipientError is also reachable via Exception."""
    assert issubclass(InvalidRecipientError, Exception)


@pytest.mark.os_agnostic
def test_invalid_recipient_error_preserves_message() -> None:
    """Instantiation stores the validation detail."""
    exc = InvalidRecipientError("bad@@example.com")
    assert str(exc) == "bad@@example.com"


@pytest.mark.os_agnostic
def test_invalid_recipient_error_is_catchable_as_value_error() -> None:
    """Existing except ValueError handlers catch InvalidRecipientError."""
    with pytest.raises(ValueError, match="missing domain"):
        raise InvalidRecipientError("missing domain")


# ======================== Distinctness ========================


@pytest.mark.os_agnostic
def test_domain_errors_are_distinct_types() -> None:
    """All three domain errors are separate types, not aliases."""
    assert ConfigurationError is not DeliveryError
    assert DeliveryError is not InvalidRecipientError
    assert ConfigurationError is not InvalidRecipientError
