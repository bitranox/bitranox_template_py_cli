"""Profile validation tests."""

from __future__ import annotations

import pytest


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
