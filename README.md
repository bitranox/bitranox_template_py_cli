# bitranox_template_py_cli

<!-- Badges -->
[![CI](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/ci.yml/badge.svg)](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/bitranox_template_py_cli?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/bitranox_template_py_cli.svg)](https://pypi.org/project/bitranox_template_py_cli/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bitranox_template_py_cli.svg)](https://pypi.org/project/bitranox_template_py_cli/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/bitranox_template_py_cli/graph/badge.svg?token=UFBaUDIgRk)](https://codecov.io/gh/bitranox/bitranox_template_py_cli)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/bitranox_template_py_cli)
[![Known Vulnerabilities](https://snyk.io/test/github/bitranox/bitranox_template_py_cli/badge.svg)](https://snyk.io/test/github/bitranox/bitranox_template_py_cli)

Scaffold for Python Projects with registered commandline commands:
- CLI entry point styled with rich-click (rich output + click ergonomics)
- Exit-code and messaging helpers powered by lib_cli_exit_tools

## Install

```bash
pip install bitranox_template_py_cli
```

For alternative install paths (pipx, uv, source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`bitranox_template_py_cli` and `bitranox-template-py-cli` commands on your PATH.

### Python 3.13+ Baseline

- The project now targets **Python 3.13 and newer only**. All compatibility
  shims for older interpreters and legacy tool outputs have been removed; the
  automation helpers now lean on modern conveniences such as `Path.unlink(missing_ok=True)`
  and standard-library `shutil.which()` lookups.
- Runtime dependencies stay on the current stable releases (`rich-click>=1.9.3`
  and `lib_cli_exit_tools>=2.0.0`), while the development extra trims unused
  packages (notably `pytest-asyncio`) and keeps pytest, ruff, pyright, bandit,
  build, twine, codecov-cli, pip-audit, textual, and import-linter pinned to
  their newest majors.
- CI workflows now exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.13 alongside the latest
  available 3.x release provided by Actions.


## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.
The scaffold keeps a CLI entry point so you can validate packaging flows, but it
currently exposes a single informational command while logging features are
developed:

```bash
bitranox_template_py_cli info
bitranox_template_py_cli hello
bitranox_template_py_cli fail
bitranox_template_py_cli --traceback fail
bitranox-template-py-cli info
python -m bitranox_template_py_cli info
```

For library use you can import the documented helpers directly:

```python
import bitranox_template_py_cli as btpc

btpc.emit_greeting()
try:
    btpc.raise_intentional_failure()
except RuntimeError as exc:
    print(f"caught expected failure: {exc}")

btpc.print_info()
```


## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)
