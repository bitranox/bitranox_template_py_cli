"""Verify that __init__conf__ constants stay in sync with pyproject.toml.

These tests catch configuration drift that could cause silent failures
in config path resolution when LAYEREDCONF_* values don't match the
actual project metadata.
"""

from __future__ import annotations

from importlib.metadata import metadata

import pytest

from bitranox_template_py_cli import __init__conf__


@pytest.mark.os_agnostic
def test_layeredconf_slug_matches_project_name() -> None:
    """LAYEREDCONF_SLUG must be derived from the project name.

    The slug is used for Linux config paths (e.g., ~/.config/<slug>/).
    If it drifts from the project name, config files won't be found.
    """
    meta = metadata("bitranox_template_py_cli")
    project_name = meta["Name"]

    # Slug should be the hyphenated form of the project name
    expected_slug = project_name.replace("_", "-")
    assert expected_slug == __init__conf__.LAYEREDCONF_SLUG, (
        f"LAYEREDCONF_SLUG '{__init__conf__.LAYEREDCONF_SLUG}' does not match "
        f"project name '{project_name}' (expected '{expected_slug}')"
    )


@pytest.mark.os_agnostic
def test_layeredconf_vendor_is_not_empty() -> None:
    """LAYEREDCONF_VENDOR must be set for macOS/Windows config paths."""
    assert __init__conf__.LAYEREDCONF_VENDOR, "LAYEREDCONF_VENDOR is empty"
    assert __init__conf__.LAYEREDCONF_VENDOR.strip(), "LAYEREDCONF_VENDOR is whitespace-only"


@pytest.mark.os_agnostic
def test_layeredconf_app_is_not_empty() -> None:
    """LAYEREDCONF_APP must be set for macOS/Windows config paths."""
    assert __init__conf__.LAYEREDCONF_APP, "LAYEREDCONF_APP is empty"
    assert __init__conf__.LAYEREDCONF_APP.strip(), "LAYEREDCONF_APP is whitespace-only"


@pytest.mark.os_agnostic
def test_version_matches_pyproject_toml() -> None:
    """__init__conf__.version must match pyproject.toml version.

    This catches version string drift between pyproject.toml and __init__conf__.py.
    Reads pyproject.toml directly since during development the installed package
    may lag behind source changes.
    """
    from pathlib import Path

    import rtoml

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject_data = rtoml.load(pyproject_path)
    pyproject_version = pyproject_data["project"]["version"]

    assert __init__conf__.version == pyproject_version, (
        f"__init__conf__.version '{__init__conf__.version}' does not match pyproject.toml version '{pyproject_version}'"
    )


@pytest.mark.os_agnostic
def test_name_matches_installed_package() -> None:
    """__init__conf__.name must match the installed package name."""
    meta = metadata("bitranox_template_py_cli")
    installed_name = meta["Name"]

    # Package names are normalized (underscores → hyphens in some contexts)
    # but __init__conf__.name should match the canonical form
    assert __init__conf__.name.replace("-", "_") == installed_name.replace("-", "_"), (
        f"__init__conf__.name '{__init__conf__.name}' does not match installed package name '{installed_name}'"
    )
