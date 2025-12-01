"""Entry point for ``python -m scripts`` invocation.

Delegates to the CLI main function to provide access to all development
automation commands.
"""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":  # pragma: no cover
    main()
