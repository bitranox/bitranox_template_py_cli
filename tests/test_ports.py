"""Port conformance tests — verify adapter functions satisfy their protocols.

Each test assigns the concrete adapter function to a variable typed as the
corresponding Protocol.  This serves two purposes:

1. **Runtime**: confirms the adapter is callable.
2. **Static analysis**: pyright verifies signature compatibility at type-check
   time (the assignment would fail if signatures diverge).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitranox_template_py_cli.adapters.config.loader import get_config, get_default_config_path
from bitranox_template_py_cli.adapters.config.deploy import deploy_configuration
from bitranox_template_py_cli.adapters.config.display import display_config
from bitranox_template_py_cli.adapters.email.sender import load_email_config_from_dict, send_email, send_notification
from bitranox_template_py_cli.adapters.logging.setup import init_logging

if TYPE_CHECKING:
    from bitranox_template_py_cli.application.ports import (
        DeployConfiguration,
        DisplayConfig,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )


@pytest.mark.os_agnostic
def test_get_config_satisfies_port() -> None:
    port: GetConfig = get_config
    assert callable(port)


@pytest.mark.os_agnostic
def test_get_default_config_path_satisfies_port() -> None:
    port: GetDefaultConfigPath = get_default_config_path
    assert callable(port)


@pytest.mark.os_agnostic
def test_deploy_configuration_satisfies_port() -> None:
    port: DeployConfiguration = deploy_configuration
    assert callable(port)


@pytest.mark.os_agnostic
def test_display_config_satisfies_port() -> None:
    port: DisplayConfig = display_config
    assert callable(port)


@pytest.mark.os_agnostic
def test_send_email_satisfies_port() -> None:
    port: SendEmail = send_email
    assert callable(port)


@pytest.mark.os_agnostic
def test_send_notification_satisfies_port() -> None:
    port: SendNotification = send_notification
    assert callable(port)


@pytest.mark.os_agnostic
def test_load_email_config_from_dict_satisfies_port() -> None:
    port: LoadEmailConfigFromDict = load_email_config_from_dict
    assert callable(port)


@pytest.mark.os_agnostic
def test_init_logging_satisfies_port() -> None:
    port: InitLogging = init_logging
    assert callable(port)
