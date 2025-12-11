"""Static package metadata surfaced to CLI commands and documentation.

Exposes the current project metadata as simple constants. These values are kept
in sync with ``pyproject.toml`` by development automation (tests, push
pipelines), so runtime code does not query packaging metadata.

Attributes:
    name: Distribution name declared in ``pyproject.toml``.
    title: Human-readable summary shown in CLI help output.
    version: Current release version pulled from ``pyproject.toml``.
    homepage: Repository homepage presented to users.
    author: Author attribution surfaced in CLI output.
    author_email: Contact email surfaced in CLI output.
    shell_command: Console-script name published by the package.

Functions:
    print_info: Renders the constants for the CLI ``info`` command.

Note:
    Lives in the adapters/platform layer; CLI transports import these constants
    to present authoritative project information without invoking packaging APIs.
"""

from __future__ import annotations

#: Distribution name declared in ``pyproject.toml``.
name = "bitranox_template_py_cli"
#: Human-readable summary shown in CLI help output.
title = "Template for python apps with registered cli commands"
#: Current release version pulled from ``pyproject.toml`` by automation.
version = "1.9.0"
#: Repository homepage presented to users.
homepage = "https://github.com/bitranox/bitranox_template_py_cli"
#: Author attribution surfaced in CLI output.
author = "bitranox"
#: Contact email surfaced in CLI output.
author_email = "bitranox@gmail.com"
#: Console-script name published by the package.
shell_command = "bitranox-template-py-cli"

#: Vendor identifier for lib_layered_config paths (macOS/Windows)
LAYEREDCONF_VENDOR: str = "bitranox"
#: Application display name for lib_layered_config paths (macOS/Windows)
LAYEREDCONF_APP: str = "Bitranox Template Py Cli"
#: Configuration slug for lib_layered_config Linux paths and environment variables
LAYEREDCONF_SLUG: str = "bitranox-template-py-cli"


def print_info() -> None:
    """Print the summarised metadata block used by the CLI ``info`` command.

    Provides a single, auditable rendering function so documentation and CLI
    output always match the system design reference.

    Note:
        Writes to ``stdout``.

    Example:
        >>> print_info()  # doctest: +ELLIPSIS
        Info for bitranox_template_py_cli:
        ...
    """

    fields = [
        ("name", name),
        ("title", title),
        ("version", version),
        ("homepage", homepage),
        ("author", author),
        ("author_email", author_email),
        ("shell_command", shell_command),
    ]
    pad = max(len(label) for label, _ in fields)
    lines = [f"Info for {name}:", ""]
    lines.extend(f"    {label.ljust(pad)} = {value}" for label, value in fields)
    print("\n".join(lines))
