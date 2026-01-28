"""CLI email stories: send-email, send-notification, SMTP overrides, credential overrides."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from bitranox_template_py_cli.adapters import cli as cli_mod

if TYPE_CHECKING:
    from bitranox_template_py_cli.adapters.memory.email import EmailSpy

# ======================== Email Command Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
) -> None:
    """When SMTP hosts are not configured, send-email should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
        ],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When SMTP is configured, send-email should successfully send."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test Subject",
            "--body",
            "Test body",
        ],
    )

    assert result.exit_code == 0
    assert "Email sent successfully" in result.output
    assert len(email_spy.sent_emails) == 1
    assert email_spy.sent_emails[0]["subject"] == "Test Subject"
    assert email_spy.sent_emails[0]["recipients"] == ["recipient@test.com"]


@pytest.mark.os_agnostic
def test_when_send_email_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When multiple --to flags are provided, send-email should accept them."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "user1@test.com",
            "--to",
            "user2@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["recipients"] == ["user1@test.com", "user2@test.com"]


@pytest.mark.os_agnostic
def test_when_send_email_includes_html_body_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When HTML body is provided, send-email should include it."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Plain text",
            "--body-html",
            "<h1>HTML</h1>",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["body_html"] == "<h1>HTML</h1>"


@pytest.mark.os_agnostic
def test_when_send_email_has_attachments_it_sends(
    cli_runner: CliRunner,
    tmp_path: Any,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When attachments are provided, send-email should include them."""
    from pathlib import Path

    attachment = tmp_path / "test.txt"
    attachment.write_text("Test content")

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "See attachment",
            "--attachment",
            str(attachment),
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["attachments"] == [Path(attachment)]


@pytest.mark.os_agnostic
def test_when_send_email_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When SMTP returns failure, send-email should show SMTP_FAILURE (69) error."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()
    email_spy.should_fail = True

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
        ],
    )

    assert result.exit_code == 69
    assert "failed" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
) -> None:
    """When SMTP hosts are not configured, send-notification should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When SMTP is configured, send-notification should successfully send."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 0
    assert "Notification sent successfully" in result.output
    assert len(email_spy.sent_notifications) == 1
    assert email_spy.sent_notifications[0]["subject"] == "Alert"
    assert email_spy.sent_notifications[0]["message"] == "System notification"


@pytest.mark.os_agnostic
def test_when_send_notification_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When multiple --to flags are provided, send-notification should accept them."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin1@test.com",
            "--to",
            "admin2@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_notifications[0]["recipients"] == ["admin1@test.com", "admin2@test.com"]


@pytest.mark.os_agnostic
def test_when_send_notification_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When SMTP returns failure, send-notification should show SMTP_FAILURE (69) error."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )
    inject_email_services()
    email_spy.should_fail = True

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 69
    assert "failed" in result.output.lower()


# ======================== SMTP Config Override Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --smtp-host is provided, send-email should use the override instead of config value."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.config.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
            "--smtp-host",
            "smtp.override.com:465",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["config"].smtp_hosts == ["smtp.override.com:465"]


@pytest.mark.os_agnostic
def test_when_send_email_receives_timeout_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --timeout is provided, send-email should use the overridden timeout."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
            "--timeout",
            "60",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["config"].timeout == 60.0


@pytest.mark.os_agnostic
def test_when_send_email_receives_no_use_starttls_override_it_applies_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --no-use-starttls is provided, send-email should disable starttls in config."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
            "--no-use-starttls",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["config"].use_starttls is False


@pytest.mark.os_agnostic
def test_when_send_email_receives_credential_overrides_it_uses_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --smtp-username and --smtp-password are provided, send-email should use them."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
            "--smtp-username",
            "myuser",
            "--smtp-password",
            "mypass",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_emails[0]["config"].smtp_username == "myuser"
    assert email_spy.sent_emails[0]["config"].smtp_password == "mypass"


@pytest.mark.os_agnostic
def test_when_send_notification_receives_from_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --from is provided, send-notification should use the override sender."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "default@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
            "--from",
            "override@test.com",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_notifications[0]["from_address"] == "override@test.com"


@pytest.mark.os_agnostic
def test_when_send_notification_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    inject_email_services: Callable[[], None],
    email_spy: EmailSpy,
) -> None:
    """When --smtp-host is provided, send-notification should use the override host."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.config.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )
    inject_email_services()

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
            "--smtp-host",
            "smtp.override.com:465",
        ],
    )

    assert result.exit_code == 0
    assert email_spy.sent_notifications[0]["config"].smtp_hosts == ["smtp.override.com:465"]


# ======================== Attachment path validation ========================


@pytest.mark.os_agnostic
def test_when_send_email_attachment_missing_with_raise_flag_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    tmp_path: Any,
) -> None:
    """Missing attachment with default raise behavior should fail with FILE_NOT_FOUND.

    This test uses the production adapter to verify actual file validation behavior.
    The memory adapter doesn't validate file paths, so we use smtplib mock here.
    """
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    nonexistent_file = str(tmp_path / "nonexistent_attachment.txt")

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--attachment",
                nonexistent_file,
            ],
        )

    # Default: raise_on_missing_attachments=True, so FileNotFoundError is raised
    assert result.exit_code != 0
    # Could be FILE_NOT_FOUND (66) or the error message in output
    assert "not found" in result.output.lower() or result.exit_code == 66


@pytest.mark.os_agnostic
def test_when_send_email_attachment_path_accepted_by_click(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
    tmp_path: Any,
) -> None:
    """Click accepts nonexistent attachment paths (validation delegated to app).

    This test uses the production adapter to verify actual file validation behavior.
    """
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    nonexistent_file = str(tmp_path / "nonexistent_attachment.txt")

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--attachment",
                nonexistent_file,
            ],
        )

    # Click doesn't reject with "Path ... does not exist"
    assert "does not exist" not in result.output
    # Error comes from application layer
    assert result.exit_code != 0
    assert "Attachment" in result.output or "not found" in result.output.lower()
