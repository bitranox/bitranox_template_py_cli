"""In-memory email adapters for testing.

Provides email functions that satisfy the same Protocols as production
adapters but perform no SMTP operations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..email.sender import EmailConfig


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
    """Return True without sending -- satisfies the SendEmail protocol."""
    return True


def send_notification_in_memory(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    message: str,
    from_address: str | None = None,
) -> bool:
    """Return True without sending -- satisfies the SendNotification protocol."""
    return True


def load_email_config_from_dict_in_memory(
    config_dict: Mapping[str, Any],
) -> EmailConfig:
    """Parse email config from dict using the real Pydantic model."""
    email_raw = config_dict.get("email", {})
    return EmailConfig.model_validate(email_raw if email_raw else {})


__all__ = [
    "load_email_config_from_dict_in_memory",
    "send_email_in_memory",
    "send_notification_in_memory",
]
