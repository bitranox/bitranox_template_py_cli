"""Unit tests for config display: section rendering, value formatting, and error paths."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from lib_layered_config import Config

from bitranox_template_py_cli.adapters.config.display import (
    _format_value,  # pyright: ignore[reportPrivateUsage]
    _print_section,  # pyright: ignore[reportPrivateUsage]
    display_config,
)
from bitranox_template_py_cli.domain.enums import OutputFormat


# ======================== _format_value ========================


@pytest.mark.os_agnostic
def test_format_value_renders_string_with_quotes() -> None:
    """String values must be double-quoted in TOML style."""
    assert _format_value("key", "hello") == '  key = "hello"'


@pytest.mark.os_agnostic
def test_format_value_renders_integer_without_quotes() -> None:
    """Integer values must not be quoted."""
    assert _format_value("port", 8080) == "  port = 8080"


@pytest.mark.os_agnostic
def test_format_value_renders_boolean_without_quotes() -> None:
    """Boolean values must not be quoted."""
    assert _format_value("enabled", True) == "  enabled = True"


@pytest.mark.os_agnostic
def test_format_value_renders_none_without_quotes() -> None:
    """None must render as-is without quotes."""
    assert _format_value("optional", None) == "  optional = None"


@pytest.mark.os_agnostic
def test_format_value_renders_float_without_quotes() -> None:
    """Float values must not be quoted."""
    assert _format_value("timeout", 30.5) == "  timeout = 30.5"


@pytest.mark.os_agnostic
def test_format_value_renders_list_as_json() -> None:
    """List values must be JSON-serialized."""
    result = _format_value("hosts", ["smtp1.com", "smtp2.com"])
    assert result == '  hosts = ["smtp1.com","smtp2.com"]'


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
    with pytest.raises(ValueError, match="not found or empty"):
        display_config(config, format=OutputFormat.HUMAN, section="nonexistent")


@pytest.mark.os_agnostic
def test_display_config_raises_for_nonexistent_section_json(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Requesting a nonexistent section in JSON format must also raise ValueError."""
    config = config_factory({"existing_section": {"key": "value"}})
    with pytest.raises(ValueError, match="not found or empty"):
        display_config(config, format=OutputFormat.JSON, section="nonexistent")
