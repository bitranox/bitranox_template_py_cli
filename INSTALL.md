# Installation Guide

> The CLI stack uses `rich-click`, which bundles `rich` styling on top of click-style ergonomics.

This guide collects every supported method to install `bitranox_template_py_cli`, including
isolated environments and system package managers. Pick the option that matches your workflow.

## 1. Standard Virtual Environment (pip)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]       # development install
# or for runtime only:
pip install .
```

## 2. Per-User Installation (No Virtualenv)

```bash
pip install --user .
```

> Note: This respects PEP 668. Avoid using it on system Python builds marked as
> "externally managed". Ensure `~/.local/bin` (POSIX) is on your PATH so the CLI is available.

## 3. pipx (Isolated CLI-Friendly Environment)

```bash
pipx install .
pipx upgrade bitranox_template_py_cli
# From Git tag/commit:
pipx install "git+https://github.com/bitranox/bitranox_template_py_cli"
```

## 4. uv (Fast Installer/Runner)

```bash
uv pip install -e .[dev]
uv tool install .
uvx bitranox_template_py_cli --help
```

## 5. From Build Artifacts

```bash
python -m build
pip install dist/bitranox_template_py_cli-*.whl
pip install dist/bitranox_template_py_cli-*.tar.gz   # sdist
```

## 6. Poetry or PDM Managed Environments

```bash
# Poetry
poetry add bitranox_template_py_cli     # as dependency
poetry install                          # for local dev

# PDM
pdm add bitranox_template_py_cli
pdm install
```

## 7. Install Directly from Git

```bash
pip install "git+https://github.com/bitranox/bitranox_template_py_cli#egg=bitranox_template_py_cli"
```

## 8. Conda or Mamba Environment

```bash
mamba create -n bitranox-template-py-cli python=3.12 pip
mamba activate bitranox-template-py-cli
pip install .
```

## 9. System Package Managers (Optional Distribution Channels)

- Homebrew (macOS): `brew install bitranox_template_py_cli` (if published)
- Nix: Use the flake or package definition for reproducible installs
- Deb/RPM: Package with `fpm` for OS-native delivery

All methods register both the `bitranox_template_py_cli` and
`bitranox-template-py-cli` commands on your PATH.
