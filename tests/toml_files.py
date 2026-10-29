"""Read a TOML file in the tests, on every interpreter the CI matrix runs.

rtoml ships no free-threaded build, so the dev install carries it only below Python 3.14 (no
marker tells 3.14t from 3.14). The standard library's tomllib reads TOML from 3.11 on, which
leaves rtoml for 3.10 alone. The branch is on ``sys.version_info`` because the type checker
narrows on it, so each interpreter's checker sees only the module it can import.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib

    def read_toml(path: Path) -> dict[str, Any]:
        """Parse the TOML file at ``path``."""
        with path.open("rb") as handle:
            return tomllib.load(handle)

else:
    import rtoml

    def read_toml(path: Path) -> dict[str, Any]:
        """Parse the TOML file at ``path``."""
        return rtoml.load(path)


__all__ = ["read_toml"]
