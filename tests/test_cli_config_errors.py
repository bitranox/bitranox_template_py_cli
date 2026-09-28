"""A configuration that cannot be loaded: who reports it, and who still runs.

The root group loads the configuration before any subcommand's options are parsed, so it
cannot report a failure in the form the subcommand would, and it must not block a command
that never reads the configuration: ``config-deploy`` is how a broken file gets replaced,
and ``info`` or ``--help`` have to work meanwhile. The root records the failure; a command
that reads the configuration refuses with exit 78 and one stderr line naming it. Every way
loading can fail (a broken file, an invalid profile, an unreadable file) takes that path.

``config-deploy`` reads one thing from the configuration: the permission settings. It runs
without them only when they cannot matter - ``--no-permissions``, or both ``--dir-mode`` and
``--file-mode`` - and otherwise refuses with exit 78 and a hint naming those options, rather
than deploying with library defaults that may be wider than what an administrator configured.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Any

import pytest
from lib_layered_config import Config, ConfigError

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters import cli as cli_mod
from bitranox_template_py_cli.composition import AppServices, build_testing

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from click.testing import CliRunner

BROKEN_TOML = "Invalid TOML in /etc/xdg/app/config.toml: expected a right bracket"
BAD_PROFILE = "profile contains invalid characters: ../x"
UNREADABLE = PermissionError(13, "Permission denied", "/etc/xdg/app/config.toml")

#: Each command with the arguments that get it past click's own option parsing. A command
#: added without an entry fails ``test_every_command_is_classified``, so nobody can add one
#: that silently reads an empty configuration after a load failure.
NEEDS_CONFIG: dict[str, list[str]] = {
    "config": ["config"],
    "send-email": ["send-email", "--to", "a@example.com", "--subject", "s", "--body", "b"],
    "send-notification": ["send-notification", "--to", "a@example.com", "--subject", "s", "--message", "m"],
}
RUNS_WITHOUT_CONFIG: dict[str, list[str]] = {
    "config-deploy": ["config-deploy", "--target", "user", "--no-permissions"],
    "hello": ["hello"],
    "info": ["info"],
}
#: Covered by their own tests below: one writes into a directory, one fails on purpose, one
#: replaces the logging runtime.
OTHER = ("config-generate-examples", "fail", "logdemo")


def _failing_config(error: Exception) -> Callable[[], AppServices]:
    def get_config(**_kwargs: Any) -> Config:
        raise error

    return lambda: dataclasses.replace(build_testing(), get_config=get_config)


@pytest.mark.os_agnostic
def test_every_command_is_classified() -> None:
    assert set(NEEDS_CONFIG) | set(RUNS_WITHOUT_CONFIG) | set(OTHER) == set(cli_mod.cli.commands)


@pytest.mark.os_agnostic
@pytest.mark.parametrize("args", NEEDS_CONFIG.values(), ids=NEEDS_CONFIG.keys())
@pytest.mark.parametrize(
    ("error", "message"),
    [(ConfigError(BROKEN_TOML), BROKEN_TOML), (ValueError(BAD_PROFILE), BAD_PROFILE), (UNREADABLE, str(UNREADABLE))],
    ids=["broken-file", "invalid-profile", "unreadable-file"],
)
def test_a_command_that_reads_the_config_refuses_with_exit_78(
    cli_runner: CliRunner, args: list[str], error: Exception, message: str
) -> None:
    result = cli_runner.invoke(cli_mod.cli, args, obj=_failing_config(error))

    assert result.exit_code == 78, result.output
    assert f"Error: {message}" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.os_agnostic
@pytest.mark.parametrize("args", RUNS_WITHOUT_CONFIG.values(), ids=RUNS_WITHOUT_CONFIG.keys())
def test_a_command_that_does_not_read_the_config_still_runs(cli_runner: CliRunner, args: list[str]) -> None:
    result = cli_runner.invoke(cli_mod.cli, args, obj=_failing_config(ConfigError(BROKEN_TOML)))

    assert result.exit_code == 0, result.output


def _recording_failing_config(error: Exception) -> tuple[list[dict[str, Any]], Callable[[], AppServices]]:
    """A failing configuration whose deploy records its keyword arguments and writes nothing."""
    calls: list[dict[str, Any]] = []

    def get_config(**_kwargs: Any) -> Config:
        raise error

    def deploy(**kwargs: Any) -> list[Path]:
        calls.append(kwargs)
        return []

    return calls, lambda: dataclasses.replace(build_testing(), get_config=get_config, deploy_configuration=deploy)


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (["--no-permissions"], (False, 0o700, 0o600)),
        (["--dir-mode", "750", "--file-mode", "640"], (True, 0o750, 0o640)),
    ],
    ids=["no-permissions", "both-modes"],
)
def test_config_deploy_runs_without_the_config_when_its_permissions_cannot_matter(
    cli_runner: CliRunner, options: list[str], expected: tuple[bool, int, int]
) -> None:
    calls, factory = _recording_failing_config(ConfigError(BROKEN_TOML))

    result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", *options], obj=factory)

    assert result.exit_code == 0, result.output
    assert BROKEN_TOML in result.stderr
    assert [(call["set_permissions"], call["dir_mode"], call["file_mode"]) for call in calls] == [expected]


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "options",
    [[], ["--permissions"], ["--dir-mode", "750"], ["--file-mode", "640"]],
    ids=["no-options", "permissions-on", "dir-mode-only", "file-mode-only"],
)
def test_config_deploy_refuses_when_the_unloaded_config_decides_a_mode(
    cli_runner: CliRunner, options: list[str]
) -> None:
    """No silent fall-back to the library's layer defaults, which can be wider than configured."""
    calls, factory = _recording_failing_config(ConfigError(BROKEN_TOML))

    result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", *options], obj=factory)

    error_lines = [line for line in result.stderr.splitlines() if line.strip()]
    assert result.exit_code == 78, result.output
    assert len(error_lines) == 1, result.stderr
    assert BROKEN_TOML in error_lines[0]
    assert all(flag in error_lines[0] for flag in ("--no-permissions", "--dir-mode", "--file-mode"))
    assert calls == []


@pytest.mark.os_agnostic
def test_config_generate_examples_still_runs(cli_runner: CliRunner, tmp_path: Path) -> None:
    args = ["config-generate-examples", "--destination", str(tmp_path)]
    result = cli_runner.invoke(cli_mod.cli, args, obj=_failing_config(ConfigError(BROKEN_TOML)))

    assert result.exit_code == 0, result.output


@pytest.mark.os_agnostic
def test_the_fail_command_is_not_refused_for_the_config(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli_mod.cli, ["fail"], obj=_failing_config(ConfigError(BROKEN_TOML)))

    assert isinstance(result.exception, RuntimeError)
    assert BROKEN_TOML not in result.stderr


@pytest.mark.os_agnostic
@pytest.mark.parametrize("args", [["config-deploy", "--help"], []], ids=["subcommand-help", "bare-group"])
def test_help_works_while_the_config_is_broken(cli_runner: CliRunner, args: list[str]) -> None:
    result = cli_runner.invoke(cli_mod.cli, args, obj=_failing_config(ConfigError(BROKEN_TOML)))

    assert result.exit_code == 0, result.output
    assert "Usage" in result.stdout


@pytest.mark.os_agnostic
def test_a_malformed_set_is_still_a_usage_error(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli_mod.cli, ["--set", "no-equals-sign", "info"], obj=build_testing)

    assert result.exit_code == 2, result.output


@pytest.mark.os_agnostic
def test_a_profile_given_to_config_itself_fails_like_one_given_to_the_root(cli_runner: CliRunner) -> None:
    def get_config(*, profile: str | None = None, **_kwargs: Any) -> Config:
        if profile == "prod":
            raise ValueError(BAD_PROFILE)
        return Config({}, {})

    services = dataclasses.replace(build_testing(), get_config=get_config)
    result = cli_runner.invoke(cli_mod.cli, ["config", "--profile", "prod"], obj=lambda: services)

    assert result.exit_code == 78, result.output
    assert f"Error: {BAD_PROFILE}" in result.stderr


@pytest.mark.os_agnostic
def test_a_profile_given_to_config_itself_keeps_the_root_env_file(cli_runner: CliRunner, tmp_path: Path) -> None:
    env_file = tmp_path / "app.env"
    env_file.write_text("", encoding="utf-8")
    calls: list[tuple[str | None, str | None]] = []

    def get_config(*, profile: str | None = None, dotenv_path: str | None = None, **_kwargs: Any) -> Config:
        calls.append((profile, dotenv_path))
        return Config({}, {})

    services = dataclasses.replace(build_testing(), get_config=get_config)
    args = ["--env-file", str(env_file), "config", "--profile", "prod"]
    result = cli_runner.invoke(cli_mod.cli, args, obj=lambda: services)

    assert result.exit_code == 0, result.output
    assert calls == [(None, str(env_file)), ("prod", str(env_file))]


@pytest.fixture
def broken_user_config_env(tmp_path: Path) -> dict[str, str]:
    """An environment whose user layer holds a config.toml that does not parse."""
    config_dir = tmp_path / __init__conf__.LAYEREDCONF_SLUG
    config_dir.mkdir()
    (config_dir / "config.toml").write_text("broken = [\n", encoding="utf-8")
    return {**os.environ, "XDG_CONFIG_HOME": str(tmp_path)}


_LINUX_ONLY = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="XDG_CONFIG_HOME locates the user layer on Linux"
)


@_LINUX_ONLY
def test_a_real_broken_user_config_does_not_stop_info(broken_user_config_env: dict[str, str]) -> None:
    """End to end through the real loader: info does not read the configuration."""
    completed = subprocess.run(
        [sys.executable, "-m", "bitranox_template_py_cli", "info"],
        capture_output=True,
        check=False,
        env=broken_user_config_env,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert completed.stdout


@_LINUX_ONLY
def test_a_real_broken_user_config_refuses_config_with_78(broken_user_config_env: dict[str, str]) -> None:
    """End to end through the real loader: config reads it, so it refuses and names the file."""
    completed = subprocess.run(
        [sys.executable, "-m", "bitranox_template_py_cli", "config"],
        capture_output=True,
        check=False,
        env=broken_user_config_env,
    )

    stderr = completed.stderr.decode("utf-8", "replace")
    assert completed.returncode == 78, stderr
    assert "Invalid TOML" in stderr
    assert "Traceback" not in stderr


@_LINUX_ONLY
def test_a_real_invalid_permission_section_is_replaced_by_a_forced_deploy_without_permissions(tmp_path: Path) -> None:
    """End to end: the command that replaces a bad file is not blocked by the value it replaces."""
    config_dir = tmp_path / __init__conf__.LAYEREDCONF_SLUG
    config_dir.mkdir()
    bad = '[lib_layered_config.default_permissions]\nuser_directory = "0o777"\n'
    (config_dir / "config.toml").write_text(bad, encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bitranox_template_py_cli",
            "config-deploy",
            "--target",
            "user",
            "--force",
            "--no-permissions",
            "--dir-mode",
            "700",
            "--file-mode",
            "600",
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "XDG_CONFIG_HOME": str(tmp_path)},
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert (config_dir / "config.toml").read_text(encoding="utf-8") != bad
