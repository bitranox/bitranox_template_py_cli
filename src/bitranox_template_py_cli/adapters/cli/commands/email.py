"""Email sending CLI commands.

Provides commands for sending emails and notifications via SMTP.

Contents:
    * :class:`SmtpConfigOverrides` - Parameter object for SMTP CLI overrides.
    * :func:`cli_send_email` - Send email with optional HTML and attachments.
    * :func:`cli_send_notification` - Send simple plain-text notification.
"""

from __future__ import annotations

import dataclasses
import functools
import logging
from pathlib import Path
from typing import Any

import rich_click as click
import lib_log_rich.runtime
from lib_layered_config import Config

from .... import __init__conf__
from ....adapters.email.sender import EmailConfig, load_email_config_from_dict, send_email, send_notification
from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import get_cli_context
from ..exit_codes import ExitCode

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True)
class SmtpConfigOverrides:
    """Parameter object for SMTP CLI overrides.

    Encapsulates the optional overrides that CLI flags can apply on top of
    the base :class:`EmailConfig` loaded from config files.  Fields left at
    their sentinel value (empty tuple / ``None``) are not applied.

    Attributes:
        smtp_hosts: Override SMTP hosts (empty tuple means "keep config value").
        smtp_username: Override SMTP username.
        smtp_password: Override SMTP password.
        use_starttls: Override STARTTLS setting.
        timeout: Override socket timeout.
        raise_on_missing_attachments: Override missing-attachment handling.
        raise_on_invalid_recipient: Override invalid-recipient handling.
    """

    smtp_hosts: tuple[str, ...] = ()
    smtp_username: str | None = None
    smtp_password: str | None = None
    use_starttls: bool | None = None
    timeout: float | None = None
    raise_on_missing_attachments: bool | None = None
    raise_on_invalid_recipient: bool | None = None

    def apply_to(self, config: EmailConfig) -> EmailConfig:
        """Return a new :class:`EmailConfig` with non-sentinel fields replaced.

        Args:
            config: Base email configuration loaded from config files.

        Returns:
            A new EmailConfig with overrides applied, or the same instance
            when no overrides are set.
        """
        overrides: dict[str, Any] = {}
        if self.smtp_hosts:
            overrides["smtp_hosts"] = list(self.smtp_hosts)
        if self.smtp_username is not None:
            overrides["smtp_username"] = self.smtp_username
        if self.smtp_password is not None:
            overrides["smtp_password"] = self.smtp_password
        if self.use_starttls is not None:
            overrides["use_starttls"] = self.use_starttls
        if self.timeout is not None:
            overrides["timeout"] = self.timeout
        if self.raise_on_missing_attachments is not None:
            overrides["raise_on_missing_attachments"] = self.raise_on_missing_attachments
        if self.raise_on_invalid_recipient is not None:
            overrides["raise_on_invalid_recipient"] = self.raise_on_invalid_recipient
        if not overrides:
            return config
        return config.model_copy(update=overrides)


def _smtp_config_options(func: Any) -> Any:
    """Apply shared SMTP configuration override options to a Click command.

    Adds CLI flags for all EmailConfig fields so that any TOML setting
    can be overridden at invocation time.
    """
    options = [
        click.option("--smtp-host", "smtp_hosts", multiple=True, default=(), help="Override SMTP host (can specify multiple; format host:port)"),
        click.option("--smtp-username", default=None, help="Override SMTP authentication username"),
        click.option("--smtp-password", default=None, help="Override SMTP authentication password"),
        click.option("--use-starttls/--no-use-starttls", default=None, help="Override STARTTLS setting"),
        click.option("--timeout", "timeout", type=float, default=None, help="Override socket timeout in seconds"),
        click.option(
            "--raise-on-missing-attachments/--no-raise-on-missing-attachments",
            default=None,
            help="Override missing attachment handling",
        ),
        click.option(
            "--raise-on-invalid-recipient/--no-raise-on-invalid-recipient",
            default=None,
            help="Override invalid recipient handling",
        ),
    ]
    return functools.reduce(lambda f, opt: opt(f), reversed(options), func)


@click.command("send-email", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--to", "recipients", multiple=True, required=False, help="Recipient email address (can specify multiple; uses config default if not specified)")
@click.option("--subject", required=True, help="Email subject line")
@click.option("--body", default="", help="Plain-text email body")
@click.option("--body-html", default="", help="HTML email body (sent as multipart with plain text)")
@click.option("--from", "from_address", default=None, help="Override sender address (uses config default if not specified)")
@click.option(
    "--attachment",
    "attachments",
    multiple=True,
    type=click.Path(exists=True, path_type=str),
    help="File to attach (can specify multiple)",
)
@_smtp_config_options
@click.pass_context
def cli_send_email(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    body: str,
    body_html: str,
    from_address: str | None,
    attachments: tuple[str, ...],
    smtp_hosts: tuple[str, ...],
    smtp_username: str | None,
    smtp_password: str | None,
    use_starttls: bool | None,
    timeout: float | None,
    raise_on_missing_attachments: bool | None,
    raise_on_invalid_recipient: bool | None,
) -> None:
    """Send an email using configured SMTP settings.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli.py
    """
    cli_ctx = get_cli_context(ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-email", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-email", extra=extra):
        email_config = _load_and_validate_email_config(cli_ctx.config)
        smtp_overrides = SmtpConfigOverrides(
            smtp_hosts=smtp_hosts,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_starttls=use_starttls,
            timeout=timeout,
            raise_on_missing_attachments=raise_on_missing_attachments,
            raise_on_invalid_recipient=raise_on_invalid_recipient,
        )
        email_config = smtp_overrides.apply_to(email_config)
        attachment_paths = [Path(p) for p in attachments] if attachments else None

        _log_send_email_start(resolved_recipients, subject, body_html, attachments)
        _execute_send_email(email_config, resolved_recipients, subject, body, body_html, from_address, attachment_paths)


def _log_send_email_start(
    recipients: list[str] | None,
    subject: str,
    body_html: str,
    attachments: tuple[str, ...],
) -> None:
    """Log the start of an email send operation.

    Args:
        recipients: Email recipients, or None when using config defaults.
        subject: Email subject.
        body_html: HTML body content.
        attachments: Attachment file paths.
    """
    logger.info(
        "Sending email",
        extra={
            "recipients": recipients,
            "subject": subject,
            "has_html": bool(body_html),
            "attachment_count": len(attachments) if attachments else 0,
        },
    )


def _execute_send_email(
    email_config: EmailConfig,
    recipients: list[str] | None,
    subject: str,
    body: str,
    body_html: str,
    from_address: str | None,
    attachments: list[Path] | None,
) -> None:
    """Execute the email send operation with error handling.

    Args:
        email_config: Validated email configuration.
        recipients: Email recipients, or None when using config defaults.
        subject: Email subject.
        body: Plain text body.
        body_html: HTML body.
        from_address: Optional sender override.
        attachments: Optional attachment paths.

    Raises:
        SystemExit: On any error.
    """
    try:
        result = send_email(
            config=email_config,
            recipients=recipients,
            subject=subject,
            body=body,
            body_html=body_html,
            from_address=from_address,
            attachments=attachments,
        )
        _handle_send_result(result, recipients, "Email")
    except ValueError as exc:
        _handle_send_error(exc, "Invalid email parameters", "Invalid email parameters", exit_code=ExitCode.INVALID_ARGUMENT)
    except FileNotFoundError as exc:
        # Click validates exists=True at parse time; this catches TOCTOU races
        # where a file is deleted between argument parsing and send_email().
        _handle_send_error(exc, "Attachment file not found", "Attachment file not found", exit_code=ExitCode.FILE_NOT_FOUND)
    except RuntimeError as exc:
        _handle_send_error(exc, "SMTP delivery failed", "Failed to send email", exit_code=ExitCode.SMTP_FAILURE)
    except Exception as exc:
        _handle_send_error(exc, "Unexpected error sending email", "Unexpected error", exit_code=ExitCode.GENERAL_ERROR, log_traceback=True)


@click.command("send-notification", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--to", "recipients", multiple=True, required=False, help="Recipient email address (can specify multiple; uses config default if not specified)")
@click.option("--subject", required=True, help="Notification subject line")
@click.option("--message", required=True, help="Notification message (plain text)")
@click.option("--from", "from_address", default=None, help="Override sender address (uses config default if not specified)")
@_smtp_config_options
@click.pass_context
def cli_send_notification(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    message: str,
    from_address: str | None,
    smtp_hosts: tuple[str, ...],
    smtp_username: str | None,
    smtp_password: str | None,
    use_starttls: bool | None,
    timeout: float | None,
    raise_on_missing_attachments: bool | None,
    raise_on_invalid_recipient: bool | None,
) -> None:
    """Send a simple plain-text notification email.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli.py
    """
    cli_ctx = get_cli_context(ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-notification", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-notification", extra=extra):
        email_config = _load_and_validate_email_config(cli_ctx.config)
        smtp_overrides = SmtpConfigOverrides(
            smtp_hosts=smtp_hosts,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_starttls=use_starttls,
            timeout=timeout,
            raise_on_missing_attachments=raise_on_missing_attachments,
            raise_on_invalid_recipient=raise_on_invalid_recipient,
        )
        email_config = smtp_overrides.apply_to(email_config)
        logger.info("Sending notification", extra={"recipients": resolved_recipients, "subject": subject})
        _execute_send_notification(email_config, resolved_recipients, subject, message, from_address)


def _execute_send_notification(
    email_config: EmailConfig,
    recipients: list[str] | None,
    subject: str,
    message: str,
    from_address: str | None = None,
) -> None:
    """Execute the notification send operation with error handling.

    Args:
        email_config: Validated email configuration.
        recipients: Email recipients, or None when using config defaults.
        subject: Notification subject.
        message: Notification message.
        from_address: Optional sender address override.

    Raises:
        SystemExit: On any error.
    """
    try:
        result = send_notification(
            config=email_config,
            recipients=recipients,
            subject=subject,
            message=message,
            from_address=from_address,
        )
        _handle_send_result(result, recipients, "Notification")
    except ValueError as exc:
        _handle_send_error(exc, "Invalid notification parameters", "Invalid notification parameters", exit_code=ExitCode.INVALID_ARGUMENT)
    except RuntimeError as exc:
        _handle_send_error(exc, "SMTP delivery failed", "Failed to send email", exit_code=ExitCode.SMTP_FAILURE)
    except Exception as exc:
        _handle_send_error(exc, "Unexpected error sending notification", "Unexpected error", exit_code=ExitCode.GENERAL_ERROR, log_traceback=True)


def _load_and_validate_email_config(config: Config) -> EmailConfig:
    """Extract and validate email config from the provided Config object.

    Args:
        config: Already-loaded layered configuration object.

    Returns:
        EmailConfig with validated SMTP configuration.

    Raises:
        SystemExit: When SMTP hosts are not configured (exit code 78 / CONFIG_ERROR).
    """
    email_config = load_email_config_from_dict(config.as_dict())

    if not email_config.smtp_hosts:
        logger.error("No SMTP hosts configured")
        click.echo("\nError: No SMTP hosts configured. Please configure email.smtp_hosts in your config file.", err=True)
        click.echo(f"See: {__init__conf__.shell_command} config-deploy --target user", err=True)
        raise SystemExit(ExitCode.CONFIG_ERROR)

    return email_config


def _handle_send_result(result: bool, recipients: list[str] | None, message_type: str) -> None:
    """Handle the result of a send operation.

    Args:
        result: True if send succeeded.
        recipients: Email recipients, or None when config defaults were used.
        message_type: "Email" or "Notification" for display.

    Raises:
        SystemExit: If send failed.
    """
    if result:
        click.echo(f"\n{message_type} sent successfully!")
        logger.info(f"{message_type} sent via CLI", extra={"recipients": recipients})
    else:
        click.echo(f"\n{message_type} sending failed.", err=True)
        raise SystemExit(ExitCode.SMTP_FAILURE)


def _handle_send_error(
    exc: Exception,
    log_message: str,
    user_message: str,
    *,
    exit_code: ExitCode = ExitCode.GENERAL_ERROR,
    log_traceback: bool = False,
) -> None:
    """Handle errors during send operations.

    Args:
        exc: The exception that occurred.
        log_message: Message for the logger.
        user_message: Message prefix for user display.
        exit_code: Exit code to use (default: GENERAL_ERROR).
        log_traceback: Whether to include traceback in logs.

    Raises:
        SystemExit: Always raises with the given exit code.
    """
    logger.error(
        log_message,
        extra={"error": str(exc), "error_type": type(exc).__name__},
        exc_info=log_traceback,
    )
    click.echo(f"\nError: {user_message} - {exc}", err=True)
    raise SystemExit(exit_code)


__all__ = ["SmtpConfigOverrides", "cli_send_email", "cli_send_notification"]
