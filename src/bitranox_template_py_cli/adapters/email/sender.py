"""Email sending adapter wrapping btx_lib_mail with typed configuration."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from btx_lib_mail import validate_email_address, validate_smtp_host
from btx_lib_mail.lib_mail import ConfMail
from btx_lib_mail.lib_mail import send as btx_send
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bitranox_template_py_cli.domain.errors import ConfigurationError, DeliveryError

from .validation import validate_recipients

logger = logging.getLogger(__name__)

# Keywords that may indicate sensitive data in exception messages
_SENSITIVE_KEYWORDS = frozenset(
    {
        "password",
        "credential",
        "auth",
        "secret",
        "token",
        "key",
        "login",
    }
)


def _sanitize_exception_message(exc: Exception) -> str:
    """Sanitize exception message to prevent credential exposure.

    Returns a generic message when the original exception text contains
    keywords suggesting sensitive data (passwords, credentials, tokens).
    The full exception is preserved in the chain for DEBUG-level logging.

    Args:
        exc: The exception to sanitize.

    Returns:
        Sanitized message safe for user display.

    Example:
        >>> class FakeExc(Exception): pass
        >>> _sanitize_exception_message(FakeExc("Connection failed"))
        'Connection failed'
        >>> _sanitize_exception_message(FakeExc("Auth password rejected"))
        'Email delivery failed. Check SMTP configuration.'
    """
    message = str(exc).lower()
    if any(keyword in message for keyword in _SENSITIVE_KEYWORDS):
        return "Email delivery failed. Check SMTP configuration."
    return str(exc)


class EmailConfig(BaseModel):
    """Validated, immutable email configuration.

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

    # Attachment security settings (None = use btx_lib_mail defaults)
    attachment_allowed_extensions: frozenset[str] | None = None
    attachment_blocked_extensions: frozenset[str] | None = None
    attachment_allowed_directories: frozenset[Path] | None = None
    attachment_blocked_directories: frozenset[Path] | None = None
    attachment_max_size_bytes: int | None = 26_214_400  # 25 MiB
    attachment_allow_symlinks: bool = False
    attachment_raise_on_security_violation: bool = True

    @field_validator("smtp_hosts", "recipients", mode="before")
    @classmethod
    def _coerce_string_to_list(cls, v: Any) -> list[str]:
        """Coerce single strings to single-element lists.

        Handles environment variables and .env files that provide single strings
        instead of TOML arrays. Empty strings become empty lists.

        Examples:
            >>> EmailConfig._coerce_string_to_list("smtp.example.com:587")
            ['smtp.example.com:587']
            >>> EmailConfig._coerce_string_to_list(["a@example.com", "b@example.com"])
            ['a@example.com', 'b@example.com']
            >>> EmailConfig._coerce_string_to_list("")
            []
        """
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return cast(list[str], v)
        return []

    @field_validator("from_address", "smtp_username", "smtp_password", mode="before")
    @classmethod
    def _coerce_empty_string_to_none(cls, v: str | None) -> str | None:
        """Coerce empty or whitespace-only strings to None.

        Treats empty strings from config files as "not configured" rather than
        explicit empty values. This prevents accidental auth attempts with
        empty credentials and ensures consistent "not set" semantics.

        Applies to: from_address, smtp_username, smtp_password.
        """
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator(
        "attachment_allowed_extensions",
        "attachment_blocked_extensions",
        mode="before",
    )
    @classmethod
    def _coerce_extension_lists(cls, v: Any) -> frozenset[str] | None:
        """Convert lists to frozensets, empty lists to None (use library defaults).

        Frozensets are preserved as-is (including empty ones) to allow explicit
        override from Python code. Empty lists from TOML config become None.
        """
        if v is None:
            return None
        if isinstance(v, frozenset):
            # Preserve frozensets as-is (allows explicit empty frozenset to disable)
            return cast(frozenset[str], v)
        if isinstance(v, list):
            # Empty list from config = use library defaults
            ext_list = cast(list[str], v)
            return frozenset(ext_list) if ext_list else None
        return None  # Unsupported type, let Pydantic handle validation error

    @field_validator(
        "attachment_allowed_directories",
        "attachment_blocked_directories",
        mode="before",
    )
    @classmethod
    def _coerce_directory_lists(cls, v: Any) -> frozenset[Path] | None:
        """Convert lists of strings/paths to frozenset[Path], empty lists to None.

        Frozensets are preserved as-is (including empty ones) to allow explicit
        override from Python code. Empty lists from TOML config become None.
        """
        if v is None:
            return None
        if isinstance(v, frozenset):
            # Preserve frozensets as-is (allows explicit empty frozenset to disable)
            return cast(frozenset[Path], v)
        if isinstance(v, list):
            # Empty list from config = use library defaults
            dir_list = cast(list[str | Path], v)
            if not dir_list:
                return None
            return frozenset(Path(p) if isinstance(p, str) else p for p in dir_list)
        return None  # Unsupported type, let Pydantic handle validation error

    @field_validator("attachment_max_size_bytes", mode="before")
    @classmethod
    def _coerce_max_size_zero_to_none(cls, v: Any) -> int | None:
        """Convert 0 to None (disable size checking)."""
        if v == 0:
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

    def __repr__(self) -> str:
        """Return string representation with smtp_password redacted.

        Prevents accidental credential exposure in logs, error messages,
        and debugging output. The password is shown as '[REDACTED]' when set.

        Example:
            >>> config = EmailConfig(
            ...     smtp_hosts=["smtp.example.com:587"],
            ...     smtp_password="secret123"
            ... )
            >>> "secret123" in repr(config)
            False
            >>> "[REDACTED]" in repr(config)
            True
        """
        fields: list[str] = []
        for name, value in self:
            if name == "smtp_password" and value is not None:
                fields.append(f"{name}='[REDACTED]'")
            else:
                fields.append(f"{name}={value!r}")
        return f"EmailConfig({', '.join(fields)})"

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
        # Build kwargs, omitting None values to use library defaults
        kwargs: dict[str, Any] = {
            "smtphosts": self.smtp_hosts,
            "smtp_username": self.smtp_username,
            "smtp_password": self.smtp_password,
            "smtp_use_starttls": self.use_starttls,
            "smtp_timeout": self.timeout,
            "raise_on_missing_attachments": self.raise_on_missing_attachments,
            "raise_on_invalid_recipient": self.raise_on_invalid_recipient,
            "attachment_allow_symlinks": self.attachment_allow_symlinks,
            "attachment_raise_on_security_violation": self.attachment_raise_on_security_violation,
        }

        # Only pass attachment security settings when explicitly configured
        # (None = use btx_lib_mail's OS-specific defaults)
        if self.attachment_allowed_extensions is not None:
            kwargs["attachment_allowed_extensions"] = self.attachment_allowed_extensions
        if self.attachment_blocked_extensions is not None:
            kwargs["attachment_blocked_extensions"] = self.attachment_blocked_extensions
        if self.attachment_allowed_directories is not None:
            kwargs["attachment_allowed_directories"] = self.attachment_allowed_directories
        if self.attachment_blocked_directories is not None:
            kwargs["attachment_blocked_directories"] = self.attachment_blocked_directories
        if self.attachment_max_size_bytes is not None:
            kwargs["attachment_max_size_bytes"] = self.attachment_max_size_bytes

        return ConfMail(**kwargs)


def _build_credentials(config: EmailConfig) -> tuple[str, str] | None:
    """Return (username, password) tuple when both are set, else None."""
    if config.smtp_username is not None and config.smtp_password is not None:
        return (config.smtp_username, config.smtp_password)
    return None


def _resolve_sender(config: EmailConfig, from_address: str | None) -> str:
    """Determine the sender address from override or config default.

    Args:
        config: Email configuration with optional default from_address.
        from_address: Explicit override, or None to use config default.

    Returns:
        Resolved sender address.

    Raises:
        ValueError: When neither override nor config provides a from_address.
    """
    sender = from_address if from_address is not None else config.from_address
    if sender is None:
        raise ValueError("No from_address configured and no override provided")
    return sender


def _resolve_recipients(
    config: EmailConfig,
    recipients: str | Sequence[str] | None,
) -> list[str]:
    """Normalize recipients from override or config default.

    Args:
        config: Email configuration with optional default recipients.
        recipients: Single address, sequence of addresses, or None for config default.

    Returns:
        Non-empty list of recipient addresses.

    Raises:
        ValueError: When no recipients are available from either source.
        InvalidRecipientError: When a runtime recipient has invalid email format.
    """
    if recipients is not None:
        recipient_list = [recipients] if isinstance(recipients, str) else list(recipients)
        # Validate runtime recipients (config recipients validated by Pydantic)
        validate_recipients(recipient_list)
    else:
        recipient_list = list(config.recipients)

    if not recipient_list:
        raise ValueError("No recipients configured and no override provided")
    return recipient_list


def _validate_smtp_hosts(config: EmailConfig) -> None:
    """Ensure at least one SMTP host is configured.

    Args:
        config: Email configuration to validate.

    Raises:
        ConfigurationError: When smtp_hosts is empty.
    """
    if not config.smtp_hosts:
        raise ConfigurationError("No SMTP hosts configured (email.smtp_hosts is empty)")


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
        True when delivery succeeds; False if the underlying transport
        reports partial failure without raising. Most failures raise
        exceptions rather than returning False.

    Raises:
        ValueError: No from_address configured and no override provided,
            or no recipients configured and no override provided.
        ConfigurationError: No SMTP hosts configured.
        FileNotFoundError: Required attachment missing and config.raise_on_missing_attachments
            is True.
        DeliveryError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts at INFO level and failures
        at ERROR level.
    """
    sender = _resolve_sender(config, from_address)
    _validate_smtp_hosts(config)
    recipient_list = _resolve_recipients(config, recipients)

    logger.info(
        "Sending email",
        extra={
            "sender": sender,
            "recipients": recipient_list,
            "subject": subject,
            "has_html": bool(body_html),
            "attachment_count": len(attachments) if attachments else 0,
        },
    )

    try:
        result = btx_send(
            mail_from=sender,
            mail_recipients=recipient_list,
            mail_subject=subject,
            mail_body=body,
            mail_body_html=body_html,
            smtphosts=config.smtp_hosts,
            attachment_file_paths=attachments,
            credentials=_build_credentials(config),
            use_starttls=config.use_starttls,
            timeout=config.timeout,
            attachment_allowed_extensions=config.attachment_allowed_extensions,
            attachment_blocked_extensions=config.attachment_blocked_extensions,
            attachment_allowed_directories=config.attachment_allowed_directories,
            attachment_blocked_directories=config.attachment_blocked_directories,
            attachment_max_size_bytes=config.attachment_max_size_bytes,
            attachment_allow_symlinks=config.attachment_allow_symlinks,
            attachment_raise_on_security_violation=config.attachment_raise_on_security_violation,
            raise_on_missing_attachments=config.raise_on_missing_attachments,
            raise_on_invalid_recipient=config.raise_on_invalid_recipient,
        )
    except RuntimeError as exc:
        logger.debug("SMTP delivery failed", exc_info=True)
        raise DeliveryError(_sanitize_exception_message(exc)) from exc

    if result:
        logger.info(
            "Email sent successfully",
            extra={"sender": sender, "recipients": recipient_list},
        )
    else:
        logger.warning(
            "Email send returned failure",
            extra={"sender": sender, "recipients": recipient_list},
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
        True when delivery succeeds; False if the underlying transport
        reports partial failure without raising.

    Raises:
        ValueError: No recipients configured and no override provided.
        ConfigurationError: No SMTP hosts configured.
        DeliveryError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts.
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

    Handles the nested `[email.attachments]` TOML section by flattening
    it with an `attachment_` prefix to match EmailConfig field names.

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

        >>> config_dict_with_attachments = {
        ...     "email": {
        ...         "smtp_hosts": ["smtp.example.com:587"],
        ...         "attachments": {
        ...             "max_size_bytes": 10485760,
        ...             "allow_symlinks": True,
        ...         }
        ...     }
        ... }
        >>> config = load_email_config_from_dict(config_dict_with_attachments)
        >>> config.attachment_max_size_bytes
        10485760
        >>> config.attachment_allow_symlinks
        True
    """
    email_section: Any = config_dict.get("email", {})

    # Handle non-dict email section (e.g. "email": "invalid")
    if not isinstance(email_section, Mapping):
        return EmailConfig.model_validate(email_section)

    email_raw: dict[str, Any] = dict(cast(Mapping[str, Any], email_section))

    # Flatten nested [email.attachments] section with prefix
    attachments_raw: dict[str, Any] = email_raw.pop("attachments", {})
    for key, value in attachments_raw.items():
        email_raw[f"attachment_{key}"] = value

    return EmailConfig.model_validate(email_raw if email_raw else {})


__all__ = [
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
]
