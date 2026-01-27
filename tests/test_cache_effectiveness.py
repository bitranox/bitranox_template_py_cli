"""Verify LRU cache effectiveness for configuration loading functions.

Ensures that ``get_config()`` and ``get_default_config_path()`` caches
are actually hit on repeated calls, confirming the caching design is
justified for avoiding redundant file I/O and TOML parsing.
"""

from __future__ import annotations

import pytest


@pytest.mark.os_agnostic
class TestGetDefaultConfigPathCache:
    """Verify get_default_config_path() caching behaviour."""

    def test_cache_hit_on_repeated_calls(self) -> None:
        """Repeated calls should serve from cache after the first miss."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        get_default_config_path.cache_clear()

        get_default_config_path()
        get_default_config_path()
        get_default_config_path()

        info = get_default_config_path.cache_info()
        assert info.hits >= 2
        assert info.misses == 1

    def test_returns_same_object(self) -> None:
        """Cached function should return the identical Path object."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        get_default_config_path.cache_clear()

        first = get_default_config_path()
        second = get_default_config_path()

        assert first is second


@pytest.mark.os_agnostic
class TestGetConfigCache:
    """Verify get_config() caching behaviour."""

    def test_cache_hit_on_same_args(self) -> None:
        """Calling get_config() twice with same args should hit the cache."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        get_config()
        get_config()

        info = get_config.cache_info()
        assert info.hits >= 1
        assert info.misses == 1

    def test_cache_miss_on_different_profile(self) -> None:
        """Different profile arguments should produce separate cache entries."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        get_config()
        get_config(profile="test")

        info = get_config.cache_info()
        assert info.misses == 2

    def test_cache_clear_forces_reload(self) -> None:
        """Clearing the cache should force a fresh load on the next call."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()
        get_config()
        info_before = get_config.cache_info()
        assert info_before.misses == 1

        get_config.cache_clear()
        get_config()
        info_after = get_config.cache_info()
        assert info_after.misses == 1
        assert info_after.hits == 0

    def test_cached_config_returns_same_object(self) -> None:
        """Same arguments should return the identical Config object."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        first = get_config()
        second = get_config()

        assert first is second
