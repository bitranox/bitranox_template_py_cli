"""Override filtering unit tests."""

from __future__ import annotations

import pytest

from bitranox_template_py_cli.adapters.cli.commands.email import filter_sentinels
from bitranox_template_py_cli.adapters.email.sender import EmailConfig


@pytest.mark.os_agnostic
def testfilter_sentinels_removes_none_and_empty_tuple() -> None:
    """filter_sentinels filters out None and empty tuple sentinels."""
    result = filter_sentinels(
        smtp_hosts=(),
        smtp_username=None,
        timeout=60.0,
    )

    assert result == {"timeout": 60.0}


@pytest.mark.os_agnostic
def testfilter_sentinels_converts_tuples_to_lists() -> None:
    """filter_sentinels converts non-empty tuples to lists for model_copy."""
    result = filter_sentinels(smtp_hosts=("smtp.example.com:587",))

    assert result == {"smtp_hosts": ["smtp.example.com:587"]}


@pytest.mark.os_agnostic
def test_model_copy_with_filtered_overrides_preserves_other_fields() -> None:
    """model_copy with filtered overrides preserves non-overridden fields."""
    config = EmailConfig(
        smtp_hosts=["smtp.original.com:587"],
        from_address="sender@example.com",
        timeout=30.0,
    )
    overrides = filter_sentinels(
        smtp_hosts=("smtp.new.com:465",),
        smtp_username=None,
        use_starttls=False,
    )

    result = config.model_copy(update=overrides)

    assert result.smtp_hosts == ["smtp.new.com:465"]
    assert result.use_starttls is False
    assert result.from_address == "sender@example.com"
    assert result.timeout == 30.0
