"""The merged [email] section becomes an EmailConfig: file keys kept, unknown keys refused.

lib_layered_config merges every layer into one mapping; load_email_config_from_dict reads its
[email] section. Five file keys differ from ConfMail's field names, values that mean "not
configured" are dropped so the library default applies, and a key that is not a file key is
refused, whatever layer it came from.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from btx_lib_mail import ConfMail
from pydantic import ValidationError

from bitranox_template_py_cli.adapters.email.config import (
    EmailConfig,
    describe_validation_error,
    load_email_config_from_dict,
)


def _load(email: object) -> EmailConfig:
    return load_email_config_from_dict({"email": email})


def _problems(email: object) -> list[str]:
    with pytest.raises(ValidationError) as caught:
        _load(email)
    return describe_validation_error(caught.value)


@pytest.mark.os_agnostic
def test_the_five_renamed_file_keys_reach_their_fields() -> None:
    config = _load(
        {
            "smtp_hosts": ["smtp.example.com:587"],
            "use_starttls": False,
            "timeout": 12.5,
            "starttls_verify": False,
            "local_hostname": "mail.example.com",
        }
    )

    assert config.smtphosts == ["smtp.example.com:587"]
    assert config.smtp_use_starttls is False
    assert config.smtp_timeout == 12.5
    assert config.smtp_starttls_verify is False
    assert config.smtp_local_hostname == "mail.example.com"


@pytest.mark.os_agnostic
def test_attachment_keys_reach_their_prefixed_fields() -> None:
    config = _load({"attachments": {"max_size_bytes": 1024, "allow_symlinks": True, "allowed_extensions": [".PDF"]}})

    assert config.attachment_max_size_bytes == 1024
    assert config.attachment_allow_symlinks is True
    assert config.attachment_allowed_extensions == frozenset({".pdf"})


@pytest.mark.os_agnostic
@pytest.mark.parametrize("key", ["from_address", "smtp_username", "smtp_password", "local_hostname"])
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_text_means_not_configured(key: str, blank: str) -> None:
    config = _load({key: blank})

    field = {"local_hostname": "smtp_local_hostname"}.get(key, key)
    assert getattr(config, field) is None


@pytest.mark.os_agnostic
@pytest.mark.parametrize("key", ["smtp_hosts", "recipients"])
def test_a_blank_list_string_means_an_empty_list(key: str) -> None:
    config = _load({key: "  "})

    assert getattr(config, {"smtp_hosts": "smtphosts"}.get(key, key)) == []


@pytest.mark.os_agnostic
def test_a_single_host_or_address_string_is_a_one_entry_list() -> None:
    config = _load({"smtp_hosts": "smtp.example.com:587", "recipients": "ops@example.com"})

    assert config.smtphosts == ["smtp.example.com:587"]
    assert config.recipients == ["ops@example.com"]


@pytest.mark.os_agnostic
def test_empty_attachment_lists_mean_the_library_defaults() -> None:
    lists: dict[str, list[str]] = {
        "allowed_extensions": [],
        "blocked_extensions": [],
        "allowed_directories": [],
        "blocked_directories": [],
    }
    config = _load({"attachments": lists})
    defaults = ConfMail()

    assert config.attachment_allowed_extensions is None
    assert config.attachment_allowed_directories is None
    assert config.attachment_blocked_extensions == defaults.attachment_blocked_extensions
    assert config.attachment_blocked_directories == defaults.attachment_blocked_directories


@pytest.mark.os_agnostic
def test_a_size_limit_of_zero_means_no_limit() -> None:
    assert _load({"attachments": {"max_size_bytes": 0}}).attachment_max_size_bytes is None


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("email", "line"),
    [
        ({"smtp_host": "smtp.example.com"}, "email.smtp_host: unknown key"),
        ({"smtp_timeout": 5}, "email.smtp_timeout: unknown key"),
        ({"attachment_max_size_bytes": 5}, "email.attachment_max_size_bytes: unknown key"),
        ({"attachments": {"max_size": 5}}, "email.attachments.max_size: unknown key"),
        ({"attachments": {"allow_empty_blocklists": True}}, "email.attachments.allow_empty_blocklists: unknown key"),
    ],
    ids=["typo", "library-name", "flattened-name", "attachment-typo", "not-exposed"],
)
def test_a_key_that_is_not_a_file_key_is_refused(email: dict[str, Any], line: str) -> None:
    assert _problems(email) == [line]


@pytest.mark.os_agnostic
def test_an_attachments_value_that_is_not_a_table_is_refused() -> None:
    assert _problems({"attachments": "none"}) == ["email.attachments: Input should be a valid dictionary"]


@pytest.mark.os_agnostic
def test_every_unknown_key_is_named_in_one_report() -> None:
    assert _problems({"smtp_host": "h", "attachments": {"maxsize": 1}}) == [
        "email.smtp_host: unknown key",
        "email.attachments.maxsize: unknown key",
    ]


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("email", "line"),
    [
        ({"timeout": -5}, "email.timeout: timeout must be positive, got -5.0"),
        (
            {"attachments": {"max_size_bytes": -1}},
            "email.attachments.max_size_bytes: attachments.max_size_bytes must be positive, got -1",
        ),
    ],
    ids=["timeout", "attachment"],
)
def test_a_refused_value_is_named_by_its_file_key_in_the_location_and_the_reason(
    email: dict[str, Any], line: str
) -> None:
    assert _problems(email) == [line]


@pytest.mark.os_agnostic
def test_a_comma_separated_extension_string_is_refused_not_ignored() -> None:
    problems = _problems({"attachments": {"allowed_extensions": ".pdf,.txt"}})

    assert len(problems) == 1
    assert problems[0].startswith("email.attachments.allowed_extensions: ")


@pytest.mark.os_agnostic
def test_every_email_config_field_but_one_is_reachable_from_exactly_one_file_key() -> None:
    """Pins the key lists against the model: a field ConfMail adds later must be decided here."""
    from bitranox_template_py_cli.adapters.email import config as module

    reachable = [module.FILE_KEY_TO_FIELD.get(key, key) for key in module.SECTION_KEYS - {"attachments"}]
    reachable += [f"attachment_{key}" for key in module.ATTACHMENT_KEYS]

    assert sorted(reachable) == sorted(set(EmailConfig.model_fields) - {"attachment_allow_empty_blocklists"})


@pytest.mark.os_agnostic
def test_the_model_refuses_unknown_python_names_too() -> None:
    with pytest.raises(ValidationError):
        EmailConfig.model_validate({"smtp_hosts": ["h"]})


@pytest.mark.os_agnostic
def test_a_directory_list_becomes_paths() -> None:
    config = _load({"attachments": {"allowed_directories": ["/srv/exports"]}})

    assert config.attachment_allowed_directories == frozenset({Path("/srv/exports")})


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "host", ["smtp.example.com:99999", "smtp.example.com:abc", "[::1"], ids=["port-range", "port-text", "bracket"]
)
def test_a_malformed_host_is_refused_at_load(host: str) -> None:
    """ConfMail refuses only userinfo, paths and control characters; the port and brackets are checked here."""
    problems = _problems({"smtp_hosts": [host]})

    assert len(problems) == 1, problems
    assert problems[0].startswith("email.smtp_hosts: "), problems
    assert "Value error" not in problems[0], problems


@pytest.mark.os_agnostic
def test_a_host_list_of_the_wrong_type_reads_as_the_file_key_without_a_prefix() -> None:
    """btx_lib_mail drops ctx for a credential field, so pydantic's prefix is still on the message."""
    assert _problems({"smtp_hosts": 587}) == [
        "email.smtp_hosts: smtp_hosts must be a string, list of strings, or tuple of strings"
    ]


@pytest.mark.os_agnostic
def test_an_all_digit_user_name_from_the_environment_is_read_as_text() -> None:
    """lib_layered_config reads an all-digit environment value as an int."""
    assert _load({"smtp_username": 4711}).smtp_username == "4711"
