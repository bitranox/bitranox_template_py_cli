"""CLI email stories: send-email, send-notification, SMTP overrides, credential overrides."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from bitranox_template_py_cli.adapters import cli as cli_mod

# ======================== Email Command Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP hosts are not configured, send-email should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

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
) -> None:
    """When SMTP is configured, send-email should successfully send."""
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

    with patch("smtplib.SMTP"):
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


@pytest.mark.os_agnostic
def test_when_send_email_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When multiple --to flags are provided, send-email should accept them."""
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

    with patch("smtplib.SMTP"):
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


@pytest.mark.os_agnostic
def test_when_send_email_includes_html_body_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When HTML body is provided, send-email should include it."""
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
                "Plain text",
                "--body-html",
                "<h1>HTML</h1>",
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_has_attachments_it_sends(
    cli_runner: CliRunner,
    tmp_path: Any,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When attachments are provided, send-email should include them."""
    from unittest.mock import patch

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
                "See attachment",
                "--attachment",
                str(attachment),
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP connection fails, send-email should show SMTP_FAILURE (69) error."""
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

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect")

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
        assert "Error" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP hosts are not configured, send-notification should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

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
) -> None:
    """When SMTP is configured, send-notification should successfully send."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP"):
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


@pytest.mark.os_agnostic
def test_when_send_notification_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When multiple --to flags are provided, send-notification should accept them."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP"):
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


@pytest.mark.os_agnostic
def test_when_send_notification_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP connection fails, send-notification should show SMTP_FAILURE (69) error."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect")

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
        assert "Error" in result.output


# ======================== SMTP Config Override Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-host is provided, send-email should use the override instead of config value."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP") as mock_smtp:
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
        smtp_calls = mock_smtp.call_args_list
        # SMTP(host, ...) — host is always the first positional arg
        assert any(len(c.args) > 0 and "smtp.override.com" in c.args[0] for c in smtp_calls)


@pytest.mark.os_agnostic
def test_when_send_email_receives_timeout_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --timeout is provided, send-email should use the overridden timeout."""
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

    with patch("smtplib.SMTP") as mock_smtp:
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
        smtp_calls = mock_smtp.call_args_list
        # smtplib.SMTP accepts timeout as keyword or second positional arg
        assert any(c.kwargs.get("timeout") == 60.0 for c in smtp_calls) or any(
            len(c.args) > 1 and c.args[1] == 60.0 for c in smtp_calls
        )


@pytest.mark.os_agnostic
def test_when_send_email_receives_no_use_starttls_override_it_skips_starttls(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --no-use-starttls is provided, send-email should not call starttls."""
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

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

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
        assert not mock_instance.starttls.called


@pytest.mark.os_agnostic
def test_when_send_email_receives_credential_overrides_it_uses_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-username and --smtp-password are provided, send-email should use them."""
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

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

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
        mock_instance.login.assert_called_once_with("myuser", "mypass")


@pytest.mark.os_agnostic
def test_when_send_notification_receives_from_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --from is provided, send-notification should use the override sender."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

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
        mock_instance.sendmail.assert_called_once()
        call_args = mock_instance.sendmail.call_args
        assert call_args[0][0] == "override@test.com"


@pytest.mark.os_agnostic
def test_when_send_notification_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-host is provided, send-notification should use the override host."""
    from unittest.mock import patch

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

    with patch("smtplib.SMTP") as mock_smtp:
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
        smtp_calls = mock_smtp.call_args_list
        # SMTP(host, ...) — host is always the first positional arg
        assert any(len(c.args) > 0 and "smtp.override.com" in c.args[0] for c in smtp_calls)
