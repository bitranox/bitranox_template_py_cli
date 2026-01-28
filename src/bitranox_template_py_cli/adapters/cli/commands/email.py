"""Email sending CLI commands.

Provides commands for sending emails and notifications via SMTP.

Contents:
    * :func:`cli_send_email` - Send email with optional HTML and attachments.
    * :func:`cli_send_notification` - Send simple plain-text notification.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import lib_log_rich.runtime
import rich_click as click
from lib_layered_config import Config

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters.email.sender import EmailConfig
from bitranox_template_py_cli.application.ports import LoadEmailConfigFromDict, SendEmail, SendNotification
from bitranox_template_py_cli.domain.errors import ConfigurationError, DeliveryError

from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import CLIContext, get_cli_context
from ..exit_codes import ExitCode

logger = logging.getLogger(__name__)


def _get_email_services(
    cli_ctx: CLIContext,
) -> tuple[SendEmail, SendNotification, LoadEmailConfigFromDict]:
    """Return email services from context or production defaults.

    Args:
        cli_ctx: CLI context potentially containing service overrides.

    Returns:
        Tuple of (send_email, send_notification, load_email_config_from_dict).
    """
    from bitranox_template_py_cli.adapters.email.sender import (
        load_email_config_from_dict as prod_load,
    )
    from bitranox_template_py_cli.adapters.email.sender import (
        send_email as prod_send_email,
    )
    from bitranox_template_py_cli.adapters.email.sender import (
        send_notification as prod_send_notification,
    )

    return (
        cli_ctx.send_email or prod_send_email,
        cli_ctx.send_notification or prod_send_notification,
        cli_ctx.load_email_config_from_dict or prod_load,
    )


def filter_sentinels(**kwargs: Any) -> dict[str, Any]:
    """Filter out None and empty tuple sentinels, converting tuples to lists.

    Used to prepare CLI option overrides for ``model_copy(update=...)``.
    Removes None values (unset options) and empty tuples (unset multiple options),
    and converts non-empty tuples to lists for Pydantic compatibility.

    Args:
        **kwargs: Keyword arguments to filter.

    Returns:
        Filtered dict with sentinel values removed and tuples converted to lists.
    """
    result: dict[str, Any] = {}
    for k, v in kwargs.items():
        if v is None or v == ():
            continue
        if isinstance(v, tuple):
            result[k] = list(cast(tuple[Any, ...], v))
        else:
            result[k] = v
    return result


def _smtp_config_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Apply shared SMTP configuration override options to a Click command.

    Adds CLI flags for all EmailConfig fields so that any TOML setting
    can be overridden at invocation time.
    """
    options = [
        click.option(
            "--smtp-host",
            "smtp_hosts",
            multiple=True,
            default=(),
            help="Override SMTP host (can specify multiple; format host:port)",
        ),
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
@click.option(
    "--to",
    "recipients",
    multiple=True,
    required=False,
    help="Recipient email address (can specify multiple; uses config default if not specified)",
)
@click.option("--subject", required=True, help="Email subject line")
@click.option("--body", default="", help="Plain-text email body")
@click.option("--body-html", default="", help="HTML email body (sent as multipart with plain text)")
@click.option(
    "--from", "from_address", default=None, help="Override sender address (uses config default if not specified)"
)
@click.option(
    "--attachment",
    "attachments",
    multiple=True,
    type=click.Path(path_type=str),
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
    send_email_svc, _, load_config_svc = _get_email_services(cli_ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-email", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-email", extra=extra):
        email_config = _load_and_validate_email_config(cli_ctx.config, load_config_svc)
        overrides = filter_sentinels(
            smtp_hosts=smtp_hosts,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_starttls=use_starttls,
            timeout=timeout,
            raise_on_missing_attachments=raise_on_missing_attachments,
            raise_on_invalid_recipient=raise_on_invalid_recipient,
        )
        if overrides:
            email_config = email_config.model_copy(update=overrides)
        attachment_paths = [Path(p) for p in attachments] if attachments else None

        _log_send_email_start(resolved_recipients, subject, body_html, attachments)
        _execute_with_email_error_handling(
            operation=functools.partial(
                send_email_svc,
                config=email_config,
                recipients=resolved_recipients,
                subject=subject,
                body=body,
                body_html=body_html,
                from_address=from_address,
                attachments=attachment_paths,
            ),
            recipients=resolved_recipients,
            message_type="Email",
            catches_file_not_found=True,
        )


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


def _execute_with_email_error_handling(
    *,
    operation: Callable[[], bool],
    recipients: list[str] | None,
    message_type: str,
    catches_file_not_found: bool = False,
) -> None:
    """Execute an email operation with unified error handling.

    Args:
        operation: Zero-arg callable returning True on success.
        recipients: Recipients for logging context.
        message_type: "Email" or "Notification" for display messages.
        catches_file_not_found: When True, catches FileNotFoundError
            (needed for send-email with attachments).

    Raises:
        SystemExit: On any error.
    """
    try:
        result = operation()
        _handle_send_result(result, recipients, message_type)
    except ConfigurationError as exc:
        _handle_send_error(
            exc,
            f"{message_type} configuration error",
            "Configuration error",
            exit_code=ExitCode.CONFIG_ERROR,
        )
    except ValueError as exc:
        _handle_send_error(
            exc,
            f"Invalid {message_type.lower()} parameters",
            f"Invalid {message_type.lower()} parameters",
            exit_code=ExitCode.INVALID_ARGUMENT,
        )
    except FileNotFoundError as exc:
        if not catches_file_not_found:
            raise
        _handle_send_error(
            exc,
            "Attachment file not found",
            "Attachment file not found",
            exit_code=ExitCode.FILE_NOT_FOUND,
        )
    except (DeliveryError, RuntimeError) as exc:
        _handle_send_error(
            exc,
            "SMTP delivery failed",
            "Failed to send email",
            exit_code=ExitCode.SMTP_FAILURE,
        )
    except Exception as exc:
        _handle_send_error(
            exc,
            f"Unexpected error sending {message_type.lower()}",
            "Unexpected error",
            exit_code=ExitCode.GENERAL_ERROR,
            log_traceback=True,
        )


@click.command("send-notification", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--to",
    "recipients",
    multiple=True,
    required=False,
    help="Recipient email address (can specify multiple; uses config default if not specified)",
)
@click.option("--subject", required=True, help="Notification subject line")
@click.option("--message", required=True, help="Notification message (plain text)")
@click.option(
    "--from", "from_address", default=None, help="Override sender address (uses config default if not specified)"
)
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
    _, send_notification_svc, load_config_svc = _get_email_services(cli_ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-notification", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-notification", extra=extra):
        email_config = _load_and_validate_email_config(cli_ctx.config, load_config_svc)
        overrides = filter_sentinels(
            smtp_hosts=smtp_hosts,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_starttls=use_starttls,
            timeout=timeout,
            raise_on_missing_attachments=raise_on_missing_attachments,
            raise_on_invalid_recipient=raise_on_invalid_recipient,
        )
        if overrides:
            email_config = email_config.model_copy(update=overrides)
        logger.info("Sending notification", extra={"recipients": resolved_recipients, "subject": subject})
        _execute_with_email_error_handling(
            operation=functools.partial(
                send_notification_svc,
                config=email_config,
                recipients=resolved_recipients,
                subject=subject,
                message=message,
                from_address=from_address,
            ),
            recipients=resolved_recipients,
            message_type="Notification",
        )


def _load_and_validate_email_config(config: Config, loader: LoadEmailConfigFromDict) -> EmailConfig:
    """Extract and validate email config from the provided Config object.

    Args:
        config: Already-loaded layered configuration object.
        loader: Function to load EmailConfig from dict.

    Returns:
        EmailConfig with validated SMTP configuration.

    Raises:
        SystemExit: When SMTP hosts are not configured (exit code 78 / CONFIG_ERROR).
    """
    email_config = loader(config.as_dict())

    if not email_config.smtp_hosts:
        logger.error("No SMTP hosts configured")
        click.echo(
            "\nError: No SMTP hosts configured. Please configure email.smtp_hosts in your config file.", err=True
        )
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
        logger.info("%s sent via CLI", message_type, extra={"recipients": recipients})
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


__all__ = ["cli_send_email", "cli_send_notification", "filter_sentinels"]
