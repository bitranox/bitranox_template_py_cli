"""Unit tests for deploy_configuration adapter logic.

Verify that deploy_configuration correctly converts enum targets to strings,
filters deploy results by action (CREATED/OVERWRITTEN), handles dot_d_results,
and validates profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from bitranox_template_py_cli.adapters.config import deploy as deploy_mod
from bitranox_template_py_cli.domain.enums import DeployTarget


@dataclass
class FakeDotDResult:
    """Simulate a dot_d deploy result from lib_layered_config."""

    action: object
    destination: Path


@dataclass
class FakeDeployResult:
    """Simulate a deploy result from lib_layered_config."""

    action: object
    destination: Path
    dot_d_results: list[FakeDotDResult] = field(default_factory=lambda: [])


@pytest.mark.os_agnostic
def test_deploy_configuration_returns_created_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Only paths with CREATED action are included in the result."""
    from lib_layered_config.examples.deploy import DeployAction

    created_path = tmp_path / "config.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [FakeDeployResult(action=DeployAction.CREATED, destination=created_path)]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert result == [created_path]


@pytest.mark.os_agnostic
def test_deploy_configuration_returns_overwritten_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Paths with OVERWRITTEN action are included in the result."""
    from lib_layered_config.examples.deploy import DeployAction

    overwritten_path = tmp_path / "config.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [FakeDeployResult(action=DeployAction.OVERWRITTEN, destination=overwritten_path)]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER], force=True)

    assert result == [overwritten_path]


@pytest.mark.os_agnostic
def test_deploy_configuration_excludes_skipped_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Paths with SKIPPED action are excluded from the result."""
    from lib_layered_config.examples.deploy import DeployAction

    skipped_path = tmp_path / "config.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [FakeDeployResult(action=DeployAction.SKIPPED, destination=skipped_path)]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert result == []


@pytest.mark.os_agnostic
def test_deploy_configuration_includes_dot_d_created_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dot_d_results with CREATED action are included in the result."""
    from lib_layered_config.examples.deploy import DeployAction

    main_path = tmp_path / "config.toml"
    dot_d_path = tmp_path / "50-mail.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [
            FakeDeployResult(
                action=DeployAction.CREATED,
                destination=main_path,
                dot_d_results=[FakeDotDResult(action=DeployAction.CREATED, destination=dot_d_path)],
            )
        ]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert main_path in result
    assert dot_d_path in result


@pytest.mark.os_agnostic
def test_deploy_configuration_excludes_dot_d_skipped_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dot_d_results with SKIPPED action are excluded from the result."""
    from lib_layered_config.examples.deploy import DeployAction

    main_path = tmp_path / "config.toml"
    skipped_dot_d = tmp_path / "50-mail.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [
            FakeDeployResult(
                action=DeployAction.CREATED,
                destination=main_path,
                dot_d_results=[FakeDotDResult(action=DeployAction.SKIPPED, destination=skipped_dot_d)],
            )
        ]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert main_path in result
    assert skipped_dot_d not in result


@pytest.mark.os_agnostic
def test_deploy_configuration_converts_multiple_targets_to_strings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Multiple DeployTarget enums are converted to string values for lib_layered_config."""
    from lib_layered_config.examples.deploy import DeployAction

    captured_targets: list[list[str]] = []

    def fake_deploy_config(**kwargs: Any) -> list[FakeDeployResult]:
        captured_targets.append(kwargs["targets"])
        return [FakeDeployResult(action=DeployAction.CREATED, destination=tmp_path / "config.toml")]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    deploy_mod.deploy_configuration(targets=[DeployTarget.USER, DeployTarget.HOST])

    assert captured_targets == [["user", "host"]]


@pytest.mark.os_agnostic
def test_deploy_configuration_passes_force_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The force flag is forwarded to lib_layered_config's deploy_config."""
    from lib_layered_config.examples.deploy import DeployAction

    captured_force: list[bool] = []

    def fake_deploy_config(**kwargs: Any) -> list[FakeDeployResult]:
        captured_force.append(kwargs["force"])
        return [FakeDeployResult(action=DeployAction.CREATED, destination=tmp_path / "config.toml")]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    deploy_mod.deploy_configuration(targets=[DeployTarget.USER], force=True)

    assert captured_force == [True]


@pytest.mark.os_agnostic
def test_deploy_configuration_passes_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The profile name is forwarded to lib_layered_config's deploy_config."""
    from lib_layered_config.examples.deploy import DeployAction

    captured_profiles: list[str | None] = []

    def fake_deploy_config(**kwargs: Any) -> list[FakeDeployResult]:
        captured_profiles.append(kwargs["profile"])
        return [FakeDeployResult(action=DeployAction.CREATED, destination=tmp_path / "config.toml")]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    deploy_mod.deploy_configuration(targets=[DeployTarget.USER], profile="production")

    assert captured_profiles == ["production"]


@pytest.mark.os_agnostic
def test_deploy_configuration_validates_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid profile names are rejected before calling deploy_config."""
    with pytest.raises(ValueError, match="Invalid profile"):
        deploy_mod.deploy_configuration(targets=[DeployTarget.USER], profile="../escape")


@pytest.mark.os_agnostic
def test_deploy_configuration_returns_only_created_and_overwritten_from_mixed_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Mixed CREATED/OVERWRITTEN/SKIPPED results return only written paths."""
    from lib_layered_config.examples.deploy import DeployAction

    created_path = tmp_path / "created.toml"
    overwritten_path = tmp_path / "overwritten.toml"
    skipped_path = tmp_path / "skipped.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [
            FakeDeployResult(action=DeployAction.CREATED, destination=created_path),
            FakeDeployResult(action=DeployAction.SKIPPED, destination=skipped_path),
            FakeDeployResult(action=DeployAction.OVERWRITTEN, destination=overwritten_path),
        ]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER], force=True)

    assert created_path in result
    assert overwritten_path in result
    assert skipped_path not in result
    assert len(result) == 2


@pytest.mark.os_agnostic
def test_deploy_configuration_mixed_dot_d_actions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Mixed dot_d actions alongside main result filter correctly."""
    from lib_layered_config.examples.deploy import DeployAction

    main_path = tmp_path / "config.toml"
    created_dot_d = tmp_path / "50-mail.toml"
    overwritten_dot_d = tmp_path / "90-logging.toml"
    skipped_dot_d = tmp_path / "99-extra.toml"

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [
            FakeDeployResult(
                action=DeployAction.CREATED,
                destination=main_path,
                dot_d_results=[
                    FakeDotDResult(action=DeployAction.CREATED, destination=created_dot_d),
                    FakeDotDResult(action=DeployAction.OVERWRITTEN, destination=overwritten_dot_d),
                    FakeDotDResult(action=DeployAction.SKIPPED, destination=skipped_dot_d),
                ],
            )
        ]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER], force=True)

    assert main_path in result
    assert created_dot_d in result
    assert overwritten_dot_d in result
    assert skipped_dot_d not in result
    assert len(result) == 3


@pytest.mark.os_agnostic
def test_deploy_configuration_returns_empty_when_all_skipped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When all results are SKIPPED, an empty list is returned."""
    from lib_layered_config.examples.deploy import DeployAction

    def fake_deploy_config(**_kwargs: Any) -> list[FakeDeployResult]:
        return [
            FakeDeployResult(action=DeployAction.SKIPPED, destination=tmp_path / "a.toml"),
            FakeDeployResult(action=DeployAction.SKIPPED, destination=tmp_path / "b.toml"),
        ]

    monkeypatch.setattr(deploy_mod, "deploy_config", fake_deploy_config)

    result = deploy_mod.deploy_configuration(targets=[DeployTarget.USER, DeployTarget.HOST])

    assert result == []
