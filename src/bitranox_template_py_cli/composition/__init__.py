"""Composition root - wires adapters to application ports.

This module serves as the dependency injection container, assembling the
concrete adapter implementations and making them available for use by the
application layer and entry points.

Contents:
    * Configuration services from :mod:`..adapters.config`
    * Email services from :mod:`..adapters.email`
    * Logging services from :mod:`..adapters.logging`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Configuration services
from ..adapters.config.loader import get_config, get_default_config_path
from ..adapters.config.deploy import deploy_configuration
from ..adapters.config.display import display_config

# Email services
from ..adapters.email.sender import (
    EmailConfig,
    send_email,
    send_notification,
    load_email_config_from_dict,
)

# Logging services
from ..adapters.logging.setup import init_logging

# Static conformance assertions — pyright verifies that each adapter function
# structurally satisfies its corresponding Protocol at type-check time.
if TYPE_CHECKING:
    from ..application.ports import (
        DeployConfiguration,
        DisplayConfig,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )

    _assert_get_config: GetConfig = get_config
    _assert_get_default_config_path: GetDefaultConfigPath = get_default_config_path
    _assert_deploy_configuration: DeployConfiguration = deploy_configuration
    _assert_display_config: DisplayConfig = display_config
    _assert_send_email: SendEmail = send_email
    _assert_send_notification: SendNotification = send_notification
    _assert_load_email_config_from_dict: LoadEmailConfigFromDict = load_email_config_from_dict
    _assert_init_logging: InitLogging = init_logging

__all__ = [
    # Configuration
    "get_config",
    "get_default_config_path",
    "deploy_configuration",
    "display_config",
    # Email
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
    # Logging
    "init_logging",
]
