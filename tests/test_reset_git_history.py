"""reset_git_history.sh publishes the whole project tree, untracked files included.

A repository freshly copied from the template and renamed holds its renamed package as UNTRACKED
files: rename.sh moves ``src/<old>/`` to ``src/<new>/`` on disk and git sees only the deletion of
the old path. The script squashes history and force-pushes, so a tree that leaves the untracked
package out publishes a repository without its source. These tests drive the real script against
a scratch repository with a bare repository as its remote.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "reset_git_history.sh"
# Absolute paths: a bare name is resolved against whatever PATH the test inherits.
GIT = shutil.which("git") or ""
BASH = shutil.which("bash") or ""

# The script is a working-tree helper the sdist does not ship, so a run from an unpacked sdist has
# nothing to test.
pytestmark = [
    pytest.mark.skipif(not SCRIPT.is_file(), reason="reset_git_history.sh is not shipped in the sdist"),
    pytest.mark.skipif(not GIT, reason="git is not installed"),
    pytest.mark.skipif(not BASH, reason="bash is not installed"),
]


def _git_env(home: Path) -> dict[str, str]:
    # Inherited GIT_* variables (GIT_DIR from a hook, pathspec modes) would point git at another
    # repository, and the user's global config may sign or hook commits; neither belongs here.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env |= {
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "LC_ALL": "C",
    }
    return env


def _git(cwd: Path, env: dict[str, str], *args: str) -> str:
    done = subprocess.run(  # noqa: S603 - argv is git plus literal arguments from this module
        [GIT, *args], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    )
    return done.stdout


def _renamed_repository(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    """A repository whose package was renamed on disk but not staged, plus its bare remote."""
    env = _git_env(tmp_path)
    remote = tmp_path / "remote.git"
    _git(tmp_path, env, "init", "--bare", "-b", "main", str(remote))
    repo = tmp_path / "repo"
    (repo / "src" / "oldpkg").mkdir(parents=True)
    (repo / "src" / "oldpkg" / "__init__.py").write_text("OLD = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("old\n", encoding="utf-8")
    _git(tmp_path, env, "init", "-b", "main", str(repo))
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-q", "-m", "first")
    _git(repo, env, "remote", "add", "origin", str(remote))
    shutil.move(repo / "src" / "oldpkg", repo / "src" / "newpkg")
    (repo / "README.md").write_text("new\n", encoding="utf-8")
    return repo, remote, env


def _run_script(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed argv: bash running this repository's script
        [BASH, str(SCRIPT), "origin"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


@pytest.mark.os_posix
def test_the_pushed_tree_holds_the_untracked_renamed_package(tmp_path: Path) -> None:
    repo, remote, env = _renamed_repository(tmp_path)

    done = _run_script(repo, env)

    assert done.returncode == 0, done.stderr
    pushed = _git(remote, env, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert "src/newpkg/__init__.py" in pushed
    assert "src/oldpkg/__init__.py" not in pushed


@pytest.mark.os_posix
def test_the_pushed_history_is_a_single_commit(tmp_path: Path) -> None:
    repo, remote, env = _renamed_repository(tmp_path)

    done = _run_script(repo, env)

    assert done.returncode == 0, done.stderr
    assert _git(remote, env, "rev-list", "--count", "main").strip() == "1"


@pytest.mark.os_posix
def test_a_gitignored_file_is_not_published(tmp_path: Path) -> None:
    repo, remote, env = _renamed_repository(tmp_path)
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / ".env").write_text("TOKEN=not-for-publication\n", encoding="utf-8")

    done = _run_script(repo, env)

    assert done.returncode == 0, done.stderr
    pushed = _git(remote, env, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert ".env" not in pushed
    assert ".gitignore" in pushed


@pytest.mark.os_posix
def test_intellij_settings_are_not_published_even_when_not_ignored(tmp_path: Path) -> None:
    repo, remote, env = _renamed_repository(tmp_path)
    (repo / ".idea").mkdir()
    (repo / ".idea" / "workspace.xml").write_text("<project/>\n", encoding="utf-8")

    done = _run_script(repo, env)

    assert done.returncode == 0, done.stderr
    pushed = _git(remote, env, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert ".idea/workspace.xml" not in pushed
    assert (repo / ".idea" / "workspace.xml").is_file()
