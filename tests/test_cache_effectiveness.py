"""Verify configuration loading returns consistent results.

Tests that ``get_config()`` and ``get_default_config_path()`` return
correct and consistent data across multiple calls.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.os_agnostic
class TestGetDefaultConfigPath:
    """Verify get_default_config_path() behavior."""

    def test_returns_toml_path(self) -> None:
        """The returned path points to a .toml file."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        result = get_default_config_path()

        assert result.suffix == ".toml"

    def test_repeated_calls_return_equal_paths(self) -> None:
        """Repeated calls return equal Path values."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        first = get_default_config_path()
        second = get_default_config_path()

        assert first == second


@pytest.mark.os_agnostic
class TestGetConfig:
    """Verify get_config() behavior."""

    def test_returns_config_with_dict(self) -> None:
        """get_config() returns a Config with a valid dict."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        config = get_config()

        assert isinstance(config.as_dict(), dict)

    def test_repeated_calls_return_equivalent_data(self) -> None:
        """Repeated calls return Config with equivalent data."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        first = get_config()
        second = get_config()

        assert first.as_dict() == second.as_dict()


@pytest.mark.os_agnostic
class TestConcurrentAccess:
    """Verify consistent results under concurrent access."""

    def test_concurrent_get_config_returns_equivalent_results(self) -> None:
        """All threads receive equivalent Config data."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(get_config) for _ in range(10)]
            results = [f.result() for f in futures]

        first_dict = results[0].as_dict()
        assert all(r.as_dict() == first_dict for r in results)

    def test_concurrent_get_default_config_path_returns_equal_results(self) -> None:
        """All threads receive equal Path values."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(get_default_config_path) for _ in range(10)]
            results = [f.result() for f in futures]

        first = results[0]
        assert all(r == first for r in results)
