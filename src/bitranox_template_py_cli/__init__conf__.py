"""Package metadata via importlib.metadata - all values derived from pyproject.toml.

When copying this template project, update only pyproject.toml. All values here
are derived automatically from the installed package metadata.

Contents:
    * Metadata properties sourced from installed package metadata.
    * LAYEREDCONF_* constants derived for lib_layered_config path resolution.
    * :func:`print_info` rendering metadata for the CLI ``info`` command.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.metadata import metadata


@lru_cache(maxsize=1)
def _get_package_name() -> str:
    """Get the package name from the module path."""
    return __name__.rsplit(".", 1)[0]


@lru_cache(maxsize=1)
def _get_metadata() -> dict[str, str]:
    """Load package metadata once and cache it."""
    package_name = _get_package_name()
    meta = metadata(package_name)

    # Extract author name and email from "Author-email: Name <email>" format
    author_email_raw = meta.get("Author-email", "")
    author_name = ""
    author_email_addr = ""
    if "<" in author_email_raw and ">" in author_email_raw:
        author_name = author_email_raw.split("<")[0].strip()
        author_email_addr = author_email_raw.split("<")[1].rstrip(">").strip()

    # Get homepage from Project-URL (format: "Homepage, https://...")
    homepage_url = ""
    for url_line in meta.get_all("Project-URL") or []:
        if url_line.startswith("Homepage,"):
            homepage_url = url_line.split(",", 1)[1].strip()
            break

    # Get package name and derive slug/shell_command
    pkg_name = meta.get("Name", package_name)

    return {
        "name": pkg_name,
        "version": meta.get("Version", "0.0.0"),
        "summary": meta.get("Summary", ""),
        "homepage": homepage_url,
        "author": author_name,
        "author_email": author_email_addr,
    }


def _to_kebab_case(value: str) -> str:
    """Convert package name to kebab-case slug."""
    return value.replace("_", "-").lower()


def _to_title_case(value: str) -> str:
    """Convert package name to Title Case display name."""
    return " ".join(word.capitalize() for word in value.replace("_", " ").replace("-", " ").split())


# Module-level variables computed directly from metadata (no global statements)
_meta = _get_metadata()

name: str = _meta["name"]
title: str = _meta["summary"]
version: str = _meta["version"]
homepage: str = _meta["homepage"]
author: str = _meta["author"]
author_email: str = _meta["author_email"]
shell_command: str = _to_kebab_case(name)

# lib_layered_config path resolution constants
LAYEREDCONF_VENDOR: str = author or name.split("_")[0]  # First word if no author
LAYEREDCONF_APP: str = _to_title_case(name)
LAYEREDCONF_SLUG: str = shell_command


def print_info() -> None:
    """Print the summarised metadata block used by the CLI ``info`` command.

    Side Effects:
        Writes to ``stdout``.

    Examples:
        >>> print_info()  # doctest: +ELLIPSIS
        Info for ...:
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
