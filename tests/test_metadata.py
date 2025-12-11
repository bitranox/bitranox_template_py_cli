"""Tests for metadata synchronization between pyproject.toml and __init__conf__.py.

Validates that the package metadata constants match their source in pyproject.toml.
Tests real files rather than stubs to ensure actual synchronization.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import pytest

from bitranox_template_py_cli import __init__conf__

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def load_pyproject() -> dict[str, Any]:
    """Load pyproject.toml as a dictionary."""
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# Metadata Field Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_name_matches_pyproject() -> None:
    """The package name matches pyproject.toml."""
    pyproject = load_pyproject()

    assert __init__conf__.name == pyproject["project"]["name"]


@pytest.mark.os_agnostic
def test_title_matches_pyproject_description() -> None:
    """The title matches pyproject.toml description."""
    pyproject = load_pyproject()

    assert __init__conf__.title == pyproject["project"]["description"]


@pytest.mark.os_agnostic
def test_version_matches_pyproject() -> None:
    """The version matches pyproject.toml."""
    pyproject = load_pyproject()

    assert __init__conf__.version == pyproject["project"]["version"]


@pytest.mark.os_agnostic
def test_homepage_matches_pyproject_urls() -> None:
    """The homepage matches pyproject.toml URLs."""
    pyproject = load_pyproject()

    assert __init__conf__.homepage == pyproject["project"]["urls"]["Homepage"]


@pytest.mark.os_agnostic
def test_author_matches_pyproject() -> None:
    """The author matches first pyproject.toml author."""
    pyproject = load_pyproject()
    authors = pyproject["project"]["authors"]

    assert authors, "pyproject.toml must have at least one author"
    assert __init__conf__.author == authors[0]["name"]


@pytest.mark.os_agnostic
def test_author_email_matches_pyproject() -> None:
    """The author email matches first pyproject.toml author."""
    pyproject = load_pyproject()
    authors = pyproject["project"]["authors"]

    assert authors, "pyproject.toml must have at least one author"
    assert __init__conf__.author_email == authors[0]["email"]


@pytest.mark.os_agnostic
def test_shell_command_is_registered_script() -> None:
    """The shell command is a registered console script."""
    pyproject = load_pyproject()
    scripts = pyproject["project"].get("scripts", {})

    assert __init__conf__.shell_command in scripts


# ---------------------------------------------------------------------------
# print_info Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_print_info_outputs_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info writes to stdout."""
    __init__conf__.print_info()

    captured = capsys.readouterr()

    assert captured.out
    assert captured.err == ""


@pytest.mark.os_agnostic
def test_print_info_includes_package_name(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info output includes the package name."""
    __init__conf__.print_info()

    output = capsys.readouterr().out

    assert __init__conf__.name in output


@pytest.mark.os_agnostic
def test_print_info_includes_version(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info output includes the version."""
    __init__conf__.print_info()

    output = capsys.readouterr().out

    assert __init__conf__.version in output


@pytest.mark.os_agnostic
def test_print_info_includes_all_field_labels(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info output includes all field labels."""
    __init__conf__.print_info()

    output = capsys.readouterr().out

    expected_labels = ["name", "title", "version", "homepage", "author", "author_email", "shell_command"]
    for label in expected_labels:
        assert label in output


@pytest.mark.os_agnostic
def test_print_info_shows_header() -> None:
    """print_info shows a header with the package name."""
    import io
    import sys

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        __init__conf__.print_info()
    finally:
        sys.stdout = old_stdout

    output = buffer.getvalue()
    assert f"Info for {__init__conf__.name}:" in output


# ---------------------------------------------------------------------------
# Module Constants Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_layered_config_vendor_is_string() -> None:
    """LAYEREDCONF_VENDOR is a non-empty string."""
    assert isinstance(__init__conf__.LAYEREDCONF_VENDOR, str)
    assert __init__conf__.LAYEREDCONF_VENDOR


@pytest.mark.os_agnostic
def test_layered_config_app_is_string() -> None:
    """LAYEREDCONF_APP is a non-empty string."""
    assert isinstance(__init__conf__.LAYEREDCONF_APP, str)
    assert __init__conf__.LAYEREDCONF_APP


@pytest.mark.os_agnostic
def test_layered_config_slug_is_string() -> None:
    """LAYEREDCONF_SLUG is a non-empty string."""
    assert isinstance(__init__conf__.LAYEREDCONF_SLUG, str)
    assert __init__conf__.LAYEREDCONF_SLUG


@pytest.mark.os_agnostic
def test_layered_config_slug_is_lowercase() -> None:
    """LAYEREDCONF_SLUG is lowercase with hyphens."""
    slug = __init__conf__.LAYEREDCONF_SLUG

    assert slug == slug.lower()
    assert "_" not in slug or "-" in slug


# ---------------------------------------------------------------------------
# pyproject.toml Structural Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_pyproject_exists() -> None:
    """pyproject.toml exists in the project root."""
    assert PYPROJECT_PATH.exists()


@pytest.mark.os_agnostic
def test_pyproject_has_project_section() -> None:
    """pyproject.toml has a [project] section."""
    pyproject = load_pyproject()

    assert "project" in pyproject


@pytest.mark.os_agnostic
def test_pyproject_has_required_fields() -> None:
    """pyproject.toml has all required project fields."""
    pyproject = load_pyproject()
    project = pyproject["project"]

    required = ["name", "version", "description", "authors", "urls"]
    for field in required:
        assert field in project, f"Missing required field: {field}"


@pytest.mark.os_agnostic
def test_pyproject_has_homepage_url() -> None:
    """pyproject.toml has a Homepage URL."""
    pyproject = load_pyproject()

    assert "Homepage" in pyproject["project"]["urls"]
