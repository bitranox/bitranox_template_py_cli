"""Email adapter - SMTP email sending.

Provides the email sending adapter using btx_lib_mail.

Contents:
    * :class:`.sender.EmailConfig` - Email configuration container
    * :func:`.sender.send_email` - Primary email sending interface
    * :func:`.sender.send_notification` - Simple notification wrapper
    * :func:`.sender.load_email_config_from_dict` - Config dict loader
"""

from __future__ import annotations

from .sender import (
    EmailConfig,
    send_email,
    send_notification,
    load_email_config_from_dict,
)

__all__ = [
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
]
