"""Exit code integration tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from bitranox_template_py_cli.adapters import cli as cli_mod
from bitranox_template_py_cli.adapters.config import deploy as config_deploy_mod


@pytest.mark.os_agnostic
def test_when_config_section_is_invalid_it_exits_with_code_22(cli_runner: CliRunner) -> None:
    """Config --section with nonexistent section must exit with INVALID_ARGUMENT (22)."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"])

    assert result.exit_code == 22
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_permission_error_it_exits_with_code_13(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config-deploy PermissionError must exit with PERMISSION_DENIED (13)."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app"])

    assert result.exit_code == 13
    assert "Permission denied" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_generic_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config-deploy generic Exception must exit with GENERAL_ERROR (1)."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise OSError("Disk full")

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 1
    assert "Disk full" in result.stderr


@pytest.mark.os_agnostic
def test_when_email_has_no_smtp_hosts_it_exits_with_code_78(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email with no SMTP hosts configured must exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_email_smtp_fails_it_exits_with_code_69(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email DeliveryError (SMTP failure) must exit with SMTP_FAILURE (69)."""
    from unittest.mock import patch

    from bitranox_template_py_cli.domain.errors import DeliveryError

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

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        side_effect=DeliveryError("SMTP connection refused"),
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 69
    assert "SMTP connection refused" in (result.output + (result.stderr or ""))


@pytest.mark.os_agnostic
def test_when_email_send_returns_false_it_exits_with_code_69(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email returning False must exit with SMTP_FAILURE (69)."""
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

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        return_value=False,
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 69
    assert "sending failed" in (result.output + (result.stderr or ""))


@pytest.mark.os_agnostic
def test_when_email_has_unexpected_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email unexpected Exception must exit with GENERAL_ERROR (1)."""
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

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        side_effect=TypeError("unexpected type error"),
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 1
    assert "unexpected type error" in (result.output + (result.stderr or ""))
