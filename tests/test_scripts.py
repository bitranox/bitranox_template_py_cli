from __future__ import annotations

from click.testing import CliRunner
from collections.abc import Mapping, Sequence
import sys
from types import ModuleType, SimpleNamespace
from typing import Protocol, TypedDict

from pytest import MonkeyPatch

import scripts.build as build
import scripts.cli as cli
import scripts.dev as dev
import scripts.install as install
import scripts.run_cli as run_cli
import scripts.test as test_script
from scripts._utils import RunResult
from scripts import _utils


RunCommand = Sequence[str] | str
ModuleLike = ModuleType | SimpleNamespace


class RecordedOptions(TypedDict):
    check: bool
    capture: bool
    cwd: str | None
    env: Mapping[str, str] | None
    dry_run: bool


RunRecord = tuple[RunCommand, RecordedOptions]


class RunStub(Protocol):
    def __call__(
        self,
        cmd: RunCommand,
        *,
        check: bool = True,
        capture: bool = True,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        dry_run: bool = False,
    ) -> RunResult: ...


def _make_run_recorder(record: list[RunRecord]) -> RunStub:
    def _run(
        cmd: RunCommand,
        *,
        check: bool = True,
        capture: bool = True,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        dry_run: bool = False,
    ) -> RunResult:
        record.append(
            (
                cmd,
                {
                    "check": check,
                    "capture": capture,
                    "cwd": cwd,
                    "env": env,
                    "dry_run": dry_run,
                },
            ),
        )
        return RunResult(0, "", "")

    return _run


def test_get_project_metadata_fields():
    meta = _utils.get_project_metadata()
    assert meta.name == "bitranox_template_py_cli"
    assert meta.slug == "bitranox-template-py-cli"
    assert meta.import_package == "bitranox_template_py_cli"
    assert meta.coverage_source == "src/bitranox_template_py_cli"
    assert meta.github_tarball_url("1.2.3").endswith("/bitranox/bitranox_template_py_cli/archive/refs/tags/v1.2.3.tar.gz")


def test_build_script_uses_metadata(monkeypatch: MonkeyPatch) -> None:
    recorded: list[RunRecord] = []
    monkeypatch.setattr(build, "run", _make_run_recorder(recorded))
    runner = CliRunner()
    result = runner.invoke(cli.main, ["build"])
    assert result.exit_code == 0
    commands = [" ".join(cmd) if not isinstance(cmd, str) else cmd for cmd, _ in recorded]
    assert any("python -m build" in cmd for cmd in commands)


def test_dev_script_installs_dev_extras(monkeypatch: MonkeyPatch) -> None:
    recorded: list[RunRecord] = []
    monkeypatch.setattr(dev, "run", _make_run_recorder(recorded))
    runner = CliRunner()
    result = runner.invoke(cli.main, ["dev"])
    assert result.exit_code == 0
    first_command, _options = recorded[0]
    assert isinstance(first_command, list)
    assert first_command == [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]


def test_install_script_installs_package(monkeypatch: MonkeyPatch) -> None:
    recorded: list[RunRecord] = []
    monkeypatch.setattr(install, "run", _make_run_recorder(recorded))
    runner = CliRunner()
    result = runner.invoke(cli.main, ["install"])
    assert result.exit_code == 0
    first_command, _options = recorded[0]
    assert isinstance(first_command, list)
    assert first_command == [sys.executable, "-m", "pip", "install", "-e", "."]


def test_run_cli_imports_dynamic_package(monkeypatch: MonkeyPatch) -> None:
    seen: list[str] = []

    def _run_cli_main(_args: Sequence[str] | None = None) -> int:
        return 0

    def fake_import(name: str) -> ModuleLike:
        seen.append(name)
        if name.endswith(".__main__"):
            return SimpleNamespace()
        if name.endswith(".cli"):
            return SimpleNamespace(main=_run_cli_main)
        raise AssertionError(f"unexpected import {name}")

    monkeypatch.setattr(run_cli, "import_module", fake_import)
    runner = CliRunner()
    result = runner.invoke(cli.main, ["run"])
    assert result.exit_code == 0
    package = run_cli.PROJECT.import_package
    assert f"{package}.cli" in seen
    if len(seen) == 2:
        assert seen == [f"{package}.__main__", f"{package}.cli"]


def test_test_script_uses_pyproject_configuration(monkeypatch: MonkeyPatch) -> None:
    recorded: list[RunRecord] = []

    def _noop() -> None:
        return None

    def _always_false(_name: str) -> bool:
        return False

    monkeypatch.setattr(test_script, "bootstrap_dev", _noop)
    monkeypatch.setattr(_utils, "cmd_exists", _always_false)
    monkeypatch.setattr(test_script, "run", _make_run_recorder(recorded))
    runner = CliRunner()
    result = runner.invoke(cli.main, ["test"])
    assert result.exit_code == 0
    pytest_commands: list[list[str]] = []
    for cmd, _ in recorded:
        if isinstance(cmd, str):
            continue
        command_list = list(cmd)
        if command_list[:3] == ["python", "-m", "pytest"]:
            pytest_commands.append(command_list)
    assert pytest_commands, "pytest not invoked"
    assert any(f"--cov={test_script.COVERAGE_TARGET}" in " ".join(sequence) for sequence in pytest_commands)
