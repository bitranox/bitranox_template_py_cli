"""Tests for the logging adapter initialization."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from lib_layered_config import Config

from bitranox_template_py_cli.adapters.logging.setup import (
    LoggingConfigModel,
    init_logging,
)

_PATCH_BASE = "bitranox_template_py_cli.adapters.logging.setup.lib_log_rich"


@pytest.mark.os_agnostic
def test_init_logging_calls_runtime_init_when_not_initialised() -> None:
    """Verify init_logging initializes lib_log_rich when not yet set up."""
    config = Config({"lib_log_rich": {"environment": "test"}}, {})
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=False),
        patch(f"{_PATCH_BASE}.config.enable_dotenv") as mock_dotenv,
        patch(f"{_PATCH_BASE}.runtime.init") as mock_init,
        patch(f"{_PATCH_BASE}.runtime.attach_std_logging") as mock_attach,
    ):
        init_logging(config)

    mock_dotenv.assert_called_once()
    mock_init.assert_called_once()
    mock_attach.assert_called_once()


@pytest.mark.os_agnostic
def test_init_logging_skips_when_already_initialised() -> None:
    """Verify init_logging is a no-op when lib_log_rich is already set up."""
    config = Config({}, {})
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=True),
        patch(f"{_PATCH_BASE}.runtime.init") as mock_init,
    ):
        init_logging(config)

    mock_init.assert_not_called()


@pytest.mark.os_agnostic
def test_init_logging_uses_package_name_when_service_not_configured() -> None:
    """Verify init_logging falls back to package name when no service configured."""
    from bitranox_template_py_cli import __init__conf__

    config = Config({}, {})
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=False),
        patch(f"{_PATCH_BASE}.config.enable_dotenv"),
        patch(f"{_PATCH_BASE}.runtime.init") as mock_init,
        patch(f"{_PATCH_BASE}.runtime.attach_std_logging"),
    ):
        init_logging(config)

    runtime_config = mock_init.call_args[0][0]
    assert runtime_config.service == __init__conf__.name
    assert runtime_config.environment == "prod"


@pytest.mark.os_agnostic
def test_init_logging_uses_configured_service_and_environment() -> None:
    """Verify init_logging reads service and environment from config."""
    config = Config({"lib_log_rich": {"service": "my-service", "environment": "staging"}}, {})
    with (
        patch(f"{_PATCH_BASE}.runtime.is_initialised", return_value=False),
        patch(f"{_PATCH_BASE}.config.enable_dotenv"),
        patch(f"{_PATCH_BASE}.runtime.init") as mock_init,
        patch(f"{_PATCH_BASE}.runtime.attach_std_logging"),
    ):
        init_logging(config)

    runtime_config = mock_init.call_args[0][0]
    assert runtime_config.service == "my-service"
    assert runtime_config.environment == "staging"


@pytest.mark.os_agnostic
def test_logging_config_model_allows_extra_fields() -> None:
    """Verify LoggingConfigModel passes through extra fields."""
    parsed = LoggingConfigModel.model_validate({"service": "test", "environment": "dev", "custom_field": "value"})

    assert parsed.service == "test"
    assert parsed.environment == "dev"
    extra = parsed.model_dump(exclude={"service", "environment"}, exclude_none=True)
    assert extra == {"custom_field": "value"}


@pytest.mark.os_agnostic
def test_logging_config_model_defaults() -> None:
    """Verify LoggingConfigModel defaults when no config provided."""
    parsed = LoggingConfigModel.model_validate({})

    assert parsed.service is None
    assert parsed.environment == "prod"
