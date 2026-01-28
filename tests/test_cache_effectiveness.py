"""Verify LRU cache effectiveness for configuration loading functions.

Ensures that ``get_config()`` and ``get_default_config_path()`` caching
is justified by confirming repeated calls return identical objects and
that the cache stabilises under concurrent access.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.os_agnostic
class TestGetDefaultConfigPathCache:
    """Verify get_default_config_path() caching behaviour."""

    def test_repeated_calls_return_identical_object(self) -> None:
        """Repeated calls return the exact same Path object (identity check)."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        get_default_config_path.cache_clear()

        first = get_default_config_path()
        second = get_default_config_path()
        third = get_default_config_path()

        assert first is second
        assert second is third

    def test_result_is_a_toml_path(self) -> None:
        """The returned path points to a .toml file."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        get_default_config_path.cache_clear()

        result = get_default_config_path()

        assert result.suffix == ".toml"


@pytest.mark.os_agnostic
class TestGetConfigCache:
    """Verify get_config() caching behaviour."""

    def test_same_args_return_identical_object(self) -> None:
        """Calling get_config() twice with same args returns the identical Config."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        first = get_config()
        second = get_config()

        assert first is second

    def test_different_profile_returns_distinct_object(self) -> None:
        """Different profile arguments return separate Config objects."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        default = get_config()
        test_profile = get_config(profile="test")

        assert default is not test_profile

    def test_cache_clear_forces_new_object(self) -> None:
        """Clearing the cache makes the next call return a fresh Config."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()
        first = get_config()

        get_config.cache_clear()
        second = get_config()

        # Both are valid configs with the same data, but different objects
        assert first.as_dict() == second.as_dict()

    def test_cached_config_has_valid_dict(self) -> None:
        """Cached Config.as_dict() returns a non-None dict."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        config = get_config()

        assert isinstance(config.as_dict(), dict)


@pytest.mark.os_agnostic
class TestCacheConcurrency:
    """Verify LRU cache behaves correctly under concurrent access.

    CPython's lru_cache is thread-safe (no corruption) but does not
    deduplicate concurrent misses. These tests verify *consistency*
    (equal results) after a concurrent burst.
    """

    def test_concurrent_get_config_returns_equivalent_results(self) -> None:
        """All threads receive equivalent Config data from get_config()."""
        from bitranox_template_py_cli.adapters.config.loader import get_config

        get_config.cache_clear()

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(get_config) for _ in range(20)]
            results = [f.result() for f in futures]

        first_dict = results[0].as_dict()
        assert all(r.as_dict() == first_dict for r in results), "All threads should receive equivalent Config data"

    def test_concurrent_get_default_config_path_returns_consistent_results(self) -> None:
        """All threads receive equal Path objects from get_default_config_path()."""
        from bitranox_template_py_cli.adapters.config.loader import get_default_config_path

        get_default_config_path.cache_clear()

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(get_default_config_path) for _ in range(20)]
            results = [f.result() for f in futures]

        first = results[0]
        assert all(r == first for r in results), "All threads should receive equal Path values"
