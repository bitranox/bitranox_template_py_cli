"""Property-based tests for EmailConfig Pydantic model.

Uses hypothesis to verify that EmailConfig validation enforces its
contracts across a wide range of generated inputs: valid emails pass,
port numbers in range pass, and negative timeouts are rejected.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from bitranox_template_py_cli.adapters.email.sender import EmailConfig

# ======================== Strategy helpers ========================

# Generate syntactically valid email addresses: local@domain.tld
_email_local_part = st.from_regex(r"[a-z][a-z0-9_.]{0,20}", fullmatch=True)
_email_domain = st.from_regex(r"[a-z][a-z0-9]{0,10}\.[a-z]{2,4}", fullmatch=True)
_valid_email = st.builds(lambda local, domain: f"{local}@{domain}", _email_local_part, _email_domain)  # type: ignore[arg-type]

# Generate valid SMTP host strings: hostname:port or hostname
_hostname = st.from_regex(r"[a-z][a-z0-9]{0,15}\.[a-z]{2,6}", fullmatch=True)
_port = st.integers(min_value=1, max_value=65535)
_smtp_host = st.builds(lambda h, p: f"{h}:{p}", _hostname, _port)  # type: ignore[arg-type]


# ======================== Valid email address tests ========================


@pytest.mark.os_agnostic
@given(email=_valid_email)
@settings(max_examples=100)
def test_valid_email_addresses_pass_from_address_validation(email: str) -> None:
    """Syntactically valid email addresses are accepted as from_address."""
    config = EmailConfig(from_address=email)

    assert config.from_address == email


@pytest.mark.os_agnostic
@given(email=_valid_email)
@settings(max_examples=100)
def test_valid_email_addresses_pass_recipients_validation(email: str) -> None:
    """Syntactically valid email addresses are accepted in the recipients list."""
    config = EmailConfig(recipients=[email])

    assert config.recipients == [email]


@pytest.mark.os_agnostic
@given(emails=st.lists(_valid_email, min_size=1, max_size=5))
@settings(max_examples=50)
def test_multiple_valid_recipients_pass_validation(emails: list[str]) -> None:
    """Multiple syntactically valid email addresses are accepted in recipients."""
    config = EmailConfig(recipients=emails)

    assert config.recipients == emails


# ======================== Valid SMTP host tests ========================


@pytest.mark.os_agnostic
@given(host=_smtp_host)
@settings(max_examples=100)
def test_valid_smtp_hosts_pass_validation(host: str) -> None:
    """SMTP hosts in 'hostname:port' format are accepted."""
    config = EmailConfig(smtp_hosts=[host])

    assert config.smtp_hosts == [host]


@pytest.mark.os_agnostic
@given(port=st.integers(min_value=1, max_value=65535))
@settings(max_examples=50)
def test_port_numbers_in_valid_range_pass_validation(port: int) -> None:
    """Port numbers between 1 and 65535 are accepted in SMTP host strings."""
    host = f"smtp.example.com:{port}"

    config = EmailConfig(smtp_hosts=[host])

    assert config.smtp_hosts == [host]


# ======================== Timeout validation tests ========================


@pytest.mark.os_agnostic
@given(timeout=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_non_positive_timeouts_are_rejected(timeout: float) -> None:
    """Timeouts that are zero or negative are rejected by the model validator."""
    with pytest.raises(ValidationError, match="timeout must be positive"):
        EmailConfig(timeout=timeout)


@pytest.mark.os_agnostic
@given(timeout=st.floats(min_value=0.001, max_value=3600.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_positive_timeouts_pass_validation(timeout: float) -> None:
    """Positive timeout values are accepted."""
    config = EmailConfig(timeout=timeout)

    assert config.timeout == timeout


# ======================== Boolean field tests ========================


@pytest.mark.os_agnostic
@given(use_starttls=st.booleans())
def test_use_starttls_accepts_any_boolean(use_starttls: bool) -> None:
    """The use_starttls field accepts both True and False."""
    config = EmailConfig(use_starttls=use_starttls)

    assert config.use_starttls is use_starttls


# ======================== Empty/None from_address tests ========================


@pytest.mark.os_agnostic
@given(whitespace=st.from_regex(r"\s*", fullmatch=True))
@settings(max_examples=50)
def test_whitespace_only_from_address_coerces_to_none(whitespace: str) -> None:
    """Whitespace-only from_address strings are coerced to None."""
    config = EmailConfig(from_address=whitespace)

    assert config.from_address is None
