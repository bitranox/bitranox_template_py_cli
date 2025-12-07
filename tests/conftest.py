"""Shared pytest fixtures for CLI and module-entry tests.

Centralizes fixtures used across multiple test modules:
- CLI runner instances
- ANSI code stripping
- lib_cli_exit_tools configuration preservation
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import pytest
from click.testing import CliRunner

import lib_cli_exit_tools

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


# ---------------------------------------------------------------------------
# Configuration Snapshot Model
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class CLIConfigSnapshot:
    """Immutable snapshot of lib_cli_exit_tools configuration.

    Attributes:
        traceback: Whether traceback mode is enabled.
        traceback_force_color: Whether color is forced in tracebacks.
        exit_code_style: Style for exit codes.
        broken_pipe_exit_code: Exit code for broken pipe errors.
    """

    traceback: bool
    traceback_force_color: bool
    exit_code_style: str
    broken_pipe_exit_code: int

    @classmethod
    def capture(cls) -> "CLIConfigSnapshot":
        """Capture current lib_cli_exit_tools configuration."""
        config = lib_cli_exit_tools.config
        return cls(
            traceback=bool(getattr(config, "traceback", False)),
            traceback_force_color=bool(getattr(config, "traceback_force_color", False)),
            exit_code_style=str(getattr(config, "exit_code_style", "errno")),
            broken_pipe_exit_code=int(getattr(config, "broken_pipe_exit_code", 141)),
        )

    def restore(self) -> None:
        """Restore this snapshot to lib_cli_exit_tools configuration."""
        config = lib_cli_exit_tools.config
        setattr(config, "traceback", self.traceback)
        setattr(config, "traceback_force_color", self.traceback_force_color)
        setattr(config, "exit_code_style", self.exit_code_style)
        setattr(config, "broken_pipe_exit_code", self.broken_pipe_exit_code)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text.

    Args:
        text: String potentially containing ANSI codes.

    Returns:
        String with all ANSI escape sequences removed.
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a fresh Click CliRunner for each test."""
    return CliRunner()


@pytest.fixture
def strip_ansi() -> Callable[[str], str]:
    """Provide a helper function that strips ANSI codes from strings."""
    return strip_ansi_codes


@pytest.fixture
def preserve_traceback_state() -> Iterator[None]:
    """Preserve and restore lib_cli_exit_tools configuration around test."""
    snapshot = CLIConfigSnapshot.capture()
    try:
        yield
    finally:
        snapshot.restore()


@pytest.fixture
def isolated_traceback_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset traceback flags to a known baseline before each test."""
    lib_cli_exit_tools.reset_config()
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)
