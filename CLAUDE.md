# Claude Code Guidelines for bitranox_template_py_cli

## Session Initialization

When starting a new session, read and apply the following system prompt files from `/media/srv-main-softdev/projects/softwarestack/systemprompts`:

### Core Guidelines (Always Apply)
- `core_programming_solid.md`

### Bash-Specific Guidelines
When working with Bash scripts:
- `core_programming_solid.md`
- `bash_clean_architecture.md`
- `bash_clean_code.md`
- `bash_small_functions.md`

### Python-Specific Guidelines
When working with Python code:
- `core_programming_solid.md`
- `python_solid_architecture_enforcer.md`
- `python_clean_architecture.md`
- `python_clean_code.md`
- `python_small_functions_style.md`
- `python_libraries_to_use.md`
- `python_structure_template.md`

### Additional Guidelines
- `self_documenting.md`
- `self_documenting_template.md`
- `python_jupyter_notebooks.md`
- `python_testing.md`

## Project Structure

```
bitranox_template_py_cli/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD workflows
├── .devcontainer/              # Dev container configuration
├── docs/                       # Project documentation
│   └── systemdesign/           # System design documents
├── notebooks/                  # Jupyter notebooks for experiments
├── scripts/                    # Build and automation scripts
│   ├── build.py               # Build wheel/sdist
│   ├── bump*.py               # Version bump scripts
│   ├── clean.py               # Clean build artifacts
│   ├── test.py                # Run tests with coverage
│   ├── push.py                # Git push with monitoring
│   ├── release.py             # Create releases
│   ├── menu.py                # Interactive TUI menu
│   └── _utils.py              # Shared utilities
├── src/
│   └── bitranox_template_py_cli/  # Main Python package
│       ├── __init__.py        # Package initialization (public API exports)
│       ├── __init__conf__.py  # Static metadata constants
│       ├── __main__.py        # Module entry point
│       ├── py.typed           # PEP 561 marker
│       ├── domain/            # Layer 1: Pure domain logic
│       │   ├── __init__.py
│       │   ├── greeting.py    # Greeting domain (pure, no I/O)
│       │   └── errors.py      # Domain errors
│       ├── application/       # Layer 2: Use cases and ports
│       │   ├── __init__.py
│       │   ├── ports/         # Protocol interfaces
│       │   │   ├── __init__.py
│       │   │   └── output.py  # OutputPort Protocol
│       │   └── use_cases/     # Application use cases
│       │       ├── __init__.py
│       │       ├── greeting.py
│       │       ├── failure.py
│       │       └── info.py
│       ├── adapters/          # Layer 3: Framework implementations
│       │   ├── __init__.py
│       │   ├── output/        # Output adapters
│       │   │   ├── __init__.py
│       │   │   └── stdout.py  # StdoutAdapter
│       │   └── cli/           # CLI transport
│       │       ├── __init__.py
│       │       ├── constants.py
│       │       ├── traceback.py
│       │       ├── context.py
│       │       ├── root.py
│       │       ├── main.py
│       │       └── commands/
│       │           ├── __init__.py
│       │           └── info.py
│       └── composition/       # Layer 4: Dependency wiring
│           ├── __init__.py
│           └── container.py   # Factory functions
├── tests/                     # Test suite
├── .env.example               # Example environment variables
├── CLAUDE.md                  # Claude Code guidelines (this file)
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
├── DEVELOPMENT.md             # Development setup guide
├── INSTALL.md                 # Installation instructions
├── Makefile                   # Make targets for common tasks
├── pyproject.toml             # Project metadata & dependencies
├── codecov.yml                # Codecov configuration
└── README.md                  # Project overview
```

## Versioning & Releases

- **Single Source of Truth**: Package version is in `pyproject.toml` (`[project].version`)
- **Version Bumps**: update `pyproject.toml` , `CHANGELOG.md` and update the constants in `src/../__init__conf__.py` according to `pyproject.toml`
    - Automation rewrites `src/bitranox_template_py_cli/__init__conf__.py` from `pyproject.toml`, so runtime code imports generated constants instead of querying `importlib.metadata`.
    - After updating project metadata (version, summary, URLs, authors) run `make test` (or `python -m scripts.test`) to regenerate the metadata module before committing.
- **Release Tags**: Format is `vX.Y.Z` (push tags for CI to build and publish)

## Common Make Targets

| Target            | Description                                                                     |
|-------------------|---------------------------------------------------------------------------------|
| `build`           | Build wheel/sdist artifacts                                                     |
| `bump`            | Bump version (VERSION=X.Y.Z or PART=major\|minor\|patch) and update changelog  |
| `bump-major`      | Increment major version ((X+1).0.0)                                            |
| `bump-minor`      | Increment minor version (X.Y.Z → X.(Y+1).0)                                    |
| `bump-patch`      | Increment patch version (X.Y.Z → X.Y.(Z+1))                                    |
| `clean`           | Remove caches, coverage, and build artifacts (includes `dist/` and `build/`)   |
| `dev`             | Install package with dev extras                                                |
| `help`            | Show make targets                                                              |
| `install`         | Editable install                                                               |
| `menu`            | Interactive TUI menu                                                           |
| `push`            | Commit changes and push to GitHub (no CI monitoring)                           |
| `release`         | Tag vX.Y.Z, push, sync packaging, run gh release if available                  |
| `run`             | Run module entry (`python -m ... --help`)                                      |
| `test`            | Lint, format, type-check, run tests with coverage, upload to Codecov           |
| `test-slow`       | Run integration tests only (marked with `@pytest.mark.integration`, not in CI) |
| `version-current` | Print current version from `pyproject.toml`                                    |

## Coding Style & Naming Conventions

Follow the guidelines in `python_clean_code.md` for all Python code.

## Architecture Overview

This project follows **Clean Architecture** with four layers:

### Layer 1: Domain (`domain/`)
Pure business logic with no I/O, no logging, no framework dependencies.
- `greeting.py`: Pure greeting logic (returns string, no side effects)
- `errors.py`: Domain-specific exceptions (`IntentionalFailure`)

### Layer 2: Application (`application/`)
Use cases and ports (Protocol interfaces).
- `ports/output.py`: `OutputPort` Protocol for text output
- `use_cases/greeting.py`: `GreetingUseCase` - emits greeting via output port
- `use_cases/failure.py`: `FailureUseCase` - raises domain error
- `use_cases/info.py`: `InfoUseCase` - outputs metadata

### Layer 3: Adapters (`adapters/`)
Framework implementations of ports.
- `output/stdout.py`: `StdoutAdapter` implements `OutputPort`
- `cli/`: CLI transport using rich-click

### Layer 4: Composition (`composition/`)
Dependency wiring that creates use cases with their adapters.
- `container.py`: Factory functions (`create_greeting_use_case()`, etc.)

### Import Rules
- **Dependencies point inward**: Adapters → Application → Domain
- **Domain is pure**: No imports from outer layers
- **Enforced by import-linter**: See `pyproject.toml` contracts

Apply principles from `python_clean_architecture.md` when designing and implementing features.

## Security & Configuration

### Secrets Management
- `.env` files are for local tooling only (CodeCov tokens, etc.)
- **NEVER** commit secrets to version control
- Store production tokens in GitHub Secrets, not in repository files
- Use `.env.example` as a template (safe to commit)

### Security Review Status
Last reviewed: 2026-01-15

| Category | Status |
|----------|--------|
| Path Traversal | ✅ None found |
| Command Injection | ✅ Mitigated (scripts only) |
| Input Validation | ✅ Click + Pydantic |
| Race Conditions | ✅ None (no threading) |
| Unsafe Deserialization | ✅ None |

### Known Limitations
- `scripts/_utils.py`: Uses `shell=True` for string commands (internal use only, not exposed to user input)

## Performance

### lru_cache Analysis
Last reviewed: 2026-01-15

**No caching optimizations needed.** Analysis found:
- No expensive pure functions (domain functions return constants)
- No repeated computations in hot paths
- Single invocation pattern (once per CLI command)
- Clean architecture requires fresh instances (caching conflicts with DI)

This is expected for a CLI tool focused on I/O rather than computation.

## Commit & Push Policy

- **Always run `make test` before pushing** to avoid lint/test breakage
- Ensure all tests pass and code is properly formatted
- Monitor GitHub Actions after pushing
- **NEVER add Claude as co-author in commits** - no `Co-Authored-By` lines
