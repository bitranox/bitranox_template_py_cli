"""Email functionality stories: every sending scenario a single verse.

Verify that the mail wrapper correctly integrates btx_lib_mail with the
application's configuration system and provides a clean interface for
email operations.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from bitranox_template_py_cli.adapters.email.sender import (
    EmailConfig,
    load_email_config_from_dict,
    send_email,
    send_notification,
)


# ======================== EmailConfig Default Values ========================


@pytest.mark.os_agnostic
def test_when_no_hosts_given_the_config_starts_empty() -> None:
    """Without SMTP hosts, the list begins empty and waiting."""
    assert EmailConfig().smtp_hosts == []


@pytest.mark.os_agnostic
def test_when_no_sender_given_none_stands_in() -> None:
    """Without a from address, None signals not configured."""
    assert EmailConfig().from_address is None


@pytest.mark.os_agnostic
def test_when_no_credentials_given_none_is_remembered() -> None:
    """Without credentials, username and password stay absent."""
    config = EmailConfig()
    assert config.smtp_username is None
    assert config.smtp_password is None


@pytest.mark.os_agnostic
def test_when_security_unspecified_starttls_guards_the_gate() -> None:
    """Without explicit security, STARTTLS protects by default."""
    assert EmailConfig().use_starttls is True


@pytest.mark.os_agnostic
def test_when_patience_unset_thirty_seconds_is_the_wait() -> None:
    """Without a timeout, thirty seconds patience is given."""
    assert EmailConfig().timeout == 30.0


@pytest.mark.os_agnostic
def test_when_strictness_unspecified_missing_attachments_halt() -> None:
    """Without relaxation, missing attachments raise alarms."""
    assert EmailConfig().raise_on_missing_attachments is True


@pytest.mark.os_agnostic
def test_when_validation_unspecified_bad_recipients_fail() -> None:
    """Without leniency, invalid recipients are rejected."""
    assert EmailConfig().raise_on_invalid_recipient is True


@pytest.mark.os_agnostic
def test_email_config_accepts_custom_values() -> None:
    """When custom values provided, EmailConfig stores them correctly."""
    config = EmailConfig(
        smtp_hosts=["smtp.example.com:587"],
        from_address="test@example.com",
        recipients=["admin@example.com", "ops@example.com"],
        smtp_username="user",
        smtp_password="pass",
        use_starttls=False,
        timeout=60.0,
    )

    assert config.smtp_hosts == ["smtp.example.com:587"]
    assert config.from_address == "test@example.com"
    assert config.recipients == ["admin@example.com", "ops@example.com"]
    assert config.smtp_username == "user"
    assert config.smtp_password == "pass"
    assert config.use_starttls is False
    assert config.timeout == 60.0


@pytest.mark.os_agnostic
def test_email_config_is_immutable() -> None:
    """Once created, EmailConfig cannot be modified."""
    config = EmailConfig()

    with pytest.raises(PydanticValidationError):
        config.smtp_hosts = ["new.smtp.com"]  # type: ignore[misc]


# ======================== EmailConfig Validation ========================


@pytest.mark.os_agnostic
def test_email_config_rejects_negative_timeout() -> None:
    """Negative timeout values are caught early with clear error."""
    with pytest.raises(PydanticValidationError, match="timeout must be positive"):
        EmailConfig(timeout=-5.0)


@pytest.mark.os_agnostic
def test_email_config_rejects_zero_timeout() -> None:
    """Zero timeout is rejected as it would cause immediate failures."""
    with pytest.raises(PydanticValidationError, match="timeout must be positive"):
        EmailConfig(timeout=0.0)


@pytest.mark.os_agnostic
def test_email_config_rejects_invalid_from_address() -> None:
    """From address without @ is caught early with clear error."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(from_address="not-an-email")


@pytest.mark.os_agnostic
def test_email_config_rejects_malformed_smtp_host_port() -> None:
    """SMTP host with invalid host:port format is rejected."""
    with pytest.raises(PydanticValidationError, match="invalid smtp port"):
        EmailConfig(smtp_hosts=["smtp.test.com:587:extra"])


@pytest.mark.os_agnostic
def test_email_config_rejects_non_numeric_port() -> None:
    """Port must be a number, not text."""
    with pytest.raises(PydanticValidationError, match="invalid smtp port"):
        EmailConfig(smtp_hosts=["smtp.test.com:abc"])


@pytest.mark.os_agnostic
def test_email_config_rejects_port_above_65535() -> None:
    """Port must be within valid TCP range."""
    with pytest.raises(PydanticValidationError, match="port must be 1-65535"):
        EmailConfig(smtp_hosts=["smtp.test.com:99999"])


@pytest.mark.os_agnostic
def test_email_config_rejects_port_below_1() -> None:
    """Port 0 is reserved and invalid."""
    with pytest.raises(PydanticValidationError, match="port must be 1-65535"):
        EmailConfig(smtp_hosts=["smtp.test.com:0"])


@pytest.mark.os_agnostic
def test_email_config_accepts_host_without_port() -> None:
    """SMTP host without explicit port uses default."""
    config = EmailConfig(smtp_hosts=["smtp.test.com"])
    assert config.smtp_hosts == ["smtp.test.com"]


@pytest.mark.os_agnostic
def test_email_config_accepts_host_with_valid_port() -> None:
    """SMTP host with standard port is accepted."""
    config = EmailConfig(smtp_hosts=["smtp.test.com:587"])
    assert config.smtp_hosts == ["smtp.test.com:587"]


@pytest.mark.os_agnostic
def test_email_config_accepts_ipv6_bracketed_host_with_port() -> None:
    """Bracketed IPv6 address with port is accepted."""
    config = EmailConfig(smtp_hosts=["[::1]:25"])
    assert config.smtp_hosts == ["[::1]:25"]


@pytest.mark.os_agnostic
def test_email_config_accepts_ipv6_bracketed_host_without_port() -> None:
    """Bracketed IPv6 address without port is accepted."""
    config = EmailConfig(smtp_hosts=["[::1]"])
    assert config.smtp_hosts == ["[::1]"]


@pytest.mark.os_agnostic
def test_email_config_accepts_full_ipv6_bracketed_host() -> None:
    """Full bracketed IPv6 address with port is accepted."""
    config = EmailConfig(smtp_hosts=["[2001:db8::1]:587"])
    assert config.smtp_hosts == ["[2001:db8::1]:587"]


@pytest.mark.os_agnostic
def test_email_config_rejects_ipv6_missing_closing_bracket() -> None:
    """Bracketed IPv6 without closing bracket is rejected."""
    with pytest.raises(PydanticValidationError, match="missing closing bracket"):
        EmailConfig(smtp_hosts=["[::1"])


@pytest.mark.os_agnostic
def test_email_config_rejects_ipv6_invalid_port() -> None:
    """Bracketed IPv6 with non-numeric port is rejected."""
    with pytest.raises(PydanticValidationError, match="invalid smtp port"):
        EmailConfig(smtp_hosts=["[::1]:abc"])


@pytest.mark.os_agnostic
def test_email_config_accepts_none_from_address() -> None:
    """None from_address is valid (not configured)."""
    config = EmailConfig()
    assert config.from_address is None


@pytest.mark.os_agnostic
def test_email_config_rejects_bare_at_sign() -> None:
    """A bare @ is not a valid email address."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(from_address="@")


@pytest.mark.os_agnostic
def test_email_config_rejects_missing_domain() -> None:
    """An email without a domain part is rejected."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(from_address="user@")


@pytest.mark.os_agnostic
def test_email_config_rejects_missing_local_part() -> None:
    """An email without a local part is rejected."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(from_address="@domain.com")


@pytest.mark.os_agnostic
def test_email_config_rejects_double_at_sign() -> None:
    """An email with multiple @ signs is rejected."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(from_address="a@@b.com")


# ======================== EmailConfig Conversion ========================


@pytest.mark.os_agnostic
def test_email_config_converts_to_conf_mail() -> None:
    """to_conf_mail produces btx_lib_mail compatible configuration."""
    config = EmailConfig(
        smtp_hosts=["smtp.example.com:587"],
        smtp_username="user",
        smtp_password="pass",
        timeout=45.0,
    )

    conf = config.to_conf_mail()

    assert conf.smtphosts == ["smtp.example.com:587"]
    assert conf.smtp_username == "user"
    assert conf.smtp_password == "pass"
    assert conf.smtp_timeout == 45.0
    assert conf.smtp_use_starttls is True


# ======================== load_email_config_from_dict ========================


@pytest.mark.os_agnostic
def test_load_config_returns_defaults_when_email_section_missing() -> None:
    """Missing email section falls back to safe defaults."""
    config = load_email_config_from_dict({})

    assert config.smtp_hosts == []
    assert config.from_address is None


@pytest.mark.os_agnostic
def test_load_config_extracts_values_from_email_section() -> None:
    """Email section values are correctly extracted and typed."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "from_address": "alerts@test.com",
            "smtp_username": "testuser",
            "smtp_password": "testpass",
            "use_starttls": False,
            "timeout": 120.0,
        }
    }

    config = load_email_config_from_dict(config_dict)

    assert config.smtp_hosts == ["smtp.test.com:587"]
    assert config.from_address == "alerts@test.com"
    assert config.smtp_username == "testuser"
    assert config.smtp_password == "testpass"
    assert config.use_starttls is False
    assert config.timeout == 120.0


@pytest.mark.os_agnostic
def test_load_config_merges_partial_config_with_defaults() -> None:
    """Partial config inherits defaults for unspecified values."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.partial.com"],
            "from_address": "partial@test.com",
        }
    }

    config = load_email_config_from_dict(config_dict)

    assert config.smtp_hosts == ["smtp.partial.com"]
    assert config.from_address == "partial@test.com"
    assert config.smtp_username is None
    assert config.use_starttls is True


@pytest.mark.os_agnostic
def test_load_config_rejects_non_dict_email_section() -> None:
    """Non-dict email section raises ValidationError."""
    config_dict = {"email": "invalid"}

    with pytest.raises(PydanticValidationError):
        load_email_config_from_dict(config_dict)


@pytest.mark.os_agnostic
def test_load_config_rejects_malformed_timeout() -> None:
    """Invalid timeout string raises ValidationError."""
    config_dict = {"email": {"timeout": "not_a_number"}}

    with pytest.raises(PydanticValidationError):
        load_email_config_from_dict(config_dict)


@pytest.mark.os_agnostic
def test_load_config_rejects_non_list_smtp_hosts() -> None:
    """String smtp_hosts raises ValidationError."""
    config_dict = {"email": {"smtp_hosts": "should_be_list"}}

    with pytest.raises(PydanticValidationError):
        load_email_config_from_dict(config_dict)


@pytest.mark.os_agnostic
def test_load_config_uses_default_for_string_boolean() -> None:
    """String boolean value falls back to default."""
    config_dict = {"email": {"use_starttls": "yes"}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.use_starttls is True


@pytest.mark.os_agnostic
def test_load_config_coerces_empty_from_address_to_none() -> None:
    """Empty string from_address is coerced to None."""
    config_dict = {"email": {"from_address": ""}}

    config = load_email_config_from_dict(config_dict)

    assert config.from_address is None


@pytest.mark.os_agnostic
def test_load_config_preserves_empty_string_username() -> None:
    """Empty string username is preserved (current behavior)."""
    config_dict = {"email": {"smtp_username": ""}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.smtp_username == ""


@pytest.mark.os_agnostic
def test_load_config_rejects_mixed_invalid_values() -> None:
    """Mixed valid/invalid config raises ValidationError for invalid fields."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "from_address": "test@example.com",
            "timeout": "invalid",
            "use_starttls": "maybe",
        }
    }

    with pytest.raises(PydanticValidationError):
        load_email_config_from_dict(config_dict)


# ======================== send_email ========================


@pytest.mark.os_agnostic
def test_send_email_delivers_simple_message() -> None:
    """Basic email with required fields is sent successfully."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_includes_html_body() -> None:
    """Email with both plain text and HTML is sent as multipart."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Plain text",
            body_html="<h1>HTML</h1>",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_accepts_multiple_recipients() -> None:
    """Email can be sent to multiple recipients at once."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients=["user1@test.com", "user2@test.com"],
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_allows_sender_override() -> None:
    """from_address parameter overrides config default."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="default@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
            from_address="override@test.com",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_includes_attachments(tmp_path: Path) -> None:
    """Email with file attachments is sent successfully."""
    attachment = tmp_path / "test.txt"
    attachment.write_text("Test attachment content")

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
            attachments=[attachment],
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_uses_credentials_when_provided() -> None:
    """SMTP credentials are used when configured."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        smtp_username="testuser",
        smtp_password="testpass",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


# ======================== send_notification ========================


@pytest.mark.os_agnostic
def test_send_notification_delivers_plain_text_message() -> None:
    """Notification sends plain-text email without HTML."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_notification(
            config=config,
            recipients="admin@test.com",
            subject="Alert",
            message="System notification",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_notification_accepts_multiple_recipients() -> None:
    """Notification can be sent to multiple recipients."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_notification(
            config=config,
            recipients=["admin1@test.com", "admin2@test.com"],
            subject="Alert",
            message="System notification",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_notification_forwards_from_address_override() -> None:
    """When from_address is provided, notification uses it instead of config default."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="default@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value
        result = send_notification(
            config=config,
            recipients="admin@test.com",
            subject="Alert",
            message="System notification",
            from_address="override@test.com",
        )

    assert result is True
    # Verify the overridden from_address was used in the SMTP sendmail call
    mock_instance.sendmail.assert_called_once()
    call_args = mock_instance.sendmail.call_args
    assert call_args[0][0] == "override@test.com"


# ======================== send_email — from_address validation ========================


@pytest.mark.os_agnostic
def test_send_email_raises_when_no_smtp_hosts() -> None:
    """Empty SMTP hosts list raises ValueError before attempting delivery."""
    config = EmailConfig(from_address="sender@test.com")
    with pytest.raises(ValueError, match="No SMTP hosts configured"):
        send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test",
            body="Hello",
        )


@pytest.mark.os_agnostic
def test_send_email_raises_when_no_recipients() -> None:
    """Empty recipients sequence raises ValueError before attempting delivery."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )
    with pytest.raises(ValueError, match="No recipients configured and no override provided"):
        send_email(
            config=config,
            recipients=[],
            subject="Test",
            body="Hello",
        )


@pytest.mark.os_agnostic
def test_send_email_raises_when_no_from_address() -> None:
    """Missing from_address in both config and override raises ValueError."""
    config = EmailConfig(smtp_hosts=["smtp.test.com:587"])

    with pytest.raises(ValueError, match="No from_address configured"):
        send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test",
            body="Hello",
        )


# ======================== Error Scenarios ========================


@pytest.mark.os_agnostic
def test_send_email_raises_when_smtp_connection_fails() -> None:
    """SMTP connection failure raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect to SMTP server")

        with pytest.raises(RuntimeError, match="failed.*on all of following hosts"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_authentication_fails() -> None:
    """SMTP authentication failure raises RuntimeError."""
    mock_instance = MagicMock()
    mock_instance.login.side_effect = Exception("Authentication failed")

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        smtp_username="user@test.com",
        smtp_password="wrong_password",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_instance

        with pytest.raises(RuntimeError, match="failed.*on all of following hosts"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_recipient_validation_fails() -> None:
    """Invalid recipient raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ValueError("Invalid recipient address")

        with pytest.raises(RuntimeError, match="following recipients failed"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_attachment_missing(tmp_path: Path) -> None:
    """Missing attachment raises FileNotFoundError when configured."""
    nonexistent = tmp_path / "nonexistent.txt"

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        raise_on_missing_attachments=True,
    )

    with patch("smtplib.SMTP"):
        with pytest.raises(FileNotFoundError):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
                attachments=[nonexistent],
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_all_smtp_hosts_fail() -> None:
    """All SMTP hosts failing raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp1.test.com:587", "smtp2.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Connection refused")

        with pytest.raises(RuntimeError, match="following recipients failed"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


# ======================== EmailConfig Recipients Defaults ========================


@pytest.mark.os_agnostic
def test_when_no_recipients_given_the_list_starts_empty() -> None:
    """Without recipients, the list begins empty and waiting."""
    assert EmailConfig().recipients == []


@pytest.mark.os_agnostic
def test_email_config_rejects_invalid_recipient_in_list() -> None:
    """Recipient without @ is caught early with clear error."""
    with pytest.raises(PydanticValidationError, match="invalid email address"):
        EmailConfig(recipients=["not-an-email"])


@pytest.mark.os_agnostic
def test_email_config_accepts_valid_recipients_list() -> None:
    """Valid recipient addresses are accepted."""
    config = EmailConfig(recipients=["admin@example.com", "ops@example.com"])
    assert config.recipients == ["admin@example.com", "ops@example.com"]


@pytest.mark.os_agnostic
def test_email_config_accepts_empty_recipients_list() -> None:
    """Empty recipients list is valid (not-configured sentinel)."""
    config = EmailConfig(recipients=[])
    assert config.recipients == []


# ======================== load_email_config_from_dict — recipients ========================


@pytest.mark.os_agnostic
def test_load_config_extracts_recipients_from_email_section() -> None:
    """Recipients are correctly extracted from config dict."""
    config_dict = {
        "email": {
            "recipients": ["admin@test.com", "ops@test.com"],
        }
    }

    config = load_email_config_from_dict(config_dict)

    assert config.recipients == ["admin@test.com", "ops@test.com"]


@pytest.mark.os_agnostic
def test_load_config_defaults_recipients_to_empty_list() -> None:
    """Missing recipients field defaults to empty list."""
    config_dict: dict[str, dict[str, object]] = {"email": {}}

    config = load_email_config_from_dict(config_dict)

    assert config.recipients == []


# ======================== send_email — recipients fallback ========================


@pytest.mark.os_agnostic
def test_send_email_uses_config_recipients_when_parameter_is_none() -> None:
    """When recipients parameter is None, config.recipients is used."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        recipients=["default@test.com"],
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_parameter_overrides_config_recipients() -> None:
    """When recipients parameter is provided, it replaces config recipients."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        recipients=["config@test.com"],
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="override@test.com",
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_raises_when_no_recipients_configured_and_none_provided() -> None:
    """Both config and parameter missing recipients raises ValueError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with pytest.raises(ValueError, match="No recipients configured and no override provided"):
        send_email(
            config=config,
            subject="Test",
            body="Hello",
        )


@pytest.mark.os_agnostic
def test_send_email_raises_when_config_recipients_empty_and_none_provided() -> None:
    """Explicit empty config recipients with None parameter raises ValueError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        recipients=[],
    )

    with pytest.raises(ValueError, match="No recipients configured and no override provided"):
        send_email(
            config=config,
            recipients=None,
            subject="Test",
            body="Hello",
        )


@pytest.mark.os_agnostic
def test_send_email_raises_when_parameter_is_empty_list() -> None:
    """Explicit empty list parameter raises ValueError even with config recipients."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        recipients=["config@test.com"],
    )

    with pytest.raises(ValueError, match="No recipients configured and no override provided"):
        send_email(
            config=config,
            recipients=[],
            subject="Test",
            body="Hello",
        )


# ======================== send_notification — recipients fallback ========================


@pytest.mark.os_agnostic
def test_send_notification_uses_config_recipients_when_parameter_is_none() -> None:
    """Notification falls back to config.recipients when parameter is None."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
        recipients=["admin@test.com"],
    )

    with patch("smtplib.SMTP"):
        result = send_notification(
            config=config,
            subject="Alert",
            message="System notification",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_notification_raises_when_no_recipients_anywhere() -> None:
    """Notification with no recipients in config or parameter raises ValueError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
    )

    with pytest.raises(ValueError, match="No recipients configured and no override provided"):
        send_notification(
            config=config,
            subject="Alert",
            message="System notification",
        )


# ======================== Real SMTP Integration ========================


@pytest.fixture
def smtp_config_from_env() -> EmailConfig:
    """Load SMTP configuration via lib_layered_config for integration tests."""
    from bitranox_template_py_cli.adapters.config.loader import get_config
    from bitranox_template_py_cli.adapters.email.sender import load_email_config_from_dict

    get_config.cache_clear()
    config = get_config()
    email_config = load_email_config_from_dict(config.as_dict())

    if not email_config.smtp_hosts or not email_config.from_address:
        pytest.skip("Email not configured (no smtp_hosts or from_address in layered config)")

    return email_config


@pytest.mark.slow
@pytest.mark.os_agnostic
def test_real_smtp_sends_email(smtp_config_from_env: EmailConfig) -> None:
    """Integration: send real email via configured SMTP server."""
    result = send_email(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.recipients,
        subject="Test Email from bitranox_template_py_cli",
        body="This is a test email sent from the integration test suite.\n\nIf you receive this, the email functionality is working correctly.",
    )

    assert result is True


@pytest.mark.slow
@pytest.mark.os_agnostic
def test_real_smtp_sends_html_email(smtp_config_from_env: EmailConfig) -> None:
    """Integration: send HTML email via configured SMTP server."""
    result = send_email(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.recipients,
        subject="Test HTML Email from bitranox_template_py_cli",
        body="This is the plain text version.",
        body_html="<html><body><h1>Test Email</h1><p>This is a <strong>HTML</strong> test email.</p></body></html>",
    )

    assert result is True


@pytest.mark.slow
@pytest.mark.os_agnostic
def test_real_smtp_sends_notification(smtp_config_from_env: EmailConfig) -> None:
    """Integration: send notification via configured SMTP server."""
    result = send_notification(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.recipients,
        subject="Test Notification from bitranox_template_py_cli",
        message="This is a test notification.\n\nSystem: All tests passing!",
    )

    assert result is True
