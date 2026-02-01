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
from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

import lib_cli_exit_tools
import pytest
from click.testing import CliRunner
from lib_layered_config import Config
from lib_layered_config.domain.config import SourceInfo

if TYPE_CHECKING:
    from bitranox_template_py_cli.adapters.memory.email import EmailSpy

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
def production_factory() -> Callable[[], Any]:
    """Provide the production services factory for tests.

    Use this when invoking CLI commands that don't need custom injection.

    Example:
        result = cli_runner.invoke(cli, ["config"], obj=production_factory)
    """
    from bitranox_template_py_cli.composition import build_production

    return build_production


@pytest.fixture
def strip_ansi() -> Callable[[str], str]:
    """Return a helper that strips ANSI escape sequences from a string."""

    def _strip(value: str) -> str:
        return _remove_ansi_codes(value)

    return _strip


@pytest.fixture
def managed_traceback_state() -> Iterator[None]:
    """Reset traceback flags to a known baseline and restore after the test.

    Combines the responsibilities of the former ``isolated_traceback_config``
    (reset to clean state) and ``preserve_traceback_state`` (snapshot/restore)
    into a single fixture.  Use this whenever a test reads or mutates the
    global ``lib_cli_exit_tools.config`` traceback flags.
    """
    lib_cli_exit_tools.reset_config()
    lib_cli_exit_tools.config.traceback = False
    lib_cli_exit_tools.config.traceback_force_color = False
    snapshot = _snapshot_cli_config()
    try:
        yield
    finally:
        _restore_cli_config(snapshot)


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
def source_info_factory() -> Callable[[str, str, str | None], SourceInfo]:
    """Create SourceInfo dicts for provenance-tracking tests.

    Reduces coupling to the SourceInfo TypedDict structure.  If
    ``lib_layered_config`` adds or renames keys, only this factory
    needs updating.
    """

    def _factory(key: str, layer: str, path: str | None = None) -> SourceInfo:
        return {"layer": layer, "path": path, "key": key}

    return _factory


@pytest.fixture
def email_ready_config(config_factory: Callable[[dict[str, Any]], Config]) -> Config:
    """Create a Config pre-loaded with standard email settings for tests.

    Provides a reusable email configuration with smtp_hosts, from_address,
    and recipients so email tests do not repeat the same setup boilerplate.
    Combine with ``inject_config`` to wire into the CLI path:

        inject_config(email_ready_config)
    """
    return config_factory(
        {
            "email": {
                "smtp_hosts": ["smtp.test.com:587"],
                "from_address": "sender@test.com",
                "recipients": ["recipient@test.com"],
                "subject_prefix": "[TEST] ",
            }
        }
    )


@pytest.fixture
def inject_config(
    clear_config_cache: None,
) -> Callable[[Config], Callable[[], Any]]:
    """Return a factory that provides test services with injected Config.

    Creates a services factory with the injected config loader,
    avoiding filesystem I/O while exercising the real Config API.

    Returns:
        Function that accepts a Config and returns a services factory callable.

    Example:
        factory = inject_config(config_factory({"section": {"key": "value"}}))
        result = cli_runner.invoke(cli, ["config"], obj=factory)
    """
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _inject(config: Config) -> Callable[[], Any]:
        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        prod = build_production()
        test_services = AppServices(
            get_config=_fake_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_config_with_profile_capture(
    clear_config_cache: None,
) -> Callable[[Config, list[str | None]], Callable[[], Any]]:
    """Return a factory that captures profile arguments during get_config.

    Creates a services factory with a get_config that records profile
    arguments for assertion in tests.

    Args:
        config: The Config to return.
        captured_profiles: A list to append captured profile values to.

    Returns:
        Function that accepts (Config, capture_list) and returns a services factory.
    """
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _inject(config: Config, captured_profiles: list[str | None]) -> Callable[[], Any]:
        def _capturing_get_config(*, profile: str | None = None, **_kwargs: Any) -> Config:
            captured_profiles.append(profile)
            return config

        prod = build_production()
        test_services = AppServices(
            get_config=_capturing_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_deploy_with_profile_capture(
    clear_config_cache: None,
) -> Callable[[Path, list[str | None]], Callable[[], Any]]:
    """Return a factory with deploy_configuration that captures profile arguments.

    Creates a services factory with a deploy_configuration that records
    profile arguments for assertion in tests.

    Returns:
        Function that accepts (deployed_path, capture_list) and returns a services factory.
    """
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _inject(deployed_path: Path, captured_profiles: list[str | None]) -> Callable[[], Any]:
        def _capturing_deploy(
            *,
            targets: Any,
            force: bool = False,
            profile: str | None = None,
            set_permissions: bool = True,
            dir_mode: int | None = None,
            file_mode: int | None = None,
        ) -> list[Path]:
            captured_profiles.append(profile)
            return [deployed_path]

        prod = build_production()
        test_services = AppServices(
            get_config=prod.get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=_capturing_deploy,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_deploy_configuration() -> Callable[[Callable[..., list[Path]]], Callable[[], Any]]:
    """Return a factory with a custom deploy_configuration function.

    Creates a services factory with the provided deploy_configuration
    function while keeping other services as production.

    Returns:
        Function that accepts a deploy function and returns a services factory.
    """
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _inject(deploy_fn: Callable[..., list[Path]]) -> Callable[[], Any]:
        prod = build_production()
        test_services = AppServices(
            get_config=prod.get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=deploy_fn,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_test_services() -> Callable[[], Callable[[], Any]]:
    """Return the build_testing factory for full in-memory testing.

    For full service replacement. Use inject_email_services for
    granular email-only testing.

    Returns:
        Function that returns the build_testing factory.

    Example:
        factory = inject_test_services()
        result = cli_runner.invoke(cli, ["config"], obj=factory)
    """
    from bitranox_template_py_cli.composition import build_testing

    def _inject() -> Callable[[], Any]:
        return build_testing

    return _inject


@dataclass
class EmailCliContext:
    """Container for email CLI test setup.

    Bundles the services factory and email spy together for tests that need
    both email configuration and email capture assertions.

    Attributes:
        factory: Callable that returns wired AppServices for CLI invocation.
        spy: EmailSpy instance for asserting on sent emails/notifications.
    """

    factory: Callable[[], Any]
    spy: EmailSpy


@pytest.fixture
def email_cli_context(
    clear_config_cache: None,
) -> Callable[[dict[str, Any]], EmailCliContext]:
    """Create email CLI test context with configured factory and spy.

    Combines config creation, injection, and email service replacement
    into a single fixture. Returns a function that takes email config
    dict (the "email" section contents) and returns a context with
    the wired factory and spy.

    Example:
        def test_send_email(cli_runner, email_cli_context):
            ctx = email_cli_context({"smtp_hosts": ["smtp.test.com:587"], ...})
            result = cli_runner.invoke(cli, [...], obj=ctx.factory)
            assert ctx.spy.sent_emails[0]["subject"] == "Test"
    """
    from bitranox_template_py_cli.adapters.memory import load_email_config_from_dict_in_memory
    from bitranox_template_py_cli.adapters.memory.email import EmailSpy
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _create(email_data: dict[str, Any]) -> EmailCliContext:
        spy = EmailSpy()
        config = Config({"email": email_data}, {})
        prod = build_production()

        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        test_services = AppServices(
            get_config=_fake_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            send_email=spy.send_email,
            send_notification=spy.send_notification,
            load_email_config_from_dict=load_email_config_from_dict_in_memory,
            init_logging=prod.init_logging,
        )
        return EmailCliContext(factory=lambda: test_services, spy=spy)

    return _create


@pytest.fixture
def config_cli_context(
    clear_config_cache: None,
) -> Callable[[dict[str, Any]], Callable[[], Any]]:
    """Create CLI test context with injected config.

    Combines config creation and injection into a single fixture.
    Returns a function that takes config dict and returns a services factory.

    Example:
        def test_config(cli_runner, config_cli_context):
            factory = config_cli_context({"section": {"key": "value"}})
            result = cli_runner.invoke(cli, ["config"], obj=factory)
    """
    from bitranox_template_py_cli.composition import AppServices, build_production

    def _create(config_data: dict[str, Any]) -> Callable[[], Any]:
        config = Config(config_data, {})
        prod = build_production()

        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        test_services = AppServices(
            get_config=_fake_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _create
