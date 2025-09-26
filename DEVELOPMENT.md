# Development

## Make Targets

| Target            | Description                                                                                |
|-------------------|--------------------------------------------------------------------------------------------|
| `help`            | Show help                                                                                  |
| `install`         | Install package editable                                                                   |
| `dev`             | Install package with dev extras                                                            |
| `test`            | Lint, type-check, run tests with coverage, upload to Codecov                               |
| `run`             | Run module CLI (requires dev install or src on PYTHONPATH)                                 |
| `version-current` | Print current version from pyproject.toml                                                  |
| `bump`            | Bump version (updates pyproject.toml and CHANGELOG.md)                                     |
| `bump-patch`      | Bump patch version (X.Y.Z -> X.Y.(Z+1))                                                    |
| `bump-minor`      | Bump minor version (X.Y.Z -> X.(Y+1).0)                                                    |
| `bump-major`      | Bump major version ((X+1).0.0)                                                             |
| `clean`           | Remove caches, build artifacts, and coverage                                               |
| `push`            | Run tests, prompt for/accept a commit message, create (allow-empty) commit, push to remote |
| `build`           | Build wheel/sdist and attempt conda, brew, and nix builds (auto-installs tools if missing) |
| `menu`            | Interactive TUI to run targets and edit parameters (requires dev dep: textual)             |

### Target Parameters (env vars)

- **Global**
  - `PY` (default: `python3`) — interpreter used to run scripts
  - `PIP` (default: `pip`) — pip executable used by bootstrap/install

- **install**
  - No specific parameters (respects `PY`, `PIP`).

- **dev**
  - No specific parameters (respects `PY`, `PIP`).

- **test**
  - `COVERAGE=on|auto|off` (default: `on`) — controls pytest coverage run and Codecov upload
  - `SKIP_BOOTSTRAP=1` — skip auto-install of dev tools if missing
  - `TEST_VERBOSE=1` — echo each command executed by the test harness
  - Also respects `CODECOV_TOKEN` when uploading to Codecov

- **run**
  - No parameters via `make` (always shows `--help`). For custom args: `python scripts/run_cli.py -- <args>`.

- **version-current**
  - No parameters

- **bump**
  - `VERSION=X.Y.Z` — explicit target version
  - `PART=major|minor|patch` — semantic part to bump (default if `VERSION` not set: `patch`)

- **bump-patch** / **bump-minor** / **bump-major**
  - No parameters; shorthand for `make bump PART=...`

- **clean**
  - No parameters

- **push**
  - `REMOTE=<name>` (default: `origin`) — git remote to push to
  - `COMMIT_MESSAGE="..."` — optional commit message used by the automation; if unset, the target prompts (or uses the default `chore: update` when non-interactive).

- **build**
  - No parameters via `make`. Advanced: call the script directly, e.g. `python scripts/build.py --no-conda --no-nix`.

- **release**
  - `REMOTE=<name>` (default: `origin`) — git remote to push to
  - Advanced (via script): `python scripts/release.py --retries 5 --retry-wait 3.0`

## Interactive Menu (Textual)

`make menu` launches a Textual-powered TUI to browse targets, edit parameters, and run them with live output.

Install dev extras if you haven’t:

```bash
pip install -e .[dev]
```

Run the menu:

```bash
make menu
```

### Target Details

- `test`: single entry point for local CI — runs ruff lint + format check, pyright, pytest (including doctests) with coverage (enabled by default), and uploads coverage to Codecov if configured (reads `.env`).
  - Auto-bootstrap: `make test` will try to install dev tools (`pip install -e .[dev]`) if `ruff`/`pyright`/`pytest` are missing. Set `SKIP_BOOTSTRAP=1` to skip this behavior.
- `build`: creates wheel/sdist, then attempts Conda, Homebrew, and Nix builds. It auto-installs missing tools (Miniforge, Homebrew, Nix) when needed.
- `version-current`: prints current version from `pyproject.toml`.
- `bump`: updates `pyproject.toml` version and inserts a new section in `CHANGELOG.md`. Use `VERSION=X.Y.Z make bump` or `make bump-minor`/`bump-major`/`bump-patch`.
- Additional scripts (`pipx-*`, `uv-*`, `which-cmd`, `verify-install`) provide install/run diagnostics.

## Development Workflow

```bash
make test                 # ruff + pyright + pytest + coverage (default ON)
SKIP_BOOTSTRAP=1 make test  # skip auto-install of dev deps
COVERAGE=off make test       # disable coverage locally
COVERAGE=on make test        # force coverage and generate coverage.xml/codecov.xml
```

**Automation notes**

- `make test` creates an allow-empty commit (`test: auto commit before Codecov upload`) just before uploading coverage so Codecov receives a concrete revision. If you do not want to keep that commit, run `git reset --soft HEAD~1` or `git commit --amend` once the upload finishes.
- `make push` prompts for a commit message (or reads `COMMIT_MESSAGE="..."`) and always pushes, creating an empty commit when there are no staged changes. The Textual menu (`make menu → push`) shows the same prompt via an input field.

### Packaging sync (Conda/Brew/Nix)

- `make test` and `make push` automatically align the packaging skeletons in `packaging/` with the current `pyproject.toml`:
  - Conda: updates `{% set version = "X.Y.Z" %}` and both `python >=X.Y` constraints to match `requires-python`.
  - Homebrew: updates the source URL tag to `vX.Y.Z` and sets `depends_on "python@X.Y"` to match `requires-python`.
  - Nix: updates the package `version`, example `rev = "vX.Y.Z"`, and switches `pkgs.pythonXYZPackages` / `pkgs.pythonXYZ` to match the minimum Python version from `requires-python`.

- To run just the sync without bumping versions: `python scripts/bump_version.py --sync-packaging`.

- On release tags (`v*.*.*`), CI validates that packaging files are consistent with `pyproject.toml` and will fail if they drift.

### Versioning & Metadata

- Single source of truth for package metadata is `pyproject.toml` (`[project]`).
- The library reads its own installed metadata at runtime via `importlib.metadata` (see `src/bitranox_template_py_cli/__init__conf__.py`).
- Do not duplicate the version in code; bump only `pyproject.toml` and update `CHANGELOG.md`.
- Console script name is discovered from entry points; defaults to `bitranox_template_py_cli`.

### Packaging Skeletons

Starter files for package managers live under `packaging/`:

- The CLI is built on `rich-click`, so help and errors inherit Rich styling while preserving click semantics.

- Conda: `packaging/conda/recipe/meta.yaml` (update version + sha256)
- Homebrew: `packaging/brew/Formula/bitranox-template-py-cli.rb` (fill sha256 and vendored resources)
- Nix: `packaging/nix/flake.nix` (use working tree or pin to GitHub rev with sha256)

These are templates; fill placeholders (e.g., sha256) before publishing. Version and Python constraints are auto-synced from `pyproject.toml` by `make test`/`make push` and during version bumps.

### CI & Publishing

GitHub Actions workflows are included:

- `.github/workflows/ci.yml` — lint/type/test, build wheel/sdist, verify pipx and uv installs, Nix and Conda builds (CI-only; no local install required).
- `.github/workflows/release.yml` — on tags `v*.*.*`, builds artifacts and publishes to PyPI when `PYPI_API_TOKEN` secret is set.

To publish a release:
1. Bump `pyproject.toml` version and update `CHANGELOG.md`.
2. Tag the commit (`git tag v0.1.1 && git push --tags`).
3. Ensure `PYPI_API_TOKEN` secret is configured in the repo.
4. Release workflow uploads wheel/sdist to PyPI.

Conda/Homebrew/Nix: use files in `packaging/` to submit to their ecosystems. CI also attempts builds to validate recipes, but does not publish automatically.

### Local Codecov uploads

- `make test` (with coverage enabled) generates `coverage.xml` and `codecov.xml`, then attempts to upload via the Codecov CLI or the bash uploader.
- For private repos, set `CODECOV_TOKEN` (see `.env.example`) or export it in your shell.
- For public repos, a token is typically not required.
- Because Codecov requires a revision, the test harness commits (allow-empty) immediately before uploading. Remove or amend that commit after the run if you do not intend to keep it.


