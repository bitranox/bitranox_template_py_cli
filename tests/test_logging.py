"""Tests for the logging adapter initialization.

Verifies behavioral contracts of init_logging and _build_runtime_config
without mocking lib_log_rich internals. The only mock is a guard preventing
actual global initialization (same justification as SMTP: destructive
global side effects).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from lib_layered_config import Config

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters.logging.setup import (
    LoggingConfigModel,
    _build_runtime_config,  # pyright: ignore[reportPrivateUsage]
    init_logging,
)

_PATCH_BASE = "bitranox_template_py_cli.adapters.logging.setup.lib_log_rich"


# ======================== _build_runtime_config (quasi-pure) ========================


@pytest.mark.os_agnostic
def test_build_runtime_config_defaults_service_to_package_name() -> None:
    """Without configured service, runtime config uses the package name."""
    config = Config({}, {})

    result = _build_runtime_config(config)

    assert result.service == __init__conf__.name


@pytest.mark.os_agnostic
def test_build_runtime_config_defaults_environment_to_prod() -> None:
    """Without configured environment, runtime config defaults to 'prod'."""
    config = Config({}, {})

    result = _build_runtime_config(config)

    assert result.environment == "prod"


@pytest.mark.os_agnostic
def test_build_runtime_config_uses_configured_service() -> None:
    """Configured service name overrides the package default."""
    config = Config({"lib_log_rich": {"service": "my-service"}}, {})

    result = _build_runtime_config(config)

    assert result.service == "my-service"


@pytest.mark.os_agnostic
def test_build_runtime_config_uses_configured_environment() -> None:
    """Configured environment overrides the 'prod' default."""
    config = Config({"lib_log_rich": {"environment": "staging"}}, {})

    result = _build_runtime_config(config)

    assert result.environment == "staging"


@pytest.mark.os_agnostic
def test_build_runtime_config_handles_empty_lib_log_rich_section() -> None:
    """An empty lib_log_rich section produces valid defaults."""
    config = Config({"lib_log_rich": {}}, {})

    result = _build_runtime_config(config)

    assert result.service == __init__conf__.name
    assert result.environment == "prod"


# ======================== init_logging (behavioral) ========================


@pytest.mark.os_agnostic
def test_init_logging_does_not_raise_with_valid_config() -> None:
    """init_logging accepts a valid Config without raising."""
    config = Config({"lib_log_rich": {"environment": "test"}}, {})
    # Guard: prevent actual global initialization (destructive side effect,
    # same justification as SMTP mocking).
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=False),
        patch(f"{_PATCH_BASE}.config.enable_dotenv"),
        patch(f"{_PATCH_BASE}.runtime.init"),
        patch(f"{_PATCH_BASE}.runtime.attach_std_logging"),
    ):
        init_logging(config)


@pytest.mark.os_agnostic
def test_init_logging_is_idempotent_when_already_initialised() -> None:
    """Calling init_logging when already initialised is a no-op."""
    config = Config({}, {})
    # Simulate already-initialised state
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=True),
        patch(f"{_PATCH_BASE}.runtime.init") as mock_init,
    ):
        init_logging(config)

    mock_init.assert_not_called()


# ======================== LoggingConfigModel ========================


@pytest.mark.os_agnostic
def test_logging_config_model_allows_extra_fields() -> None:
    """Extra fields pass through for lib_log_rich RuntimeConfig."""
    parsed = LoggingConfigModel.model_validate({"service": "test", "environment": "dev", "custom_field": "value"})

    assert parsed.service == "test"
    assert parsed.environment == "dev"
    extra = parsed.model_dump(exclude={"service", "environment"}, exclude_none=True)
    assert extra == {"custom_field": "value"}


@pytest.mark.os_agnostic
def test_logging_config_model_defaults() -> None:
    """Empty input produces sensible defaults."""
    parsed = LoggingConfigModel.model_validate({})

    assert parsed.service is None
    assert parsed.environment == "prod"
