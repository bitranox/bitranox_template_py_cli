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
import rich_click as click
from lib_layered_config import Config, redact_mapping
from lib_layered_config.domain.config import SourceInfo
from rich.console import Console
from rich.text import Text

from bitranox_template_py_cli.domain.enums import OutputFormat

_REDACTED = "***REDACTED***"
_SECTION_INDENT = "    "
_TOPLEVEL_INDENT = ""
_console = Console(highlight=False)


def _format_raw_value(value: Any) -> str:
    """Format a config value without key prefix.

    Args:
        value: The configuration value to format.

    Returns:
        Formatted string representation of the value.
    """
    if isinstance(value, list):
        return orjson.dumps(value).decode()
    if isinstance(value, str):
        return f'"{value}"'
    return f"{value}"


def _styled_entry(key: str, value: Any, *, indent: str = "  ") -> Text:
    """Build a Rich Text object for a styled config key-value line.

    Args:
        key: Configuration key name.
        value: Configuration value.
        indent: Leading whitespace before the key.

    Returns:
        A styled ``Text`` object ready for Console output.
    """
    text = Text(indent)
    text.append(key, style="bold")
    text.append(" = ", style="dim")
    raw = _format_raw_value(value)
    if isinstance(value, str) and value == _REDACTED:
        text.append(raw, style="dim red")
    elif isinstance(value, str):
        text.append(raw, style="green")
    else:
        text.append(raw, style="yellow")
    return text


def _format_source_line(info: SourceInfo, indent: str = "  ") -> str:
    """Build a source comment string from an origin info dict.

    Args:
        info: Origin metadata dict with ``layer`` and ``path`` keys.
        indent: Leading whitespace before the comment.

    Returns:
        A comment string like ``# source: defaults (path/to/file.toml)``
        or ``# source: env`` when no path is available.
    """
    layer = info["layer"]
    path = info["path"]
    if path is not None:
        return f"{indent}# source: {layer} ({path})"
    return f"{indent}# source: {layer}"


def _print_section(
    section_name: str,
    data: dict[str, Any],
    config: Config | None = None,
) -> None:
    """Print a configuration section, recursing into nested dicts as TOML sub-sections.

    Args:
        section_name: Dotted section path (e.g. ``lib_log_rich`` or
            ``lib_log_rich.payload_limits``).
        data: Key-value pairs for this section.
        config: Optional Config object for provenance comments. When provided,
            each leaf value is preceded by a ``# source:`` comment line.
    """
    header = Text(f"\n[{section_name}]")
    header.stylize("bold cyan")
    _console.print(header)
    for key, value in data.items():
        if isinstance(value, dict):
            _print_section(f"{section_name}.{key}", cast(dict[str, Any], value), config)
        else:
            if config is not None:
                dotted_key = f"{section_name}.{key}"
                info = config.origin(dotted_key)
                if info is not None:
                    _console.print(_format_source_line(info, _SECTION_INDENT), style="yellow")
            _console.print(_styled_entry(key, value, indent=_SECTION_INDENT))
            _console.print()


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
        Writes formatted configuration to stdout via click.echo().

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
        click.echo(orjson.dumps(redacted, option=orjson.OPT_INDENT_2).decode())
    else:
        click.echo(config.to_json(indent=2, redact=True))


def _display_human(config: Config, section: str | None) -> None:
    """Render configuration as human-readable TOML-like output to stdout."""
    if section:
        section_data = config.get(section, default={})
        if not section_data:
            raise ValueError(f"Section '{section}' not found or empty")
        redacted_section = redact_mapping({section: section_data})
        redacted_value = redacted_section[section]
        if isinstance(redacted_value, dict):
            _print_section(section, cast(dict[str, Any], redacted_value), config)
        else:
            info = config.origin(section)
            if info is not None:
                _console.print(_format_source_line(info, _TOPLEVEL_INDENT), style="yellow")
            _console.print(_styled_entry(section, redacted_value, indent=_TOPLEVEL_INDENT))
            _console.print()
    else:
        data: dict[str, Any] = config.as_dict(redact=True)
        for key, value in data.items():
            if not isinstance(value, dict):
                info = config.origin(key)
                if info is not None:
                    _console.print(_format_source_line(info, _TOPLEVEL_INDENT), style="yellow")
                _console.print(_styled_entry(key, value, indent=_TOPLEVEL_INDENT))
                _console.print()
        for name, value in data.items():
            if isinstance(value, dict):
                _print_section(name, cast(dict[str, Any], value), config)


__all__ = [
    "display_config",
]
