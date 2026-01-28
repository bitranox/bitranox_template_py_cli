"""Email sending adapter using btx_lib_mail.

Provides a clean wrapper around btx_lib_mail that integrates with the
application's configuration system and logging infrastructure. Isolates
email functionality behind a domain-appropriate interface.

Contents:
    * :class:`EmailConfig` – Pydantic configuration model for email settings
    * :func:`send_email` – Primary email sending interface
    * :func:`send_notification` – Convenience wrapper for simple notifications

System Role:
    Acts as the email adapter layer, bridging btx_lib_mail with the application's
    configuration and logging systems while keeping domain logic decoupled from
    email mechanics.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Sequence

from btx_lib_mail import validate_email_address, validate_smtp_host
from btx_lib_mail.lib_mail import ConfMail, send as btx_send
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class EmailConfig(BaseModel):
    """Email configuration container.

    Pydantic model providing validated, immutable email configuration. Serves as
    both the boundary validation model (parsing config dicts) and the internal
    typed configuration object, eliminating conversion chains.

    Attributes:
        smtp_hosts: List of SMTP servers in 'host[:port]' format. Tried in order until
            one succeeds.
        from_address: Default sender address for outgoing emails, or None if not configured.
        recipients: Default recipient addresses, or empty list if not configured.
        smtp_username: Optional SMTP authentication username.
        smtp_password: Optional SMTP authentication password.
        use_starttls: Enable STARTTLS negotiation.
        timeout: Socket timeout in seconds for SMTP operations.
        raise_on_missing_attachments: When True, missing attachment files raise FileNotFoundError.
        raise_on_invalid_recipient: When True, invalid email addresses raise ValueError.

    Example:
        >>> config = EmailConfig(
        ...     smtp_hosts=["smtp.example.com:587"],
        ...     from_address="noreply@example.com"
        ... )
        >>> config.smtp_hosts
        ['smtp.example.com:587']
    """

    model_config = ConfigDict(frozen=True)

    smtp_hosts: list[str] = Field(default_factory=list)
    from_address: str | None = None
    recipients: list[str] = Field(default_factory=list)
    smtp_username: str | None = None
    smtp_password: str | None = None
    use_starttls: bool = True
    timeout: float = 30.0
    raise_on_missing_attachments: bool = True
    raise_on_invalid_recipient: bool = True

    @field_validator("from_address", mode="before")
    @classmethod
    def _coerce_empty_from_address(cls, v: str | None) -> str | None:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def _validate_config(self) -> EmailConfig:
        """Validate configuration values.

        Catch common configuration mistakes early with clear error messages
        rather than allowing invalid values to cause obscure failures later.

        Raises:
            ValueError: When configuration values are invalid.

        Example:
            >>> EmailConfig(timeout=-5.0)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            ValidationError: ...

            >>> EmailConfig(from_address="not-an-email")  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            ValidationError: ...
        """
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")

        if self.from_address is not None:
            validate_email_address(self.from_address)

        for recipient in self.recipients:
            validate_email_address(recipient)

        for host in self.smtp_hosts:
            validate_smtp_host(host)

        return self

    def to_conf_mail(self) -> ConfMail:
        """Convert to btx_lib_mail ConfMail object.

        Isolates the adapter dependency on btx_lib_mail types from the
        rest of the application.

        Returns:
            ConfMail instance configured with current settings.

        Example:
            >>> config = EmailConfig(smtp_hosts=["smtp.example.com"])
            >>> conf = config.to_conf_mail()
            >>> conf.smtphosts
            ['smtp.example.com']
        """
        return ConfMail(
            smtphosts=self.smtp_hosts,
            smtp_username=self.smtp_username,
            smtp_password=self.smtp_password,
            smtp_use_starttls=self.use_starttls,
            smtp_timeout=self.timeout,
            raise_on_missing_attachments=self.raise_on_missing_attachments,
            raise_on_invalid_recipient=self.raise_on_invalid_recipient,
        )


def _build_credentials(config: EmailConfig) -> tuple[str, str] | None:
    """Extract SMTP credentials from config when both username and password are set."""
    if config.smtp_username is not None and config.smtp_password is not None:
        return (config.smtp_username, config.smtp_password)
    return None


def send_email(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    body: str = "",
    body_html: str = "",
    from_address: str | None = None,
    attachments: Sequence[Path] | None = None,
) -> bool:
    """Send an email using configured SMTP settings.

    Provides the primary email-sending interface that integrates with
    application configuration while exposing a clean, typed API.

    Args:
        config: Email configuration containing SMTP settings and defaults.
        recipients: Single recipient address, sequence of addresses, or None to use
            config.recipients. When provided, replaces config recipients entirely.
        subject: Email subject line (UTF-8 supported).
        body: Plain-text email body.
        body_html: HTML email body (optional, sent as multipart with plain text).
        from_address: Override sender address. Uses config.from_address when None.
        attachments: Optional sequence of file paths to attach.

    Returns:
        Always True when delivery succeeds. Failures raise exceptions.

    Raises:
        ValueError: No from_address configured and no override provided,
            no SMTP hosts configured, or no recipients configured and no override
            provided.
        FileNotFoundError: Required attachment missing and config.raise_on_missing_attachments
            is True.
        RuntimeError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts at INFO level and failures
        at ERROR level.

    Example:
        >>> from unittest.mock import patch, MagicMock
        >>> config = EmailConfig(
        ...     smtp_hosts=["smtp.example.com"],
        ...     from_address="sender@example.com"
        ... )
        >>> with patch("smtplib.SMTP") as mock_smtp:
        ...     result = send_email(
        ...         config=config,
        ...         recipients="recipient@example.com",
        ...         subject="Test",
        ...         body="Hello"
        ...     )
        >>> result
        True
    """
    sender = from_address if from_address is not None else config.from_address
    if sender is None:
        raise ValueError("No from_address configured and no override provided")

    if not config.smtp_hosts:
        raise ValueError("No SMTP hosts configured (email.smtp_hosts is empty)")

    if recipients is not None:
        recipient_list = [recipients] if isinstance(recipients, str) else list(recipients)
    else:
        recipient_list = list(config.recipients)

    if not recipient_list:
        raise ValueError("No recipients configured and no override provided")

    logger.info(
        "Sending email",
        extra={
            "from": sender,
            "recipients": recipient_list,
            "subject": subject,
            "has_html": bool(body_html),
            "attachment_count": len(attachments) if attachments else 0,
        },
    )

    credentials = _build_credentials(config)

    result = btx_send(
        mail_from=sender,
        mail_recipients=recipient_list,
        mail_subject=subject,
        mail_body=body,
        mail_body_html=body_html,
        smtphosts=config.smtp_hosts,
        attachment_file_paths=attachments,
        credentials=credentials,
        use_starttls=config.use_starttls,
        timeout=config.timeout,
    )

    logger.info(
        "Email sent successfully",
        extra={
            "from": sender,
            "recipients": recipient_list,
        },
    )

    return result


def send_notification(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    message: str,
    from_address: str | None = None,
) -> bool:
    """Send a simple plain-text notification email.

    Convenience wrapper for the common case of sending simple notifications
    without HTML or attachments.

    Args:
        config: Email configuration containing SMTP settings.
        recipients: Single recipient address, sequence of addresses, or None to use
            config.recipients. When provided, replaces config recipients entirely.
        subject: Email subject line.
        message: Plain-text notification message.
        from_address: Override sender address. Uses config.from_address when None.

    Returns:
        Always True when delivery succeeds. Failures raise exceptions.

    Raises:
        ValueError: No recipients configured and no override provided.
        RuntimeError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts.

    Example:
        >>> from unittest.mock import patch
        >>> config = EmailConfig(
        ...     smtp_hosts=["smtp.example.com"],
        ...     from_address="alerts@example.com"
        ... )
        >>> with patch("smtplib.SMTP"):
        ...     result = send_notification(
        ...         config=config,
        ...         recipients="admin@example.com",
        ...         subject="System Alert",
        ...         message="Deployment completed successfully"
        ...     )
        >>> result
        True
    """
    return send_email(
        config=config,
        recipients=recipients,
        subject=subject,
        body=message,
        from_address=from_address,
    )


def load_email_config_from_dict(config_dict: Mapping[str, Any]) -> EmailConfig:
    """Load EmailConfig from a configuration dictionary.

    Bridges lib_layered_config's dictionary output with the typed
    EmailConfig Pydantic model. Single-parse validation at the boundary
    with no intermediate conversions.

    Args:
        config_dict: Configuration dictionary typically from lib_layered_config.
            Expected to have an 'email' section with email settings.

    Returns:
        Configured email settings with defaults for missing values.

    Example:
        >>> config_dict = {
        ...     "email": {
        ...         "smtp_hosts": ["smtp.example.com:587"],
        ...         "from_address": "test@example.com"
        ...     }
        ... }
        >>> email_config = load_email_config_from_dict(config_dict)
        >>> email_config.from_address
        'test@example.com'
        >>> email_config.use_starttls
        True
    """
    email_raw = config_dict.get("email", {})
    return EmailConfig.model_validate(email_raw if email_raw else {})


__all__ = [
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
]
