"""Integration tests for config display via public API.

Tests cover display_config behavior - private helper functions are tested
implicitly through the public API. CLI tests in test_cli_config.py provide
additional integration coverage.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from lib_layered_config import Config
from lib_layered_config.domain.config import SourceInfo

from bitranox_template_py_cli.adapters.config.display import display_config
from bitranox_template_py_cli.domain.enums import OutputFormat

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
def test_display_config_json_displays_section_with_falsey_values(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON format with falsey values must display (not raise as 'not found')."""
    config = Config({"section": {"count": 0, "enabled": False, "items": []}}, {})

    display_config(config, output_format=OutputFormat.JSON, section="section")

    output = capsys.readouterr().out
    assert '"count": 0' in output
    assert '"enabled": false' in output
    assert '"items": []' in output
