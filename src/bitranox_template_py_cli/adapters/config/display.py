"""Configuration display functionality for CLI config command.

Provides the business logic for displaying merged configuration from all
sources in human-readable or JSON format. Keeps CLI layer thin by handling
all formatting and display logic here.

Contents:
    * :func:`display_config` -- displays configuration in requested format

System Role:
    Lives in the adapters layer. The CLI command delegates to this module for
    all configuration display logic, keeping presentation concerns separate from
    command-line argument parsing.
"""

from __future__ import annotations

from typing import Any, cast

import orjson

from lib_layered_config import Config, redact_mapping

from ...domain.enums import OutputFormat


def _format_value(key: str, value: Any) -> str:
    """Format a config value for human-readable TOML-like display."""
    if isinstance(value, list):
        return f"  {key} = {orjson.dumps(value).decode()}"
    if isinstance(value, str):
        return f'  {key} = "{value}"'
    return f"  {key} = {value}"


def _print_section(section_name: str, data: dict[str, Any]) -> None:
    """Print a configuration section, recursing into nested dicts as TOML sub-sections.

    Args:
        section_name: Dotted section path (e.g. ``lib_log_rich`` or
            ``lib_log_rich.payload_limits``).
        data: Key-value pairs for this section.
    """
    print(f"\n[{section_name}]")
    for key, value in data.items():
        if isinstance(value, dict):
            _print_section(f"{section_name}.{key}", cast(dict[str, Any], value))
        else:
            print(_format_value(key, value))


def display_config(
    config: Config,
    *,
    format: OutputFormat = OutputFormat.HUMAN,
    section: str | None = None,
) -> None:
    """Display the provided configuration in the requested format.

    Users need visibility into the effective configuration loaded from
    defaults, app configs, host configs, user configs, .env files, and
    environment variables. Outputs the provided Config object in the
    requested format.

    Args:
        config: Already-loaded layered configuration object to display.
        format: Output format: OutputFormat.HUMAN for TOML-like display or
            OutputFormat.JSON for JSON. Defaults to OutputFormat.HUMAN.
        section: Optional section name to display only that section. When None,
            displays all configuration.

    Side Effects:
        Writes formatted configuration to stdout via print().

    Raises:
        ValueError: If a section was requested that doesn't exist or is empty.

    Note:
        The human-readable format mimics TOML syntax for consistency with the
        configuration file format. JSON format provides machine-readable output
        suitable for parsing by other tools. Sensitive values (passwords,
        secrets, tokens, credentials, API keys) are automatically redacted
        using ``lib_layered_config``'s redaction API.

    Example:
        >>> from bitranox_template_py_cli.adapters.config.loader import get_config
        >>> config = get_config()  # doctest: +SKIP
        >>> display_config(config)  # doctest: +SKIP
        [lib_log_rich]
          service = "bitranox_template_py_cli"
          environment = "prod"

        >>> display_config(config, format=OutputFormat.JSON)  # doctest: +SKIP
        {
          "lib_log_rich": {
            "service": "bitranox_template_py_cli",
            "environment": "prod"
          }
        }
    """
    if format == OutputFormat.JSON:
        _display_json(config, section)
    else:
        _display_human(config, section)


def _display_json(config: Config, section: str | None) -> None:
    """Render configuration as JSON to stdout."""
    if section:
        section_data = config.get(section, default={})
        if not section_data:
            raise ValueError(f"Section '{section}' not found or empty")
        redacted = redact_mapping({section: section_data})
        print(orjson.dumps(redacted, option=orjson.OPT_INDENT_2).decode())
    else:
        print(config.to_json(indent=2, redact=True))


def _display_human(config: Config, section: str | None) -> None:
    """Render configuration as human-readable TOML-like output to stdout."""
    if section:
        section_data = config.get(section, default={})
        if not section_data:
            raise ValueError(f"Section '{section}' not found or empty")
        redacted_section = redact_mapping({section: section_data})
        redacted_value = redacted_section[section]
        if isinstance(redacted_value, dict):
            _print_section(section, cast(dict[str, Any], redacted_value))
        else:
            print(f"\n[{section}]")
            print(f"  {redacted_value}")
    else:
        data: dict[str, Any] = config.as_dict(redact=True)
        for section_name, section_value in data.items():
            if isinstance(section_value, dict):
                _print_section(section_name, cast(dict[str, Any], section_value))
            else:
                print(f"\n[{section_name}]")
                print(f"  {section_value}")


__all__ = [
    "display_config",
]
