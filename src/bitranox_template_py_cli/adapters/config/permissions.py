"""Permission settings for config deployment.

Reads ``[lib_layered_config.default_permissions]`` into a validated model and computes the
directory and file mode ``config-deploy`` applies to each target layer. The section is part
of this application's configuration (lib_layered_config's own ``deploy_config`` only knows
its built-in layer defaults), so these settings take effect only because ``config-deploy``
passes each target's modes explicitly.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Final

from lib_layered_config import (
    DEFAULT_APP_DIR_MODE,
    DEFAULT_APP_FILE_MODE,
    DEFAULT_USER_DIR_MODE,
    DEFAULT_USER_FILE_MODE,
)
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, ValidationError

from bitranox_template_py_cli.domain.errors import ConfigurationError

if TYPE_CHECKING:
    from lib_layered_config import Config

    from bitranox_template_py_cli.domain.enums import DeployTarget

#: chmod(2) defines only the low 12 bits (setuid, setgid, sticky and rwxrwxrwx).
MAX_PERMISSION_MODE: Final[int] = 0o7777

#: A plain octal literal: an optional lowercase ``0o`` prefix, then octal digits, nothing
#: else. A bare ``int(value, 8)`` would also accept surrounding whitespace, ``_`` digit
#: separators and non-ASCII decimal digits, and ``int(value, 0)`` a sign or another base.
_OCTAL_MODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?:0o)?[0-7]+")

#: The special bits no deployed configuration directory or file may carry.
_SPECIAL_BITS: Final[tuple[tuple[int, str], ...]] = ((0o4000, "setuid"), (0o2000, "setgid"), (0o1000, "sticky"))
_GROUP_WRITE: Final[int] = 0o020
_WORLD_WRITE: Final[int] = 0o002
#: Execute for owner, group and other: a configuration file is never run.
_ANY_EXECUTE: Final[int] = 0o111
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

    The deployed directory and files can hold SMTP credentials, so a mode may widen READ
    access beyond the layer defaults (755/644 for app and host, 700/600 for user) but may
    not add a special bit, grant the group or the world write access, put an execute bit
    on a file, or lock the owner out: a directory needs owner rwx to be entered and
    redeployed into, a file owner rw to be read and rewritten. Group write counts like
    world write because a group can be every local account (``staff`` on macOS), and a
    file never needs x, so an x bit on one is the typical sign of a mistyped mode.

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
    if mode & _GROUP_WRITE:
        problems.append(f"group-write ({oct(_GROUP_WRITE)})")
    if mode & _WORLD_WRITE:
        problems.append(f"world-write ({oct(_WORLD_WRITE)})")
    if not is_directory and mode & _ANY_EXECUTE:
        problems.append(f"execute on a file ({oct(mode & _ANY_EXECUTE)})")
    owner = _OWNER_DIRECTORY if is_directory else _OWNER_FILE
    if mode & owner != owner:
        problems.append(f"no owner {'rwx' if is_directory else 'rw'} ({oct(owner)} is required)")
    if problems:
        raise ValueError(f"unsafe mode {oct(mode)}: {'; '.join(problems)}")


def _to_mode(value: object) -> int:
    """Pydantic before-validator: a plain octal string, as a mode in 0..0o7777.

    An integer is refused, never reinterpreted: TOML ``user_file = 400``, ``--set ...=400``
    and an environment value ``400`` all arrive as the DECIMAL integer 400, which is
    ``0o620`` (group-writable) and not the owner-read-only mode the digits suggest. Reading
    it as octal instead would make the same digits mean different modes in a string and an
    integer, so the only unambiguous form is the string, and the refusal says so.

    A malformed or out-of-range string is refused too; a silent fallback to the layer
    default would hide a typo in a setting that guards credentials. Every refusal is a
    ``ValueError``, which pydantic reports as a ``value_error`` carrying it;
    :func:`_describe` prints its message.
    """
    if isinstance(value, str):
        return parse_octal_mode_string(value)
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError(
            f"a bare integer is read as decimal ({value} = {oct(value)}); "
            'write the mode as an octal string such as "0o640" instead'
        )
    raise ValueError(f"expected an octal string, got {type(value).__name__}")


def _safe_directory_mode(mode: int) -> int:
    """Pydantic after-validator: refuse a directory mode :func:`check_deploy_mode` rejects."""
    check_deploy_mode(mode, is_directory=True)
    return mode


def _safe_file_mode(mode: int) -> int:
    """Pydantic after-validator: refuse a file mode :func:`check_deploy_mode` rejects."""
    check_deploy_mode(mode, is_directory=False)
    return mode


DirectoryMode = Annotated[int, BeforeValidator(_to_mode), AfterValidator(_safe_directory_mode)]
FileMode = Annotated[int, BeforeValidator(_to_mode), AfterValidator(_safe_file_mode)]


class PermissionDefaults(BaseModel):
    """Validated, immutable permission defaults for deployment layers.

    Parsed at the boundary from the ``[lib_layered_config.default_permissions]`` section.
    Every field falls back to lib_layered_config's layer default; the host layer shares the
    app layer's (lib_layered_config defines no separate host constants). An unknown key is
    refused rather than ignored, so a misspelt setting cannot silently not apply.

    Example:
        >>> defaults = PermissionDefaults()
        >>> defaults.user_directory == 0o700
        True
        >>> oct(PermissionDefaults.model_validate({"user_directory": "750"}).user_directory)
        '0o750'
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    app_directory: DirectoryMode = DEFAULT_APP_DIR_MODE
    app_file: FileMode = DEFAULT_APP_FILE_MODE
    host_directory: DirectoryMode = DEFAULT_APP_DIR_MODE
    host_file: FileMode = DEFAULT_APP_FILE_MODE
    user_directory: DirectoryMode = DEFAULT_USER_DIR_MODE
    user_file: FileMode = DEFAULT_USER_FILE_MODE
    enabled: bool = True

    def dir_mode_for(self, layer: str) -> int:
        """Return directory mode for the given layer name."""
        return getattr(self, f"{layer}_directory")

    def file_mode_for(self, layer: str) -> int:
        """Return file mode for the given layer name."""
        return getattr(self, f"{layer}_file")


class _LayeredConfigSection(BaseModel):
    """The ``[lib_layered_config]`` section, as far as this module reads it."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    default_permissions: PermissionDefaults = Field(default_factory=PermissionDefaults)


_SECTION: Final[str] = "lib_layered_config"


def _describe(error: ValidationError) -> str:
    """Render a validation error as one line: ``<dotted key>: <reason>`` per problem."""
    problems: list[str] = []
    for item in error.errors():
        key = ".".join((_SECTION, *(str(part) for part in item["loc"])))
        # pydantic prefixes the message of a ValueError raised by our validators with
        # "Value error, "; the exception it carries holds the message as written.
        raised = item.get("ctx", {}).get("error")
        problems.append(f"{key}: {raised if isinstance(raised, ValueError) else item['msg']}")
    return "; ".join(problems).replace("\n", " ")


def get_permission_defaults(config: Config) -> PermissionDefaults:
    """Load permission defaults from ``[lib_layered_config.default_permissions]``.

    Args:
        config: Configuration object with merged settings.

    Returns:
        PermissionDefaults with each layer's directory and file mode and the enabled flag;
        lib_layered_config's layer defaults where nothing is configured.

    Raises:
        ConfigurationError: A value is malformed, out of range, unsafe or of the wrong type,
            the section is not a table, or it holds an unknown key. The message is one line
            naming each offending key.

    Example:
        >>> from lib_layered_config import Config
        >>> get_permission_defaults(Config({}, {})).user_directory == 0o700
        True
        >>> get_permission_defaults(Config({"lib_layered_config": {"default_permissions": {"enabled": "maybe"}}}, {}))
        Traceback (most recent call last):
        ...
        bitranox_template_py_cli.domain.errors.ConfigurationError: lib_layered_config.default_permissions.enabled: ...
    """
    raw: object = config.get(_SECTION, default={})
    try:
        return _LayeredConfigSection.model_validate(raw).default_permissions
    except ValidationError as exc:
        raise ConfigurationError(_describe(exc)) from exc


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

    Raises:
        ConfigurationError: The configured permission defaults are invalid; see
            :func:`get_permission_defaults`.

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
    "DirectoryMode",
    "FileMode",
    "PermissionDefaults",
    "check_deploy_mode",
    "get_modes_for_target",
    "get_permission_defaults",
    "parse_octal_mode_string",
]
