"""Tests for metadata synchronization between pyproject.toml and __init__conf__.py.

Validates that the package metadata constants match their source in pyproject.toml.
Tests real files rather than stubs to ensure actual synchronization.
"""

from pathlib import Path

import pytest

from bitranox_template_py_cli import __init__conf__
from conftest import Pyproject, load_pyproject

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def get_pyproject() -> Pyproject:
    """Load and validate pyproject.toml as a typed Pydantic model."""
    return load_pyproject(PYPROJECT_PATH)


# ---------------------------------------------------------------------------
# Metadata Field Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_name_matches_pyproject() -> None:
    """The package name matches pyproject.toml."""
    pyproject = get_pyproject()

    assert __init__conf__.name == pyproject.project.name


@pytest.mark.os_agnostic
def test_title_matches_pyproject_description() -> None:
    """The title matches pyproject.toml description."""
    pyproject = get_pyproject()

    assert __init__conf__.title == pyproject.project.description


@pytest.mark.os_agnostic
def test_version_matches_pyproject() -> None:
    """The version matches pyproject.toml."""
    pyproject = get_pyproject()

    assert __init__conf__.version == pyproject.project.version


@pytest.mark.os_agnostic
def test_homepage_matches_pyproject_urls() -> None:
    """The homepage matches pyproject.toml URLs."""
    pyproject = get_pyproject()

    assert pyproject.project.urls is not None
    assert __init__conf__.homepage == pyproject.project.urls.Homepage


@pytest.mark.os_agnostic
def test_author_matches_pyproject() -> None:
    """The author matches first pyproject.toml author."""
    pyproject = get_pyproject()
    authors = pyproject.project.authors

    assert authors, "pyproject.toml must have at least one author"
    assert __init__conf__.author == authors[0].name


@pytest.mark.os_agnostic
def test_author_email_matches_pyproject() -> None:
    """The author email matches first pyproject.toml author."""
    pyproject = get_pyproject()
    authors = pyproject.project.authors

    assert authors, "pyproject.toml must have at least one author"
    assert __init__conf__.author_email == authors[0].email


@pytest.mark.os_agnostic
def test_shell_command_is_registered_script() -> None:
    """The shell command is a registered console script."""
    pyproject = get_pyproject()
    scripts = pyproject.project.scripts or {}

    assert __init__conf__.shell_command in scripts


# ---------------------------------------------------------------------------
# print_info Tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_print_info_writes_to_stdout_only(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info writes output to stdout and nothing to stderr."""
    __init__conf__.print_info()

    captured = capsys.readouterr()

    assert captured.out
    assert captured.err == ""


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "expected_content",
    [
        pytest.param(__init__conf__.name, id="package_name"),
        pytest.param(__init__conf__.version, id="version"),
        pytest.param("name", id="label_name"),
        pytest.param("title", id="label_title"),
        pytest.param("version", id="label_version"),
        pytest.param("homepage", id="label_homepage"),
        pytest.param("author", id="label_author"),
        pytest.param("author_email", id="label_author_email"),
        pytest.param("shell_command", id="label_shell_command"),
    ],
)
def test_print_info_includes_expected_content(
    capsys: pytest.CaptureFixture[str],
    expected_content: str,
) -> None:
    """print_info output includes expected values and labels."""
    __init__conf__.print_info()
    output = capsys.readouterr().out

    assert expected_content in output


@pytest.mark.os_agnostic
def test_print_info_shows_header(capsys: pytest.CaptureFixture[str]) -> None:
    """print_info output begins with a header containing the package name."""
    __init__conf__.print_info()

    output = capsys.readouterr().out

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
    pyproject = get_pyproject()

    # Pydantic validation ensures project exists; accessing it confirms
    assert pyproject.project is not None


@pytest.mark.os_agnostic
def test_pyproject_has_required_fields() -> None:
    """pyproject.toml has all required project fields."""
    pyproject = get_pyproject()
    project = pyproject.project

    # Pydantic validates required fields; verify they have values
    assert project.name
    assert project.version
    assert project.description
    assert project.authors
    assert project.urls is not None


@pytest.mark.os_agnostic
def test_pyproject_has_homepage_url() -> None:
    """pyproject.toml has a Homepage URL."""
    pyproject = get_pyproject()

    assert pyproject.project.urls is not None
    assert pyproject.project.urls.Homepage is not None
