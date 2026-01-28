"""Shared pytest fixtures for CLI and module-entry tests.

Centralizes test infrastructure following clean architecture principles:
- All shared fixtures live here
- Tests import fixtures implicitly via pytest's conftest discovery
- Fixtures use descriptive names that read as plain English
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import fields
from pathlib import Path
from typing import Any

import lib_cli_exit_tools
import pytest
from click.testing import CliRunner
from lib_layered_config import Config

_COVERAGE_BASENAME = ".coverage.bitranox_template_py_cli"


def _purge_stale_coverage_files(cov_path: Path) -> None:
    """Delete leftover SQLite database and journal files from crashed runs.

    A prior crash can leave ``-journal``, ``-wal``, or ``-shm`` sidecar
    files next to the coverage database.  SQLite interprets those as an
    incomplete transaction and may raise ``database is locked`` on the
    next open.
    """
    for suffix in ("", "-journal", "-wal", "-shm"):
        with contextlib.suppress(FileNotFoundError):
            Path(str(cov_path) + suffix).unlink()


def pytest_configure(config: pytest.Config) -> None:
    """Redirect the coverage database to a **local** temp directory.

    coverage.py stores trace data in a SQLite database.  SQLite requires
    POSIX file-locking semantics that network mounts (SMB / NFS) do not
    reliably provide, and stale journal files from a previous crash can
    trigger *"database is locked"* on Python 3.14's free-threaded build.

    This hook runs **before** ``pytest-cov``'s ``pytest_sessionstart``
    creates the ``Coverage()`` object, so the ``COVERAGE_FILE`` value is
    picked up regardless of how pytest is invoked (CI, ``make test``,
    bare ``pytest --cov``).
    """
    if "COVERAGE_FILE" not in os.environ:
        cov_path = Path(tempfile.gettempdir()) / _COVERAGE_BASENAME
        _purge_stale_coverage_files(cov_path)
        os.environ["COVERAGE_FILE"] = str(cov_path)


def _load_dotenv() -> None:
    """Load .env file when it exists for integration test configuration."""
    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass


_load_dotenv()

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
CONFIG_FIELDS: tuple[str, ...] = tuple(field.name for field in fields(type(lib_cli_exit_tools.config)))


def _remove_ansi_codes(text: str) -> str:
    """Return *text* stripped of ANSI escape sequences."""
    return ANSI_ESCAPE_PATTERN.sub("", text)


def _snapshot_cli_config() -> dict[str, object]:
    """Capture every attribute from ``lib_cli_exit_tools.config``."""
    return {name: getattr(lib_cli_exit_tools.config, name) for name in CONFIG_FIELDS}


def _restore_cli_config(snapshot: dict[str, object]) -> None:
    """Reapply a configuration snapshot captured by ``_snapshot_cli_config``."""
    for name, value in snapshot.items():
        setattr(lib_cli_exit_tools.config, name, value)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a fresh CliRunner per test.

    Click 8.x provides separate result.stdout and result.stderr attributes.
    Use result.stdout for clean output (e.g., JSON parsing) to avoid
    async log messages from stderr contaminating the output.
    """
    return CliRunner()


@pytest.fixture
def strip_ansi() -> Callable[[str], str]:
    """Return a helper that strips ANSI escape sequences from a string."""

    def _strip(value: str) -> str:
        return _remove_ansi_codes(value)

    return _strip


@pytest.fixture
def preserve_traceback_state() -> Iterator[None]:
    """Snapshot and restore the entire lib_cli_exit_tools configuration."""
    snapshot = _snapshot_cli_config()
    try:
        yield
    finally:
        _restore_cli_config(snapshot)


@pytest.fixture
def isolated_traceback_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset traceback flags to a known baseline before each test."""
    lib_cli_exit_tools.reset_config()
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)


@pytest.fixture
def clear_config_cache() -> Iterator[None]:
    """Clear the get_config lru_cache before each test.

    Note: Only clears before, not after, to avoid errors when the function
    has been monkeypatched during the test (losing cache_clear method).
    """
    from bitranox_template_py_cli.adapters.config import loader as config_mod

    config_mod.get_config.cache_clear()
    yield


@pytest.fixture
def config_factory() -> Callable[[dict[str, Any]], Config]:
    """Create real Config instances from test data dicts."""

    def _factory(data: dict[str, Any]) -> Config:
        return Config(data, {})

    return _factory


@pytest.fixture
def inject_config(
    monkeypatch: pytest.MonkeyPatch,
    clear_config_cache: None,
) -> Callable[[Config], None]:
    """Inject a Config into the CLI's get_config path.

    Monkeypatches get_config to return a pre-built real Config object,
    avoiding filesystem I/O while exercising the real Config API.
    """
    from bitranox_template_py_cli.adapters.config import loader as config_mod

    def _inject(config: Config) -> None:
        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        monkeypatch.setattr(config_mod, "get_config", _fake_get_config)

    return _inject
