"""Convenience script to bump the patch version component.

Increments the patch version (X.Y.Z) in pyproject.toml and updates CHANGELOG.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .bump import bump

__all__ = ["bump_patch"]


def bump_patch(pyproject: Path = Path("pyproject.toml"), changelog: Path = Path("CHANGELOG.md")) -> None:
    """Bump the patch version component.

    Args:
        pyproject: Path to pyproject.toml file.
        changelog: Path to CHANGELOG.md file.
    """
    bump(part="patch", pyproject=pyproject, changelog=changelog)


if __name__ == "__main__":  # pragma: no cover
    from .cli import main as cli_main

    cli_main(["bump", "--part", "patch", *sys.argv[1:]])
