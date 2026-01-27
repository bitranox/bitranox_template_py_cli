"""Domain enums for configuration and output formatting.

Provides type-safe enumeration values for output formats, deployment targets,
and other fixed string values used throughout the application.

Contents:
    * :class:`OutputFormat` - Output format options for config display
    * :class:`DeployTarget` - Configuration deployment target layers

System Role:
    Acts as the single source of truth for fixed string values, eliminating
    magic strings and enabling type-safe comparisons throughout the codebase.
"""

from __future__ import annotations

from enum import Enum


class OutputFormat(str, Enum):
    """Output format options for configuration display.

    Defines valid output format choices for the config command.
    Inherits from str to allow direct string comparison and Click integration.

    Attributes:
        HUMAN: Human-readable TOML-like output format.
        JSON: Machine-readable JSON output format.

    Example:
        >>> OutputFormat.HUMAN.value
        'human'
        >>> OutputFormat.JSON == "json"
        True
    """

    HUMAN = "human"
    JSON = "json"


class DeployTarget(str, Enum):
    """Configuration deployment target layers.

    Defines valid target layers for configuration file deployment.
    Inherits from str to allow direct string comparison and Click integration.

    Attributes:
        APP: System-wide application configuration (requires privileges).
        HOST: System-wide host-specific configuration (requires privileges).
        USER: User-specific configuration (~/.config on Linux).

    Example:
        >>> DeployTarget.USER.value
        'user'
        >>> DeployTarget.APP == "app"
        True
    """

    APP = "app"
    HOST = "host"
    USER = "user"


__all__ = [
    "DeployTarget",
    "OutputFormat",
]
