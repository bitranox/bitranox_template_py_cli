"""In-memory email adapters for testing.

Provides email functions that satisfy the same Protocols as production
adapters but perform no SMTP operations.

Contents:
    * :class:`EmailSpy` - Captures email calls for test assertions.
    * :func:`get_email_spy` - Access the global spy instance.
    * :func:`send_email_in_memory` - In-memory send_email implementation.
    * :func:`send_notification_in_memory` - In-memory send_notification implementation.
    * :func:`load_email_config_from_dict_in_memory` - In-memory config loader.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..email.sender import EmailConfig


def _empty_email_list() -> list[dict[str, Any]]:
    """Create an empty typed list for email records."""
    return []


@dataclass
class EmailSpy:
    """Captures email operations for test assertions.

    Attributes:
        sent_emails: List of captured send_email calls.
        sent_notifications: List of captured send_notification calls.
        should_fail: When True, send operations return False to simulate failure.
        raise_exception: When set, send operations raise this exception.
    """

    sent_emails: list[dict[str, Any]] = field(default_factory=_empty_email_list)
    sent_notifications: list[dict[str, Any]] = field(default_factory=_empty_email_list)
    should_fail: bool = False
    raise_exception: Exception | None = None

    def clear(self) -> None:
        """Reset captured data for next test."""
        self.sent_emails.clear()
        self.sent_notifications.clear()
        self.raise_exception = None


_spy = EmailSpy()


def get_email_spy() -> EmailSpy:
    """Return the global email spy instance for test assertions."""
    return _spy


def send_email_in_memory(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    body: str = "",
    body_html: str = "",
    from_address: str | None = None,
    attachments: Sequence[Path] | None = None,
) -> bool:
    """Record the call and return success/failure based on spy state."""
    _spy.sent_emails.append(
        {
            "config": config,
            "recipients": recipients,
            "subject": subject,
            "body": body,
            "body_html": body_html,
            "from_address": from_address,
            "attachments": list(attachments) if attachments else None,
        }
    )
    if _spy.raise_exception is not None:
        raise _spy.raise_exception
    return not _spy.should_fail


def send_notification_in_memory(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    message: str,
    from_address: str | None = None,
) -> bool:
    """Record the call and return success/failure based on spy state."""
    _spy.sent_notifications.append(
        {
            "config": config,
            "recipients": recipients,
            "subject": subject,
            "message": message,
            "from_address": from_address,
        }
    )
    if _spy.raise_exception is not None:
        raise _spy.raise_exception
    return not _spy.should_fail


def load_email_config_from_dict_in_memory(
    config_dict: Mapping[str, Any],
) -> EmailConfig:
    """Parse email config from dict using the real Pydantic model."""
    email_raw = config_dict.get("email", {})
    return EmailConfig.model_validate(email_raw if email_raw else {})


__all__ = [
    "EmailSpy",
    "get_email_spy",
    "load_email_config_from_dict_in_memory",
    "send_email_in_memory",
    "send_notification_in_memory",
]
