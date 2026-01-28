"""Unit tests for config display: section rendering, value formatting, and error paths."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from lib_layered_config import Config
from lib_layered_config.domain.config import SourceInfo

from bitranox_template_py_cli.adapters.config.display import (
    _format_raw_value,  # pyright: ignore[reportPrivateUsage]
    _format_source_line,  # pyright: ignore[reportPrivateUsage]
    _print_section,  # pyright: ignore[reportPrivateUsage]
    display_config,
)
from bitranox_template_py_cli.domain.enums import OutputFormat

# ======================== _format_raw_value ========================


@pytest.mark.os_agnostic
def test_format_raw_value_renders_string_with_quotes() -> None:
    """String values must be double-quoted in TOML style."""
    assert _format_raw_value("hello") == '"hello"'


@pytest.mark.os_agnostic
def test_format_raw_value_renders_integer_without_quotes() -> None:
    """Integer values must not be quoted."""
    assert _format_raw_value(8080) == "8080"


@pytest.mark.os_agnostic
def test_format_raw_value_renders_boolean_without_quotes() -> None:
    """Boolean values must not be quoted."""
    assert _format_raw_value(True) == "True"


@pytest.mark.os_agnostic
def test_format_raw_value_renders_none_without_quotes() -> None:
    """None must render as-is without quotes."""
    assert _format_raw_value(None) == "None"


@pytest.mark.os_agnostic
def test_format_raw_value_renders_float_without_quotes() -> None:
    """Float values must not be quoted."""
    assert _format_raw_value(30.5) == "30.5"


@pytest.mark.os_agnostic
def test_format_raw_value_renders_list_as_json() -> None:
    """List values must be JSON-serialized."""
    assert _format_raw_value(["smtp1.com", "smtp2.com"]) == '["smtp1.com","smtp2.com"]'


# ======================== _print_section — flat data ========================


@pytest.mark.os_agnostic
def test_print_section_renders_flat_section(capsys: pytest.CaptureFixture[str]) -> None:
    """Flat sections must render all key-value pairs under a single header."""
    data: dict[str, Any] = {
        "service": "myapp",
        "environment": "prod",
        "timeout": 30,
    }
    _print_section("app", data)
    output = capsys.readouterr().out

    assert "[app]" in output
    assert '  service = "myapp"' in output
    assert '  environment = "prod"' in output
    assert "  timeout = 30" in output


@pytest.mark.os_agnostic
def test_print_section_renders_empty_dict(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty section must render only the section header."""
    _print_section("empty", {})
    output = capsys.readouterr().out

    assert "[empty]" in output
    lines = [line for line in output.strip().split("\n") if line.strip()]
    assert len(lines) == 1


# ======================== _print_section — nested sub-sections ========================


@pytest.mark.os_agnostic
def test_print_section_renders_nested_dicts_as_subsections(capsys: pytest.CaptureFixture[str]) -> None:
    """Nested dicts must be rendered as [section.subsection] headers, not JSON blobs."""
    data: dict[str, Any] = {
        "service": "myapp",
        "payload_limits": {
            "message_max_chars": 4096,
            "extra_max_keys": 25,
        },
    }
    _print_section("lib_log_rich", data)
    output = capsys.readouterr().out

    assert "[lib_log_rich]" in output
    assert "[lib_log_rich.payload_limits]" in output
    assert "message_max_chars = 4096" in output
    assert "extra_max_keys = 25" in output
    assert '  service = "myapp"' in output


@pytest.mark.os_agnostic
def test_print_section_handles_deeply_nested_dicts(capsys: pytest.CaptureFixture[str]) -> None:
    """Three levels of nesting must produce dotted section headers."""
    data: dict[str, Any] = {
        "level1": {
            "level2": {
                "leaf": "value",
            },
        },
    }
    _print_section("root", data)
    output = capsys.readouterr().out

    assert "[root]" in output
    assert "[root.level1]" in output
    assert "[root.level1.level2]" in output
    assert '  leaf = "value"' in output


@pytest.mark.os_agnostic
def test_print_section_renders_list_values(capsys: pytest.CaptureFixture[str]) -> None:
    """List values in sections must be rendered as JSON arrays."""
    data: dict[str, Any] = {
        "smtp_hosts": ["smtp1.example.com:587", "smtp2.example.com:587"],
        "enabled": True,
    }
    _print_section("email", data)
    output = capsys.readouterr().out

    assert "[email]" in output
    assert "smtp_hosts = [" in output
    assert "smtp1.example.com:587" in output
    assert "  enabled = True" in output


# ======================== display_config — error paths ========================


@pytest.mark.os_agnostic
def test_display_config_raises_for_nonexistent_section(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Requesting a section that doesn't exist must raise ValueError."""
    config = config_factory({"existing_section": {"key": "value"}})
    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.HUMAN, section="nonexistent")


@pytest.mark.os_agnostic
def test_display_config_raises_for_nonexistent_section_json(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Requesting a nonexistent section in JSON format must also raise ValueError."""
    config = config_factory({"existing_section": {"key": "value"}})
    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.JSON, section="nonexistent")


# ======================== _format_source_line ========================


@pytest.mark.os_agnostic
def test_format_source_line_returns_layer_and_path(
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Source comment must include both layer name and file path when path is available."""
    info = source_info_factory("email.smtp_hosts", "dotenv", "/app/.env")
    assert _format_source_line(info) == "  # source: dotenv (/app/.env)"


@pytest.mark.os_agnostic
def test_format_source_line_returns_layer_only_when_path_is_none(
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Source comment must omit parenthesized path when path is None (e.g. env vars)."""
    info = source_info_factory("app.debug", "env")
    assert _format_source_line(info) == "  # source: env"


@pytest.mark.os_agnostic
def test_format_source_line_returns_none_for_unknown_key_via_config() -> None:
    """Config.origin returns None when no provenance exists; _format_source_line is not called."""
    config = Config({"app": {"key": "val"}}, {})
    assert config.origin("app.key") is None


@pytest.mark.os_agnostic
def test_format_source_line_defaults_layer(
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Source comment for the defaults layer must include the config file path."""
    path = "/src/pkg/adapters/config/defaultconfig.toml"
    info = source_info_factory("lib_log_rich.service", "defaults", path)
    assert _format_source_line(info) == f"  # source: defaults ({path})"


# ======================== _print_section — provenance comments ========================


@pytest.mark.os_agnostic
def test_print_section_includes_source_comments(
    capsys: pytest.CaptureFixture[str],
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """When a Config with metadata is provided, each leaf must be preceded by a source comment."""
    data: dict[str, Any] = {"smtp_hosts": "mail.example.com:25", "from_address": "cli@local"}
    metadata: dict[str, SourceInfo] = {
        "email.smtp_hosts": source_info_factory("email.smtp_hosts", "dotenv", "/app/.env"),
        "email.from_address": source_info_factory("email.from_address", "user", "/home/user/config.toml"),
    }
    config = Config({"email": data}, metadata)
    _print_section("email", data, config)
    output = capsys.readouterr().out

    assert "# source: dotenv (/app/.env)" in output
    assert 'smtp_hosts = "mail.example.com:25"' in output
    assert "# source: user (/home/user/config.toml)" in output
    assert 'from_address = "cli@local"' in output

    lines = output.strip().split("\n")
    # Source comment must appear immediately before the value line
    for i, line in enumerate(lines):
        if "smtp_hosts =" in line:
            assert "# source: dotenv" in lines[i - 1]
        if "from_address =" in line:
            assert "# source: user" in lines[i - 1]


@pytest.mark.os_agnostic
def test_print_section_omits_source_when_no_config(capsys: pytest.CaptureFixture[str]) -> None:
    """When config is None (backward compat), no source comments must appear."""
    data: dict[str, Any] = {"key": "value"}
    _print_section("section", data)
    output = capsys.readouterr().out
    assert "# source:" not in output


@pytest.mark.os_agnostic
def test_print_section_omits_source_for_keys_without_metadata(
    capsys: pytest.CaptureFixture[str],
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Keys with no provenance metadata must not get source comments."""
    data: dict[str, Any] = {"known": "val1", "unknown": "val2"}
    metadata: dict[str, SourceInfo] = {"sec.known": source_info_factory("sec.known", "defaults", "/defaults.toml")}
    config = Config({"sec": data}, metadata)
    _print_section("sec", data, config)
    output = capsys.readouterr().out

    assert "# source: defaults" in output
    lines = output.strip().split("\n")
    for i, line in enumerate(lines):
        if "unknown =" in line:
            assert "# source:" not in lines[i - 1]


# ======================== _print_section — blank line separators ========================


@pytest.mark.os_agnostic
def test_print_section_adds_blank_line_after_each_entry(capsys: pytest.CaptureFixture[str]) -> None:
    """Each leaf entry must be followed by a blank line separator."""
    data: dict[str, Any] = {"first": "a", "second": "b"}
    _print_section("sec", data)
    output = capsys.readouterr().out

    lines = output.split("\n")
    for i, line in enumerate(lines):
        if "first =" in line or "second =" in line:
            assert i + 1 < len(lines), "Expected blank line after entry"
            assert lines[i + 1].strip() == "", f"Expected blank line after '{line.strip()}'"


# ======================== display_config — scalar rendering ========================


@pytest.mark.os_agnostic
def test_display_human_renders_scalars_as_key_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Top-level scalars must render as 'key = value', not as [key] section headers."""
    config = Config({"app_name": "myapp", "section": {"key": "val"}}, {})
    display_config(config, output_format=OutputFormat.HUMAN)
    output = capsys.readouterr().out

    assert "[app_name]" not in output
    assert 'app_name = "myapp"' in output
    assert "[section]" in output


@pytest.mark.os_agnostic
def test_display_human_renders_scalar_provenance(
    capsys: pytest.CaptureFixture[str],
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Top-level scalars must show source provenance comment when metadata exists."""
    metadata: dict[str, SourceInfo] = {
        "codecov_token": source_info_factory("codecov_token", "dotenv", "/app/.env"),
    }
    config = Config({"codecov_token": "***REDACTED***"}, metadata)
    display_config(config, output_format=OutputFormat.HUMAN)
    output = capsys.readouterr().out

    assert "# source: dotenv (/app/.env)" in output
    assert 'codecov_token = "***REDACTED***"' in output
    assert "[codecov_token]" not in output


@pytest.mark.os_agnostic
def test_display_human_scalars_before_sections(capsys: pytest.CaptureFixture[str]) -> None:
    """Top-level scalars must appear before dict sections in output."""
    config = Config({"token": "abc", "email": {"host": "smtp.test"}}, {})
    display_config(config, output_format=OutputFormat.HUMAN)
    output = capsys.readouterr().out

    token_pos = output.index("token =")
    email_pos = output.index("[email]")
    assert token_pos < email_pos, "Scalars must appear before section headers"


@pytest.mark.os_agnostic
def test_display_human_single_scalar_section(
    capsys: pytest.CaptureFixture[str],
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Requesting a scalar key by name must render key=value, not a section header."""
    metadata: dict[str, SourceInfo] = {"app_name": source_info_factory("app_name", "env")}
    config = Config({"app_name": "myapp"}, metadata)
    display_config(config, output_format=OutputFormat.HUMAN, section="app_name")
    output = capsys.readouterr().out

    assert "[app_name]" not in output
    assert 'app_name = "myapp"' in output
    assert "# source: env" in output


# ======================== _format_raw_value — consistent formatting ========================


@pytest.mark.os_agnostic
def test_format_raw_value_quotes_string_consistently() -> None:
    """All string values must be double-quoted regardless of content."""
    assert _format_raw_value("smtp.test") == '"smtp.test"'


# ======================== Edge cases ========================


@pytest.mark.os_agnostic
def test_display_human_empty_section_raises() -> None:
    """Requesting a non-existent section raises ValueError."""
    config = Config({"other": {"key": "val"}}, {})

    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.HUMAN, section="nonexistent")


@pytest.mark.os_agnostic
def test_display_json_empty_section_raises() -> None:
    """JSON format with non-existent section raises ValueError."""
    config = Config({"other": {"key": "val"}}, {})

    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.JSON, section="nonexistent")


@pytest.mark.os_agnostic
def test_format_raw_value_empty_string() -> None:
    """Empty string is rendered as empty quoted string."""
    assert _format_raw_value("") == '""'


@pytest.mark.os_agnostic
def test_format_raw_value_none() -> None:
    """None value is rendered as string representation."""
    assert _format_raw_value(None) == "None"


@pytest.mark.os_agnostic
def test_format_raw_value_boolean_true() -> None:
    """Boolean True is rendered without quotes."""
    assert _format_raw_value(True) == "True"


@pytest.mark.os_agnostic
def test_format_raw_value_unicode_string() -> None:
    """Unicode string is properly quoted."""
    assert _format_raw_value("日本語") == '"日本語"'


@pytest.mark.os_agnostic
def test_display_human_deeply_nested_section(capsys: pytest.CaptureFixture[str]) -> None:
    """Deeply nested dicts render as dotted TOML sub-sections."""
    config = Config({"top": {"mid": {"deep": "value"}}}, {})

    display_config(config, output_format=OutputFormat.HUMAN)

    output = capsys.readouterr().out
    assert "[top.mid]" in output
    assert "deep" in output


# ======================== Falsey value handling ========================


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_zero_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with integer zero value must display (not raise as 'not found')."""
    config = Config({"section": {"count": 0}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    assert "count = 0" in output


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_false_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with boolean False value must display (not raise as 'not found')."""
    config = Config({"section": {"enabled": False}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    assert "enabled = False" in output


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_empty_string_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with empty string value must display (not raise as 'not found')."""
    config = Config({"section": {"name": ""}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    assert 'name = ""' in output


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_empty_list_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with empty list value must display (not raise as 'not found')."""
    config = Config({"section": {"items": []}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    assert "items = []" in output


@pytest.mark.os_agnostic
def test_display_config_json_displays_section_with_falsey_values(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON format with falsey values must display (not raise as 'not found')."""
    config = Config({"section": {"count": 0, "enabled": False, "items": []}}, {})

    display_config(config, output_format=OutputFormat.JSON, section="section")

    output = capsys.readouterr().out
    assert '"count": 0' in output
    assert '"enabled": false' in output
    assert '"items": []' in output
