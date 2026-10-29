"""On a free-threaded build the CLI runs with the GIL off.

CPython turns the GIL back on, with a ``RuntimeWarning``, when it imports an extension module that
does not declare free-threading support. orjson and rtoml are such modules, so the package keeps
both out of a free-threaded process. The check runs the real CLI in a fresh interpreter, because
the test process has already imported whatever pytest and its plugins load. ``PYTHON_GIL`` is
removed and ``-X gil=0`` is not passed: either would force the GIL off and hide the import that
turned it back on. ``-W error::RuntimeWarning`` makes that import fail the run instead.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

_FREE_THREADED = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))


@pytest.mark.os_agnostic
@pytest.mark.skipif(not _FREE_THREADED, reason="needs a free-threaded (Py_GIL_DISABLED) interpreter")
def test_a_config_override_runs_with_the_gil_off(tmp_path: Path) -> None:
    verdict_file = tmp_path / "verdict.json"
    env = {name: value for name, value in os.environ.items() if name != "PYTHON_GIL"}
    env["GIL_PROBE_VERDICT"] = str(verdict_file)

    # The probe is a literal argv element and its output path comes through the environment:
    # ruff's S603 flags an argv spliced from a variable as untrusted input.
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::RuntimeWarning",
            "-c",
            """
import json
import os
import sys

from bitranox_template_py_cli.adapters.cli.main import main
from bitranox_template_py_cli.composition import build_production

argv = ["--set", 'email.smtp_hosts=["a.test:25"]', "config", "--format", "json", "--section", "email"]
code = main(argv, services_factory=build_production)
verdict = {
    "exit": code,
    "gil": sys._is_gil_enabled(),
    "loaded": sorted(name for name in ("orjson", "rtoml") if name in sys.modules),
}
with open(os.environ["GIL_PROBE_VERDICT"], "w", encoding="utf-8") as handle:
    json.dump(verdict, handle)
""",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["email"]["smtp_hosts"] == ["a.test:25"]
    assert json.loads(verdict_file.read_text(encoding="utf-8")) == {"exit": 0, "gil": False, "loaded": []}
