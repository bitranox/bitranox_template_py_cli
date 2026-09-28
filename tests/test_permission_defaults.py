"""The configured permission defaults are what ``config-deploy`` applies.

``[lib_layered_config.default_permissions]`` documents a directory and a file mode per
layer. They are read through one pydantic model, so a value the model refuses (a malformed
or out-of-range mode, string or integer alike, an unsafe mode, a non-boolean ``enabled``, a
section that is not a table, an unknown key) ends the command with exit 78 and one line
naming the key, before anything is deployed, instead of silently falling back to a default.
"""

from __future__ import annotations

import dataclasses
import os
import stat
import subprocess
import sys
from typing import TYPE_CHECKING, Any

import pytest
from lib_layered_config import Config

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters import cli as cli_mod
from bitranox_template_py_cli.adapters.config.permissions import get_modes_for_target
from bitranox_template_py_cli.composition import AppServices, build_testing
from bitranox_template_py_cli.domain.enums import DeployTarget

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from click.testing import CliRunner

_SECTION = "lib_layered_config.default_permissions"


@pytest.fixture
def recorded_deploys() -> Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]]:
    """A testing-composition factory over a given configuration whose deploy records its arguments.

    Built on ``build_testing`` so its logging runtime is the quiet one: the production
    runtime's queued INFO lines would race into the stderr these tests count lines of.
    """

    def _make(config_data: dict[str, Any]) -> tuple[list[dict[str, Any]], Callable[[], AppServices]]:
        calls: list[dict[str, Any]] = []
        config = Config(config_data, {})

        def get_config(**_kwargs: Any) -> Config:
            return config

        def deploy(**kwargs: Any) -> list[Path]:
            calls.append(kwargs)
            return []

        def factory() -> AppServices:
            return dataclasses.replace(build_testing(), get_config=get_config, deploy_configuration=deploy)

        return calls, factory

    return _make


def _modes(calls: list[dict[str, Any]]) -> list[tuple[str, int | None, int | None]]:
    return [(call["targets"][0].value, call["dir_mode"], call["file_mode"]) for call in calls]


@pytest.mark.os_agnostic
def test_every_target_gets_its_own_configured_modes(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
) -> None:
    calls, factory = recorded_deploys({})

    result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app", "--target", "user"], obj=factory)

    assert result.exit_code == 0, result.output
    assert _modes(calls) == [("app", 0o755, 0o644), ("user", 0o700, 0o600)]
    assert all(len(call["targets"]) == 1 for call in calls)


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "setting",
    [f"{_SECTION}.user_directory=488", f'{_SECTION}.user_directory="0o750"', f'{_SECTION}.user_directory="750"'],
    ids=["decimal-int", "0o-string", "bare-string"],
)
def test_a_configured_mode_reaches_the_deploy(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
    setting: str,
) -> None:
    calls, factory = recorded_deploys({})

    result = cli_runner.invoke(cli_mod.cli, ["--set", setting, "config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0, result.output
    assert _modes(calls) == [("user", 0o750, 0o600)]


@pytest.mark.os_agnostic
def test_a_cli_mode_beats_the_configured_one(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
) -> None:
    calls, factory = recorded_deploys({"lib_layered_config": {"default_permissions": {"user_directory": "0o750"}}})

    result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--dir-mode", "700"], obj=factory)

    assert result.exit_code == 0, result.output
    assert _modes(calls) == [("user", 0o700, 0o600)]


@pytest.mark.os_agnostic
def test_enabled_false_turns_permission_setting_off(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
) -> None:
    calls, factory = recorded_deploys({"lib_layered_config": {"default_permissions": {"enabled": False}}})

    result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0, result.output
    assert [call["set_permissions"] for call in calls] == [False]


#: Each ``--set`` value, and the text the one-line refusal must contain.
_REFUSED = [
    (f'{_SECTION}.user_directory="10000"', "user_directory: Invalid octal mode '10000': must be between"),
    (f'{_SECTION}.user_directory="-1"', "user_directory: Invalid octal mode '-1': not a plain octal literal"),
    (f'{_SECTION}.user_directory="7_5_0"', "user_directory: Invalid octal mode '7_5_0': not a plain octal literal"),
    (f'{_SECTION}.user_directory="rwx"', "user_directory: Invalid octal mode 'rwx': not a plain octal literal"),
    (f"{_SECTION}.user_directory=-1", "user_directory: Invalid mode -1: must be between"),
    (f"{_SECTION}.user_directory=10000", "user_directory: Invalid mode 10000: must be between"),
    (f"{_SECTION}.user_directory=1.5", "user_directory: expected an octal string or an integer, got float"),
    (f"{_SECTION}.user_directory=true", "user_directory: expected an octal string or an integer, got bool"),
    (f"{_SECTION}.user_directory=511", "user_directory: unsafe mode 0o777: world-write"),
    (f'{_SECTION}.user_file="0o4600"', "user_file: unsafe mode 0o4600: the setuid bit"),
    (f'{_SECTION}.app_file="0o400"', "app_file: unsafe mode 0o400: no owner rw"),
    (f'{_SECTION}.enabled="maybe"', "default_permissions.enabled: Input should be a valid boolean"),
    (f"{_SECTION}=5", "default_permissions: Input should be a valid dictionary"),
    (f'{_SECTION}.user_dir="0o750"', "default_permissions.user_dir: Extra inputs are not permitted"),
]


@pytest.mark.os_agnostic
@pytest.mark.parametrize(("setting", "named"), _REFUSED, ids=[setting for setting, _ in _REFUSED])
def test_an_invalid_permission_setting_is_a_one_line_config_error(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
    setting: str,
    named: str,
) -> None:
    calls, factory = recorded_deploys({})

    result = cli_runner.invoke(cli_mod.cli, ["--set", setting, "config-deploy", "--target", "user"], obj=factory)

    error_lines = [line for line in result.stderr.splitlines() if line.strip()]
    assert result.exit_code == 78, result.output
    assert len(error_lines) == 1, result.stderr
    assert error_lines[0].startswith("Error: Invalid configuration:")
    assert named in error_lines[0]
    assert calls == []


@pytest.mark.os_agnostic
def test_a_non_boolean_enabled_is_not_reported_as_a_mode(
    cli_runner: CliRunner,
    recorded_deploys: Callable[[dict[str, Any]], tuple[list[dict[str, Any]], Callable[[], AppServices]]],
) -> None:
    _calls, factory = recorded_deploys({})

    result = cli_runner.invoke(
        cli_mod.cli, ["--set", f'{_SECTION}.enabled="maybe"', "config-deploy", "--target", "user"], obj=factory
    )

    assert "mode" not in result.stderr.lower()
    assert "errors.pydantic.dev" not in result.stderr


@pytest.mark.os_agnostic
def test_modes_for_each_target_follow_the_layer_defaults(config_factory: Callable[[dict[str, Any]], Any]) -> None:
    config = config_factory({})

    assert get_modes_for_target(DeployTarget.HOST, config) == (0o755, 0o644)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="XDG_CONFIG_HOME locates the user layer on Linux")
def test_a_real_deploy_applies_the_configured_user_modes(tmp_path: Path) -> None:
    """End to end: the setting from the bug report now changes the mode on disk."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bitranox_template_py_cli",
            "--set",
            "lib_layered_config.default_permissions.user_directory=488",
            "--set",
            'lib_layered_config.default_permissions.user_file="0o640"',
            "config-deploy",
            "--target",
            "user",
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "XDG_CONFIG_HOME": str(tmp_path)},
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    deployed = tmp_path / __init__conf__.LAYEREDCONF_SLUG
    assert stat.S_IMODE(deployed.stat().st_mode) == 0o750
    assert stat.S_IMODE((deployed / "config.toml").stat().st_mode) == 0o640
