"""CLI stories: every invocation a single beat."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Sequence
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

import lib_cli_exit_tools

from bitranox_template_py_cli.adapters import cli as cli_mod
from bitranox_template_py_cli.adapters.cli.traceback import TracebackState
from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters.config import loader as config_mod
from bitranox_template_py_cli.adapters.config import deploy as config_deploy_mod


@dataclass(slots=True)
class CapturedRun:
    """Record of a single ``lib_cli_exit_tools.run_cli`` invocation.

    Attributes:
        command: Command object passed to ``run_cli``.
        argv: Argument vector forwarded to the command, when any.
        prog_name: Program name announced in the help output.
        signal_specs: Signal handlers registered by the runner.
        install_signals: ``True`` when the runner installed default signal handlers.
    """

    command: Any
    argv: Sequence[str] | None
    prog_name: str | None
    signal_specs: Any
    install_signals: bool


def _capture_run_cli(target: list[CapturedRun]) -> Callable[..., int]:
    """Return a stub that records lib_cli_exit_tools.run_cli invocations.

    Tests assert that the CLI delegates to lib_cli_exit_tools with the
    expected arguments; recording each call keeps those assertions readable.

    Args:
        target: Mutable list that will collect CapturedRun entries.

    Returns:
        Replacement callable for lib_cli_exit_tools.run_cli.
    """

    def _run(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        target.append(
            CapturedRun(
                command=command,
                argv=argv,
                prog_name=prog_name,
                signal_specs=signal_specs,
                install_signals=install_signals,
            )
        )
        return 42

    return _run


@pytest.mark.os_agnostic
def test_when_we_snapshot_traceback_the_initial_state_is_quiet(isolated_traceback_config: None) -> None:
    """Verify snapshot_traceback_state returns disabled state initially."""
    assert cli_mod.snapshot_traceback_state() == TracebackState(traceback_enabled=False, force_color=False)


@pytest.mark.os_agnostic
def test_when_we_enable_traceback_the_config_sings_true(isolated_traceback_config: None) -> None:
    """Verify apply_traceback_preferences enables traceback flags."""
    cli_mod.apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_when_we_restore_traceback_the_config_whispers_false(isolated_traceback_config: None) -> None:
    """Verify restore_traceback_state resets traceback flags to previous values."""
    previous = cli_mod.snapshot_traceback_state()
    cli_mod.apply_traceback_preferences(True)

    cli_mod.restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_info_runs_with_traceback_the_choice_is_shared(
    monkeypatch: pytest.MonkeyPatch,
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify traceback flag is active during info command then restored."""
    notes: list[tuple[bool, bool]] = []

    def record() -> None:
        notes.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(__init__conf__, "print_info", record)

    exit_code = cli_mod.main(["--traceback", "info"])

    assert exit_code == 0
    assert notes == [(True, True)]
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_main_is_called_it_delegates_to_run_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() delegates to lib_cli_exit_tools.run_cli with correct args."""
    ledger: list[CapturedRun] = []
    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", _capture_run_cli(ledger))

    result = cli_mod.main(["info"])

    assert result == 42
    assert ledger == [
        CapturedRun(
            command=cli_mod.cli,
            argv=["info"],
            prog_name=__init__conf__.shell_command,
            signal_specs=None,
            install_signals=True,
        )
    ]


@pytest.mark.os_agnostic
def test_when_cli_runs_without_arguments_help_is_printed(
    cli_runner: CliRunner,
) -> None:
    """Verify CLI with no arguments displays help text."""
    result = cli_runner.invoke(cli_mod.cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_when_main_receives_no_arguments_help_is_shown(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    isolated_traceback_config: None,
) -> None:
    """Verify main with no args shows help."""
    outputs: list[str] = []

    def fake_run_cli(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        args = [] if argv is None else list(argv)
        result: Result = cli_runner.invoke(command, args)
        if result.exception is not None:
            raise result.exception
        outputs.append(result.output)
        return result.exit_code

    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", fake_run_cli)

    exit_code = cli_mod.main([])

    assert exit_code == 0
    assert outputs and "Usage:" in outputs[0]


@pytest.mark.os_agnostic
def test_when_traceback_is_requested_without_command_help_is_shown(
    cli_runner: CliRunner,
) -> None:
    """Verify --traceback without command still shows help."""
    result = cli_runner.invoke(cli_mod.cli, ["--traceback"])

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_when_traceback_flag_is_passed_the_full_story_is_printed(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Verify --traceback displays full exception traceback on failure."""
    exit_code = cli_mod.main(["--traceback", "fail"])

    plain_err = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_hello_is_invoked_the_cli_smiles(cli_runner: CliRunner) -> None:
    """Verify hello command outputs Hello World greeting."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["hello"])

    assert result.exit_code == 0
    assert "Hello World" in result.output


@pytest.mark.os_agnostic
def test_when_fail_is_invoked_the_cli_raises(cli_runner: CliRunner) -> None:
    """Verify fail command raises RuntimeError."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["fail"])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)


@pytest.mark.os_agnostic
def test_when_info_is_invoked_the_metadata_is_displayed(cli_runner: CliRunner) -> None:
    """Verify info command displays project metadata."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert f"Info for {__init__conf__.name}:" in result.output
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_it_displays_configuration(cli_runner: CliRunner) -> None:
    """Verify config command displays configuration."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    # With default config (all commented), output may be empty or show only log messages


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_it_outputs_json(cli_runner: CliRunner) -> None:
    """Verify config --format json outputs JSON."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

    assert result.exit_code == 0
    # Use result.stdout to avoid async log messages from stderr
    assert "{" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_nonexistent_section_it_fails(cli_runner: CliRunner) -> None:
    """Verify config with nonexistent section returns error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"])

    assert result.exit_code != 0
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_mocked_data_it_displays_sections(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify config displays sections from mocked configuration."""
    inject_config(
        config_factory(
            {
                "test_section": {
                    "setting1": "value1",
                    "setting2": 42,
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "test_section" in result.output
    assert "setting1" in result.output
    assert "value1" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_section_it_shows_section(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify JSON format displays specific section content."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "test@example.com",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json", "--section", "email"])

    assert result.exit_code == 0
    assert "email" in result.output
    assert "smtp_hosts" in result.output
    assert "smtp.test.com:587" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_nonexistent_section_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify JSON format with nonexistent section returns error."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json", "--section", "nonexistent"])

    assert result.exit_code != 0
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_section_showing_complex_values(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify human format with section containing lists and dicts."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp1.test.com:587", "smtp2.test.com:587"],
                    "from_address": "test@example.com",
                    "metadata": {"key1": "value1", "key2": "value2"},
                    "timeout": 60.0,
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "email"])

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "smtp_hosts" in result.output
    assert "smtp1.test.com:587" in result.output
    assert "smtp2.test.com:587" in result.output
    assert "metadata" in result.output
    assert '"test@example.com"' in result.output
    assert "60.0" in result.output


@pytest.mark.os_agnostic
def test_when_config_shows_all_sections_with_complex_values(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify human format showing all sections with lists and dicts."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "tags": {"environment": "test", "version": "1.0"},
                },
                "logging": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                },
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "[logging]" in result.output
    assert "smtp_hosts" in result.output
    assert "handlers" in result.output
    assert "tags" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_target_it_fails(cli_runner: CliRunner) -> None:
    """Verify config-deploy without --target option fails."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_it_deploys_configuration(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy creates configuration files."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        return [deployed_path]

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert "Configuration deployed successfully" in result.output
    assert str(deployed_path) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_finds_no_files_to_create_it_informs_user(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy reports when no files are created."""
    from pathlib import Path

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        return []

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert "No files were created" in result.output
    assert "--force" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_encounters_permission_error_it_handles_gracefully(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy handles PermissionError gracefully."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app"])

    assert result.exit_code != 0
    assert "Permission denied" in result.stderr
    assert "sudo" in result.stderr.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_supports_multiple_targets(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy accepts multiple --target options."""
    from pathlib import Path
    from bitranox_template_py_cli.domain.enums import DeployTarget

    path1 = tmp_path / "config1.toml"
    path2 = tmp_path / "config2.toml"
    path1.touch()
    path2.touch()

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        target_values = [t.value if isinstance(t, DeployTarget) else t for t in targets]
        assert len(target_values) == 2
        assert "user" in target_values
        assert "host" in target_values
        return [path1, path2]

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--target", "host"])

    assert result.exit_code == 0
    assert str(path1) in result.output
    assert str(path2) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_with_profile_it_passes_profile(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy passes profile to deploy_configuration."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profile: list[str | None] = []

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        captured_profile.append(profile)
        return [deployed_path]

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--profile", "production"])

    assert result.exit_code == 0
    assert captured_profile == ["production"]
    assert "(profile: production)" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_profile_it_passes_profile_to_get_config(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    config_factory: Callable[[dict[str, Any]], Config],
    clear_config_cache: None,
) -> None:
    """Verify config command passes --profile to get_config."""
    captured_profiles: list[str | None] = []
    config = config_factory({"test_section": {"key": "value"}})

    def capturing(*, profile: str | None = None, **_kwargs: Any) -> Config:
        captured_profiles.append(profile)
        return config

    monkeypatch.setattr(config_mod, "get_config", capturing)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--profile", "staging"])

    assert result.exit_code == 0
    assert "staging" in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    config_factory: Callable[[dict[str, Any]], Config],
    clear_config_cache: None,
) -> None:
    """Verify config command passes None when no --profile specified."""
    captured_profiles: list[str | None] = []
    config = config_factory({"test_section": {"key": "value"}})

    def capturing(*, profile: str | None = None, **_kwargs: Any) -> Config:
        captured_profiles.append(profile)
        return config

    monkeypatch.setattr(config_mod, "get_config", capturing)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert None in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy passes None when no --profile specified."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profiles: list[str | None] = []

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        captured_profiles.append(profile)
        return [deployed_path]

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert captured_profiles == [None]
    assert "(profile:" not in result.output


# ======================== --set CLI Override Integration Tests ========================


@pytest.mark.os_agnostic
def test_when_set_override_is_passed_config_reflects_change(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify --set override is visible in config command output."""
    inject_config(
        config_factory(
            {
                "lib_log_rich": {
                    "console_level": "INFO",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "lib_log_rich.console_level=DEBUG", "config", "--section", "lib_log_rich"],
    )

    assert result.exit_code == 0
    assert "DEBUG" in result.output


@pytest.mark.os_agnostic
def test_when_multiple_set_overrides_are_passed_all_apply(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify multiple --set options all apply."""
    inject_config(
        config_factory(
            {
                "lib_log_rich": {
                    "console_level": "INFO",
                    "force_color": False,
                }
            }
        )
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "--set",
            "lib_log_rich.console_level=DEBUG",
            "--set",
            "lib_log_rich.force_color=true",
            "config",
            "--section",
            "lib_log_rich",
        ],
    )

    assert result.exit_code == 0
    assert "DEBUG" in result.output


@pytest.mark.os_agnostic
def test_when_set_override_has_nested_key_it_works(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify nested key override (e.g., SECTION.SUB.KEY=VALUE) works."""
    inject_config(
        config_factory(
            {
                "lib_log_rich": {
                    "payload_limits": {
                        "message_max_chars": 4096,
                    },
                }
            }
        )
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "lib_log_rich.payload_limits.message_max_chars=8192", "config", "--format", "json"],
    )

    assert result.exit_code == 0
    assert "8192" in result.stdout


@pytest.mark.os_agnostic
def test_when_set_override_is_invalid_it_shows_usage_error(
    cli_runner: CliRunner,
) -> None:
    """Verify invalid --set format shows usage error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "invalid_no_equals", "config"],
    )

    assert result.exit_code != 0
    assert "must contain '='" in result.output or "must contain '='" in (result.stderr or "")


@pytest.mark.os_agnostic
def test_when_set_override_has_no_dot_it_shows_usage_error(
    cli_runner: CliRunner,
) -> None:
    """Verify --set without dot in key shows usage error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "nodot=value", "config"],
    )

    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_when_set_override_is_empty_string_it_shows_error(
    cli_runner: CliRunner,
) -> None:
    """Verify --set with empty string shows error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "", "config"],
    )

    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_when_no_set_overrides_config_is_unchanged(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Verify no --set leaves config unchanged."""
    inject_config(
        config_factory(
            {
                "lib_log_rich": {
                    "console_level": "WARNING",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config", "--section", "lib_log_rich"],
    )

    assert result.exit_code == 0
    assert "WARNING" in result.output


@pytest.mark.os_agnostic
def test_when_an_unknown_command_is_used_a_helpful_error_appears(cli_runner: CliRunner) -> None:
    """Verify unknown command shows No such command error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"])

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_when_restore_is_disabled_the_traceback_choice_remains(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify restore_traceback=False keeps traceback flags enabled."""
    cli_mod.apply_traceback_preferences(False)

    cli_mod.main(["--traceback", "hello"], restore_traceback=False)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


# ======================== SmtpConfigOverrides Unit Tests ========================


@pytest.mark.os_agnostic
def test_when_smtp_overrides_have_no_values_it_returns_same_config() -> None:
    """When no overrides are set, apply_to returns the same config instance."""
    from bitranox_template_py_cli.adapters.cli.commands.email import SmtpConfigOverrides
    from bitranox_template_py_cli.adapters.email.sender import EmailConfig

    config = EmailConfig(smtp_hosts=["smtp.example.com:587"], from_address="a@b.com")
    overrides = SmtpConfigOverrides()

    result = overrides.apply_to(config)

    assert result is config


@pytest.mark.os_agnostic
def test_when_smtp_overrides_include_host_it_applies_override() -> None:
    """When smtp_hosts is set, apply_to replaces hosts and keeps other fields unchanged."""
    from bitranox_template_py_cli.adapters.cli.commands.email import SmtpConfigOverrides
    from bitranox_template_py_cli.adapters.email.sender import EmailConfig

    config = EmailConfig(
        smtp_hosts=["smtp.original.com:587"],
        from_address="sender@example.com",
        timeout=30.0,
    )
    overrides = SmtpConfigOverrides(smtp_hosts=("smtp.override.com:465",))

    result = overrides.apply_to(config)

    assert result.smtp_hosts == ["smtp.override.com:465"]
    assert result.from_address == "sender@example.com"
    assert result.timeout == 30.0


@pytest.mark.os_agnostic
def test_when_smtp_overrides_include_multiple_fields_it_applies_all() -> None:
    """When multiple overrides are set, apply_to replaces all specified fields."""
    from bitranox_template_py_cli.adapters.cli.commands.email import SmtpConfigOverrides
    from bitranox_template_py_cli.adapters.email.sender import EmailConfig

    config = EmailConfig(
        smtp_hosts=["smtp.original.com:587"],
        from_address="sender@example.com",
        use_starttls=True,
        timeout=30.0,
    )
    overrides = SmtpConfigOverrides(
        smtp_hosts=("smtp.new.com:465",),
        use_starttls=False,
        timeout=60.0,
    )

    result = overrides.apply_to(config)

    assert result.smtp_hosts == ["smtp.new.com:465"]
    assert result.use_starttls is False
    assert result.timeout == 60.0
    assert result.from_address == "sender@example.com"


# ======================== Email Command Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP hosts are not configured, send-email should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
        ],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP is configured, send-email should successfully send."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test body",
            ],
        )

        assert result.exit_code == 0
        assert "Email sent successfully" in result.output


@pytest.mark.os_agnostic
def test_when_send_email_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When multiple --to flags are provided, send-email should accept them."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "user1@test.com",
                "--to",
                "user2@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_includes_html_body_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When HTML body is provided, send-email should include it."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Plain text",
                "--body-html",
                "<h1>HTML</h1>",
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_has_attachments_it_sends(
    cli_runner: CliRunner,
    tmp_path: Any,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When attachments are provided, send-email should include them."""
    from unittest.mock import patch

    attachment = tmp_path / "test.txt"
    attachment.write_text("Test content")

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "See attachment",
                "--attachment",
                str(attachment),
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP connection fails, send-email should show SMTP_FAILURE (69) error."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect")

        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
            ],
        )

        assert result.exit_code == 69
        assert "Error" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP hosts are not configured, send-notification should exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP is configured, send-notification should successfully send."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-notification",
                "--to",
                "admin@test.com",
                "--subject",
                "Alert",
                "--message",
                "System notification",
            ],
        )

        assert result.exit_code == 0
        assert "Notification sent successfully" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When multiple --to flags are provided, send-notification should accept them."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP"):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-notification",
                "--to",
                "admin1@test.com",
                "--to",
                "admin2@test.com",
                "--subject",
                "Alert",
                "--message",
                "System notification",
            ],
        )

        assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_notification_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When SMTP connection fails, send-notification should show SMTP_FAILURE (69) error."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect")

        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-notification",
                "--to",
                "admin@test.com",
                "--subject",
                "Alert",
                "--message",
                "System notification",
            ],
        )

        assert result.exit_code == 69
        assert "Error" in result.output


# ======================== SMTP Config Override Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-host is provided, send-email should use the override instead of config value."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.config.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--smtp-host",
                "smtp.override.com:465",
            ],
        )

        assert result.exit_code == 0
        smtp_calls = mock_smtp.call_args_list
        # SMTP(host, ...) — host is always the first positional arg
        assert any(len(c.args) > 0 and "smtp.override.com" in c.args[0] for c in smtp_calls)


@pytest.mark.os_agnostic
def test_when_send_email_receives_timeout_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --timeout is provided, send-email should use the overridden timeout."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--timeout",
                "60",
            ],
        )

        assert result.exit_code == 0
        smtp_calls = mock_smtp.call_args_list
        # smtplib.SMTP accepts timeout as keyword or second positional arg
        assert any(c.kwargs.get("timeout") == 60.0 for c in smtp_calls) or any(len(c.args) > 1 and c.args[1] == 60.0 for c in smtp_calls)


@pytest.mark.os_agnostic
def test_when_send_email_receives_no_use_starttls_override_it_skips_starttls(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --no-use-starttls is provided, send-email should not call starttls."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--no-use-starttls",
            ],
        )

        assert result.exit_code == 0
        assert not mock_instance.starttls.called


@pytest.mark.os_agnostic
def test_when_send_email_receives_credential_overrides_it_uses_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-username and --smtp-password are provided, send-email should use them."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-email",
                "--to",
                "recipient@test.com",
                "--subject",
                "Test",
                "--body",
                "Hello",
                "--smtp-username",
                "myuser",
                "--smtp-password",
                "mypass",
            ],
        )

        assert result.exit_code == 0
        mock_instance.login.assert_called_once_with("myuser", "mypass")


@pytest.mark.os_agnostic
def test_when_send_notification_receives_from_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --from is provided, send-notification should use the override sender."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "default@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = mock_smtp.return_value.__enter__.return_value

        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-notification",
                "--to",
                "admin@test.com",
                "--subject",
                "Alert",
                "--message",
                "System notification",
                "--from",
                "override@test.com",
            ],
        )

        assert result.exit_code == 0
        mock_instance.sendmail.assert_called_once()
        call_args = mock_instance.sendmail.call_args
        assert call_args[0][0] == "override@test.com"


@pytest.mark.os_agnostic
def test_when_send_notification_receives_smtp_host_override_it_uses_it(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """When --smtp-host is provided, send-notification should use the override host."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.config.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch("smtplib.SMTP") as mock_smtp:
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            [
                "send-notification",
                "--to",
                "admin@test.com",
                "--subject",
                "Alert",
                "--message",
                "System notification",
                "--smtp-host",
                "smtp.override.com:465",
            ],
        )

        assert result.exit_code == 0
        smtp_calls = mock_smtp.call_args_list
        # SMTP(host, ...) — host is always the first positional arg
        assert any(len(c.args) > 0 and "smtp.override.com" in c.args[0] for c in smtp_calls)


# ======================== Profile Validation Tests ========================


@pytest.mark.os_agnostic
def test_when_profile_contains_path_traversal_it_rejects(clear_config_cache: None) -> None:
    """Profile names containing path traversal sequences must be rejected."""
    from bitranox_template_py_cli.adapters.config.loader import get_config

    with pytest.raises(ValueError, match="Invalid profile name"):
        get_config(profile="../etc")


@pytest.mark.os_agnostic
def test_when_profile_is_dot_dot_it_rejects(clear_config_cache: None) -> None:
    """A bare '..' profile must be rejected."""
    from bitranox_template_py_cli.adapters.config.loader import get_config

    with pytest.raises(ValueError, match="Invalid profile name"):
        get_config(profile="..")


@pytest.mark.os_agnostic
def test_when_profile_contains_slash_it_rejects(clear_config_cache: None) -> None:
    """Profile names with slashes must be rejected."""
    from bitranox_template_py_cli.adapters.config.loader import get_config

    with pytest.raises(ValueError, match="Invalid profile name"):
        get_config(profile="foo/bar")


@pytest.mark.os_agnostic
def test_when_profile_is_valid_alphanumeric_it_accepts(clear_config_cache: None) -> None:
    """Alphanumeric profiles with hyphens and underscores must be accepted."""
    from bitranox_template_py_cli.adapters.config.loader import get_config

    # Should not raise — the config may or may not exist, but validation passes
    config = get_config(profile="staging-v2")
    assert config is not None


@pytest.mark.os_agnostic
def test_when_deploy_receives_invalid_profile_it_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    """deploy_configuration must reject path traversal profiles."""
    from bitranox_template_py_cli.adapters.config.deploy import deploy_configuration
    from bitranox_template_py_cli.domain.enums import DeployTarget

    with pytest.raises(ValueError, match="Invalid profile name"):
        deploy_configuration(targets=[DeployTarget.USER], profile="../../x")


# ======================== Config Display Redaction Tests ========================


@pytest.mark.os_agnostic
def test_when_config_displays_human_format_it_redacts_password(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Human-readable output must redact sensitive keys like smtp_password."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_password": "super_secret_123",
                    "from_address": "test@example.com",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "super_secret_123" not in result.output
    assert "***REDACTED***" in result.output
    assert "from_address" in result.output
    assert "test@example.com" in result.output


@pytest.mark.os_agnostic
def test_when_config_displays_json_format_it_redacts_password(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """JSON output must redact sensitive keys like smtp_password."""
    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_password": "super_secret_123",
                    "from_address": "test@example.com",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

    assert result.exit_code == 0
    assert "super_secret_123" not in result.stdout
    assert "***REDACTED***" in result.stdout
    assert "from_address" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_displays_non_sensitive_values_it_shows_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Non-sensitive keys must show their real values, not be redacted."""
    inject_config(
        config_factory(
            {
                "logging": {
                    "level": "DEBUG",
                    "service": "my_app",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "DEBUG" in result.output
    assert "my_app" in result.output
    assert "***REDACTED***" not in result.output


@pytest.mark.os_agnostic
def test_when_config_displays_token_and_secret_keys_it_redacts_them(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Keys containing 'token', 'secret', or 'credential' must be redacted."""
    inject_config(
        config_factory(
            {
                "auth": {
                    "api_token": "tok_abc123",
                    "client_secret": "sec_xyz789",
                    "username": "admin",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "tok_abc123" not in result.output
    assert "sec_xyz789" not in result.output
    assert "admin" in result.output


@pytest.mark.os_agnostic
def test_when_logdemo_is_invoked_it_completes_successfully(
    cli_runner: CliRunner,
) -> None:
    """Verify logdemo command runs and exits with code 0."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["logdemo"])

    assert result.exit_code == 0
    assert "Log demo completed" in result.output


@pytest.mark.os_agnostic
def test_when_config_generate_examples_is_invoked_it_creates_files(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-generate-examples creates files in the target directory."""
    from pathlib import Path

    created_file = tmp_path / "example.toml"
    created_file.touch()

    def mock_generate_examples(destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None) -> list[Path]:
        return [created_file]

    monkeypatch.setattr("bitranox_template_py_cli.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Generated 1 example file(s)" in result.output
    assert str(created_file) in result.output


@pytest.mark.os_agnostic
def test_when_config_generate_examples_has_no_files_it_informs_user(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-generate-examples reports when all files already exist."""
    from pathlib import Path

    def mock_generate_examples(destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None) -> list[Path]:
        return []

    monkeypatch.setattr("bitranox_template_py_cli.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "No files generated" in result.output
    assert "--force" in result.output


@pytest.mark.os_agnostic
def test_when_config_generate_examples_missing_destination_it_fails(
    cli_runner: CliRunner,
) -> None:
    """Verify config-generate-examples without --destination fails."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-generate-examples"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_config_displays_password_in_list_of_dicts_it_redacts(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Sensitive keys inside dicts nested in lists must be redacted."""
    inject_config(
        config_factory(
            {
                "connections": {
                    "servers": [
                        {"host": "smtp.example.com", "password": "secret123"},
                        {"host": "backup.example.com", "password": "secret456"},
                    ],
                    "name": "production",
                }
            }
        )
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

    assert result.exit_code == 0
    assert "secret123" not in result.stdout
    assert "secret456" not in result.stdout
    assert "smtp.example.com" in result.stdout
    assert "REDACTED" in result.stdout


# ======================== Exit Code Integration Tests ========================


@pytest.mark.os_agnostic
def test_when_config_section_is_invalid_it_exits_with_code_22(cli_runner: CliRunner) -> None:
    """Config --section with nonexistent section must exit with INVALID_ARGUMENT (22)."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"])

    assert result.exit_code == 22
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_permission_error_it_exits_with_code_13(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config-deploy PermissionError must exit with PERMISSION_DENIED (13)."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app"])

    assert result.exit_code == 13
    assert "Permission denied" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_generic_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config-deploy generic Exception must exit with GENERAL_ERROR (1)."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise OSError("Disk full")

    monkeypatch.setattr(config_deploy_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 1
    assert "Disk full" in result.stderr


@pytest.mark.os_agnostic
def test_when_email_has_no_smtp_hosts_it_exits_with_code_78(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email with no SMTP hosts configured must exit with CONFIG_ERROR (78)."""
    inject_config(config_factory({"email": {}}))

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_email_smtp_fails_it_exits_with_code_69(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email RuntimeError (SMTP failure) must exit with SMTP_FAILURE (69)."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        side_effect=RuntimeError("SMTP connection refused"),
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 69
    assert "SMTP connection refused" in (result.output + (result.stderr or ""))


@pytest.mark.os_agnostic
def test_when_email_send_returns_false_it_exits_with_code_69(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email returning False must exit with SMTP_FAILURE (69)."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        return_value=False,
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 69
    assert "sending failed" in (result.output + (result.stderr or ""))


@pytest.mark.os_agnostic
def test_when_email_has_unexpected_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], None],
) -> None:
    """Send-email unexpected Exception must exit with GENERAL_ERROR (1)."""
    from unittest.mock import patch

    inject_config(
        config_factory(
            {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
        )
    )

    with patch(
        "bitranox_template_py_cli.adapters.cli.commands.email.send_email",
        side_effect=TypeError("unexpected type error"),
    ):
        result: Result = cli_runner.invoke(
            cli_mod.cli,
            ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        )

    assert result.exit_code == 1
    assert "unexpected type error" in (result.output + (result.stderr or ""))
