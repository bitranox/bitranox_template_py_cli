"""SmtpConfigOverrides unit tests."""

from __future__ import annotations

import pytest

from bitranox_template_py_cli.adapters.cli.commands.email import SmtpConfigOverrides
from bitranox_template_py_cli.adapters.email.sender import EmailConfig


@pytest.mark.os_agnostic
def test_when_smtp_overrides_have_no_values_it_returns_same_config() -> None:
    """When no overrides are set, apply_to returns the same config instance."""
    config = EmailConfig(smtp_hosts=["smtp.example.com:587"], from_address="a@b.com")
    overrides = SmtpConfigOverrides()

    result = overrides.apply_to(config)

    assert result is config


@pytest.mark.os_agnostic
def test_when_smtp_overrides_include_host_it_applies_override() -> None:
    """When smtp_hosts is set, apply_to replaces hosts and keeps other fields unchanged."""
    config = EmailConfig(
        smtp_hosts=["smtp.original.com:587"],
        from_address="sender@example.com",
        timeout=30.0,
    )
    overrides = SmtpConfigOverrides(smtp_hosts=("smtp.override.com:465",))

    result = overrides.apply_to(config)

    assert result.smtp_hosts == ["smtp.override.com:465"]
    assert result.from_address == "sender@example.com"
    assert result.timeout == 30.0


@pytest.mark.os_agnostic
def test_when_smtp_overrides_include_multiple_fields_it_applies_all() -> None:
    """When multiple overrides are set, apply_to replaces all specified fields."""
    config = EmailConfig(
        smtp_hosts=["smtp.original.com:587"],
        from_address="sender@example.com",
        use_starttls=True,
        timeout=30.0,
    )
    overrides = SmtpConfigOverrides(
        smtp_hosts=("smtp.new.com:465",),
        use_starttls=False,
        timeout=60.0,
    )

    result = overrides.apply_to(config)

    assert result.smtp_hosts == ["smtp.new.com:465"]
    assert result.use_starttls is False
    assert result.timeout == 60.0
    assert result.from_address == "sender@example.com"
