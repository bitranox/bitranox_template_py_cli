"""In-memory adapter implementations for testing.

Provides lightweight implementations of all application ports that operate
entirely in memory -- no filesystem, no SMTP, no logging framework.

Contents:
    * :mod:`.config` - In-memory configuration adapters
    * :mod:`.email` - In-memory email adapters
    * :mod:`.logging` - In-memory logging adapter
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import (
    deploy_configuration_in_memory,
    display_config_in_memory,
    get_config_in_memory,
    get_default_config_path_in_memory,
)
from .email import (
    EmailSpy,
    get_email_spy,
    load_email_config_from_dict_in_memory,
    send_email_in_memory,
    send_notification_in_memory,
)
from .logging import init_logging_in_memory

# Static conformance assertions
if TYPE_CHECKING:
    from bitranox_template_py_cli.application.ports import (
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )

    _assert_get_config: GetConfig = get_config_in_memory
    _assert_get_default_config_path: GetDefaultConfigPath = get_default_config_path_in_memory
    _assert_send_email: SendEmail = send_email_in_memory
    _assert_send_notification: SendNotification = send_notification_in_memory
    _assert_load_email_config: LoadEmailConfigFromDict = load_email_config_from_dict_in_memory
    _assert_init_logging: InitLogging = init_logging_in_memory

__all__ = [
    "EmailSpy",
    "deploy_configuration_in_memory",
    "display_config_in_memory",
    "get_config_in_memory",
    "get_default_config_path_in_memory",
    "get_email_spy",
    "init_logging_in_memory",
    "load_email_config_from_dict_in_memory",
    "send_email_in_memory",
    "send_notification_in_memory",
]
