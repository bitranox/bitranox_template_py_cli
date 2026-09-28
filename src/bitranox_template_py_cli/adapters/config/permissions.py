"""Permission settings loader for config deployment.

Provides functions to load permission defaults from configuration and
compute effective permission modes for deployment targets.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from lib_layered_config import (
    DEFAULT_APP_DIR_MODE,
    DEFAULT_APP_FILE_MODE,
    DEFAULT_USER_DIR_MODE,
    DEFAULT_USER_FILE_MODE,
)
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from lib_layered_config import Config

    from bitranox_template_py_cli.domain.enums import DeployTarget


class PermissionDefaults(BaseModel):
    """Validated, immutable permission defaults for deployment layers.

    Parsed at the boundary from ``[lib_layered_config.default_permissions]``
    config section. All fields have library-level fallback defaults.

    Example:
        >>> defaults = PermissionDefaults()
        >>> defaults.user_directory == 0o700
        True
    """

    model_config = ConfigDict(frozen=True)

    app_directory: int = DEFAULT_APP_DIR_MODE
    app_file: int = DEFAULT_APP_FILE_MODE
    host_directory: int = DEFAULT_APP_DIR_MODE
    host_file: int = DEFAULT_APP_FILE_MODE
    user_directory: int = DEFAULT_USER_DIR_MODE
    user_file: int = DEFAULT_USER_FILE_MODE
    enabled: bool = True

    def dir_mode_for(self, layer: str) -> int:
        """Return directory mode for the given layer name."""
        return getattr(self, f"{layer}_directory")

    def file_mode_for(self, layer: str) -> int:
        """Return file mode for the given layer name."""
        return getattr(self, f"{layer}_file")


#: chmod(2) defines only the low 12 bits (setuid, setgid, sticky and rwxrwxrwx).
MAX_PERMISSION_MODE: Final[int] = 0o7777

#: A plain octal literal: an optional lowercase ``0o`` prefix, then octal digits, nothing
#: else. A bare ``int(value, 8)`` would also accept surrounding whitespace, ``_`` digit
#: separators and non-ASCII decimal digits, and ``int(value, 0)`` a sign or another base.
_OCTAL_MODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?:0o)?[0-7]+")

#: The special bits no deployed configuration directory or file may carry.
_SPECIAL_BITS: Final[tuple[tuple[int, str], ...]] = ((0o4000, "setuid"), (0o2000, "setgid"), (0o1000, "sticky"))
_WORLD_WRITE: Final[int] = 0o002
_OWNER_DIRECTORY: Final[int] = 0o700
_OWNER_FILE: Final[int] = 0o600


def parse_octal_mode_string(value: str) -> int:
    """Parse a plain octal literal (``"750"`` or ``"0o750"``) into a mode in 0..0o7777.

    The single rule for what a textual mode looks like, shared by the ``--dir-mode`` /
    ``--file-mode`` options and the configured permission defaults.

    Args:
        value: The candidate literal.

    Returns:
        The parsed mode.

    Raises:
        ValueError: `value` is not a plain octal literal, or lies outside 0..0o7777.

    Example:
        >>> oct(parse_octal_mode_string("0o750"))
        '0o750'
        >>> parse_octal_mode_string("-1")
        Traceback (most recent call last):
        ...
        ValueError: Invalid octal mode '-1': not a plain octal literal
    """
    if not _OCTAL_MODE_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid octal mode {value!r}: not a plain octal literal")
    mode = int(value.removeprefix("0o"), 8)
    if mode > MAX_PERMISSION_MODE:
        raise ValueError(f"Invalid octal mode {value!r}: must be between 0 and {oct(MAX_PERMISSION_MODE)}")
    return mode


def check_deploy_mode(mode: int, *, is_directory: bool) -> None:
    """Refuse a mode that is unsafe for configuration that can hold secrets.

    The deployed directory and files can hold SMTP credentials, so a mode may widen access
    beyond the layer defaults (755/644 for app and host, 700/600 for user) but may not add a
    special bit, grant the world write access, or lock the owner out: a directory needs
    owner rwx to be entered and redeployed into, a file owner rw to be read and rewritten.

    Args:
        mode: A mode in 0..0o7777.
        is_directory: Whether the mode is for the configuration directory or its files.

    Raises:
        ValueError: The mode is unsafe; the message names every offending bit.

    Example:
        >>> check_deploy_mode(0o750, is_directory=True)
        >>> check_deploy_mode(0o4750, is_directory=True)
        Traceback (most recent call last):
        ...
        ValueError: unsafe mode 0o4750: the setuid bit (0o4000)
    """
    problems = [f"the {name} bit ({oct(bit)})" for bit, name in _SPECIAL_BITS if mode & bit]
    if mode & _WORLD_WRITE:
        problems.append(f"world-write ({oct(_WORLD_WRITE)})")
    owner = _OWNER_DIRECTORY if is_directory else _OWNER_FILE
    if mode & owner != owner:
        problems.append(f"no owner {'rwx' if is_directory else 'rw'} ({oct(owner)} is required)")
    if problems:
        raise ValueError(f"unsafe mode {oct(mode)}: {'; '.join(problems)}")


def parse_mode(value: int | str, default: int) -> int:
    """Parse a permission mode value from config.

    Accepts either an integer or an octal string (e.g., "0o755" or "755").

    Args:
        value: Integer mode or octal string.
        default: Fallback value if parsing fails.

    Returns:
        Integer permission mode.

    Example:
        >>> parse_mode(493, 0o755)
        493
        >>> parse_mode("0o755", 0o644)
        493
        >>> parse_mode("755", 0o644)
        493
    """
    if isinstance(value, int):
        return value
    # value is str at this point
    try:
        # Handle both "755" and "0o755" formats
        if value.startswith("0o"):
            return int(value, 0)  # int() auto-detects 0o prefix
        return int(value, 8)  # Plain "755" needs explicit base 8
    except ValueError:
        return default


def _parse_mode_from_section(section: dict[str, int | str | bool], key: str, default: int) -> int:
    """Extract and parse a mode value from a raw config section dict.

    Used only at the boundary when parsing the raw config dict into
    PermissionDefaults. The raw section comes from lib_layered_config's
    Config.get() which returns untyped dicts.
    """
    raw = section.get(key, default)
    if isinstance(raw, bool):
        return default
    return parse_mode(raw, default)


def get_permission_defaults(config: Config) -> PermissionDefaults:
    """Load permission defaults from [lib_layered_config.default_permissions].

    Reads configurable permission defaults for each deployment layer.
    Falls back to lib_layered_config library defaults if not configured.

    Args:
        config: Configuration object with merged settings.

    Returns:
        PermissionDefaults model with typed fields for each layer's
        directory and file modes, plus an enabled flag.

    Example:
        >>> from lib_layered_config import Config
        >>> config = Config({}, {})  # Empty config
        >>> defaults = get_permission_defaults(config)
        >>> defaults.user_directory == 0o700
        True
    """
    section = config.get("lib_layered_config", {}).get("default_permissions", {})
    # NOTE: lib_layered_config does not define separate HOST_* constants.
    # Host layer shares defaults with app layer (both world-readable: 755/644).
    # This is intentional per CLAUDE.md "Deployment Permissions" documentation.
    return PermissionDefaults(
        app_directory=_parse_mode_from_section(section, "app_directory", DEFAULT_APP_DIR_MODE),
        app_file=_parse_mode_from_section(section, "app_file", DEFAULT_APP_FILE_MODE),
        host_directory=_parse_mode_from_section(section, "host_directory", DEFAULT_APP_DIR_MODE),
        host_file=_parse_mode_from_section(section, "host_file", DEFAULT_APP_FILE_MODE),
        user_directory=_parse_mode_from_section(section, "user_directory", DEFAULT_USER_DIR_MODE),
        user_file=_parse_mode_from_section(section, "user_file", DEFAULT_USER_FILE_MODE),
        enabled=section.get("enabled", True),
    )


def get_modes_for_target(
    target: DeployTarget,
    config: Config,
    *,
    dir_mode_override: int | None = None,
    file_mode_override: int | None = None,
) -> tuple[int, int]:
    """Get dir_mode and file_mode for a target, applying overrides.

    Retrieves permission modes for a deployment target from configuration,
    then applies any CLI overrides. CLI overrides take precedence over
    configured defaults.

    Args:
        target: The deployment target layer (app, host, or user).
        config: Configuration object with merged settings.
        dir_mode_override: CLI override for directory mode. If provided,
            takes precedence over configuration.
        file_mode_override: CLI override for file mode. If provided,
            takes precedence over configuration.

    Returns:
        Tuple of (dir_mode, file_mode) to pass to deploy_config.
        Values are integers (octal mode values). Always returns valid modes
        since get_permission_defaults provides fallbacks for all targets.

    Example:
        >>> from lib_layered_config import Config
        >>> from bitranox_template_py_cli.domain.enums import DeployTarget
        >>> config = Config({}, {})
        >>> dir_mode, file_mode = get_modes_for_target(
        ...     DeployTarget.USER, config
        ... )
        >>> dir_mode == 0o700
        True
    """
    defaults = get_permission_defaults(config)
    layer = target.value  # "app", "host", or "user"

    dir_mode: int = dir_mode_override if dir_mode_override is not None else defaults.dir_mode_for(layer)
    file_mode: int = file_mode_override if file_mode_override is not None else defaults.file_mode_for(layer)

    return dir_mode, file_mode


__all__ = [
    "MAX_PERMISSION_MODE",
    "PermissionDefaults",
    "check_deploy_mode",
    "get_modes_for_target",
    "get_permission_defaults",
    "parse_mode",
    "parse_octal_mode_string",
]
