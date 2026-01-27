"""Unit tests for the ExitCode IntEnum."""

from __future__ import annotations

import pytest

from bitranox_template_cli_app_config_log_mail.adapters.cli.exit_codes import ExitCode


@pytest.mark.os_agnostic
def test_exit_code_is_int_enum() -> None:
    """ExitCode members must be usable as plain integers."""
    assert isinstance(ExitCode.SUCCESS, int)
    assert ExitCode.SUCCESS == 0


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("member", "expected_value"),
    [
        (ExitCode.SUCCESS, 0),
        (ExitCode.GENERAL_ERROR, 1),
        (ExitCode.FILE_NOT_FOUND, 2),
        (ExitCode.PERMISSION_DENIED, 13),
        (ExitCode.INVALID_ARGUMENT, 22),
        (ExitCode.SMTP_FAILURE, 69),
        (ExitCode.CONFIG_ERROR, 78),
        (ExitCode.TIMEOUT, 110),
        (ExitCode.SIGNAL_INT, 130),
        (ExitCode.BROKEN_PIPE, 141),
        (ExitCode.SIGNAL_TERM, 143),
    ],
)
def test_exit_code_posix_values(member: ExitCode, expected_value: int) -> None:
    """Each ExitCode member must match its POSIX-conventional value."""
    assert int(member) == expected_value


@pytest.mark.os_agnostic
def test_exit_code_member_count() -> None:
    """ExitCode must contain exactly the expected number of members."""
    assert len(ExitCode) == 11


@pytest.mark.os_agnostic
def test_exit_code_lookup_by_value() -> None:
    """ExitCode(value) must return the correct member."""
    assert ExitCode(69) is ExitCode.SMTP_FAILURE
    assert ExitCode(78) is ExitCode.CONFIG_ERROR
