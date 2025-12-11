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
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

<agent: fill in short project description and main features>
- CLI entry point styled with rich-click (rich output + click ergonomics)
- Exit-code and messaging helpers powered by lib_cli_exit_tools

## Install - recommended via UV
UV - the ultrafast installer - written in Rust (10–20× faster than pip/poetry)

```bash
# recommended Install via uv 
pip install --upgrade uv
# Create and activate a virtual environment (optional but recommended)
uv venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# install via uv from PyPI
uv pip install bitranox_template_py_cli
```

For alternative install paths (pip, pipx, uv, uvx source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`bitranox_template_py_cli` and `bitranox-template-py-cli` commands on your PATH.

### Python 3.10+ Compatibility

- The project targets **Python 3.10 and newer**.
- Runtime dependencies stay on the current stable releases (`rich-click>=1.9.4`
  and `lib_cli_exit_tools>=2.2.1`) and keeps pytest, ruff, pyright, bandit,
  build, twine, codecov-cli, pip-audit, textual, and import-linter pinned to
  their newest majors.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.10 through the latest
  available 3.x release provided by Actions.


## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.
The scaffold keeps a CLI entry point so you can validate packaging flows, but it
currently exposes a single informational command while logging features are
developed:

```bash
bitranox_template_py_cli info
bitranox_template_py_cli hello
bitranox_template_py_cli fail              # errors show summary (default: --no-traceback)
bitranox_template_py_cli --traceback fail  # errors show full Python traceback
bitranox-template-py-cli info
python -m bitranox_template_py_cli info
uvx bitranox_template_py_cli info
```

### Traceback Mode

By default, errors display a concise summary (`--no-traceback`). Use `--traceback`
to see full Python tracebacks for debugging:

```bash
# Default: concise error summary
bitranox_template_py_cli fail

# Verbose: full traceback with colors
bitranox_template_py_cli --traceback fail
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
