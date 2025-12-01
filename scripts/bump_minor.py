"""Convenience script to bump the minor version component.

Increments the minor version (X.Y.0) in pyproject.toml and updates CHANGELOG.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .bump import bump

__all__ = ["bump_minor"]


def bump_minor(pyproject: Path = Path("pyproject.toml"), changelog: Path = Path("CHANGELOG.md")) -> None:
    """Bump the minor version component.

    Args:
        pyproject: Path to pyproject.toml file.
        changelog: Path to CHANGELOG.md file.
    """
    bump(part="minor", pyproject=pyproject, changelog=changelog)


if __name__ == "__main__":  # pragma: no cover
    from .cli import main as cli_main

    cli_main(["bump", "--part", "minor", *sys.argv[1:]])
