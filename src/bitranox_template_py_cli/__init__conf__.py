"""Runtime metadata facade kept in sync with the installed distribution.

Purpose
-------
Expose key package metadata (name, version, homepage, author) as simple module
attributes so that CLI commands and documentation can present authoritative
information without parsing project files at runtime.

Contents
--------
* Module-level constants provide defaults when distribution metadata is absent.
* :class:`PackagePortrait` captures the fields presented to end users.
* Helper functions (``_load_metadata`` … ``_shell_command``) compose the
  portrait while making each fallback explicit.
* :func:`print_info` renders the portrait for the CLI ``info`` command.

System Role
-----------
Lives in the adapters/platform layer: domain code does not depend on these
details, but transports and tooling reference them to keep messages and release
automation consistent with the published package.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata as _im
from typing import Any, Iterable

#: Distribution name declared in ``pyproject.toml``.
_DIST_NAME = "bitranox_template_py_cli"
#: Summary shown when real metadata is unavailable.
_DEFAULT_SUMMARY = "Rich-powered logging helpers for colorful terminal output"
#: Repository URL used as a fallback homepage.
_DEFAULT_HOMEPAGE = "https://github.com/bitranox/bitranox_template_py_cli"
#: Default author attribution used when metadata is missing.
_DEFAULT_AUTHOR = "bitranox"
#: Default author email used when metadata is missing.
_DEFAULT_EMAIL = "bitranox@gmail.com"


@dataclass(frozen=True)
class PackagePortrait:
    """Snapshot describing the package presentation to end users.

    Attributes
    ----------
    name:
        Distribution name registered in ``pyproject.toml``.
    title:
        Human readable summary shown in CLI help.
    version:
        Installed version or the development fallback.
    homepage:
        URL shown in ``print_info`` and metadata output.
    author / author_email:
        Attribution drawn from package metadata or defaults.
    shell_command:
        Console-script name surfaced to users.
    """

    name: str
    title: str
    version: str
    homepage: str
    author: str
    author_email: str
    shell_command: str


def _load_metadata(dist_name: str) -> Any | None:
    """Return the installed metadata mapping for ``dist_name`` when available.

    Why
        ``print_info`` needs to present authoritative package details. Fetching
        once lets us cache the portrait.

    Inputs
        dist_name:
            Distribution name to query via :mod:`importlib.metadata`.

    Outputs
        Mapping or ``None`` when the distribution is not installed yet.
    """

    try:
        return _im.metadata(dist_name)
    except _im.PackageNotFoundError:
        return None


def _load_version(dist_name: str) -> str:
    """Return the installed version for ``dist_name`` or the dev fallback."""

    try:
        return _im.version(dist_name)
    except _im.PackageNotFoundError:
        return "0.0.0.dev0"


def _metadata_field(metadata: Any | None, key: str, default: str) -> str:
    """Fetch a string field from ``metadata`` while enforcing the default."""

    if metadata is None:
        return default
    candidate = metadata.get(key, default)  # type: ignore[call-arg]
    return candidate if isinstance(candidate, str) else default


def _resolve_homepage(metadata: Any | None) -> str:
    """Return the homepage URL to show in ``print_info``."""

    primary = _metadata_field(metadata, "Home-page", "")
    fallback = _metadata_field(metadata, "Homepage", "")
    return primary or fallback or _DEFAULT_HOMEPAGE


def _resolve_author(metadata: Any | None) -> tuple[str, str]:
    """Return the ``(name, email)`` pair describing the package author."""

    if metadata is None:
        return (_DEFAULT_AUTHOR, _DEFAULT_EMAIL)
    author_name = _metadata_field(metadata, "Author", _DEFAULT_AUTHOR)
    author_mail = _metadata_field(metadata, "Author-email", _DEFAULT_EMAIL)
    return (author_name, author_mail)


def _resolve_summary(metadata: Any | None) -> str:
    """Return the human-readable summary string for the package."""

    return _metadata_field(metadata, "Summary", _DEFAULT_SUMMARY)


def _shell_command(entry_points: Iterable[Any] | None = None) -> str:
    """Return the console-script name associated with the CLI entry point."""

    target = "bitranox_template_py_cli.cli:main"
    entries = entry_points if entry_points is not None else _im.entry_points(group="console_scripts")
    for entry in list(entries):
        if getattr(entry, "value", None) == target:
            return getattr(entry, "name")
    return _DIST_NAME


def _describe_package(dist_name: str = _DIST_NAME) -> PackagePortrait:
    """Gather metadata, fallbacks, and entry-point details into a portrait."""

    metadata = _load_metadata(dist_name)
    author_name, author_mail = _resolve_author(metadata)
    return PackagePortrait(
        name=dist_name,
        title=_resolve_summary(metadata),
        version=_load_version(dist_name),
        homepage=_resolve_homepage(metadata),
        author=author_name,
        author_email=author_mail,
        shell_command=_shell_command(),
    )


_PORTRAIT = _describe_package()

name = _PORTRAIT.name
title = _PORTRAIT.title
version = _PORTRAIT.version
homepage = _PORTRAIT.homepage
author = _PORTRAIT.author
author_email = _PORTRAIT.author_email
shell_command = _PORTRAIT.shell_command


def print_info() -> None:
    """Print the summarised metadata block used by the CLI ``info`` command."""

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
