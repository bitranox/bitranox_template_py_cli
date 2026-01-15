# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.

## [2.0.0] - 2026-01-15

### Added
- **Integration test infrastructure** - `make test-slow` target for slow tests:
  - Added `integration` pytest marker for tests requiring external resources
  - Added `test-slow` Make target and menu entry
  - Integration tests do NOT run in GitHub Actions CI
  - No integration tests exist yet - infrastructure prepared for future use

### Changed
- **Full Clean Architecture Refactoring** - Implemented 4-layer architecture:
  - **Domain Layer** (`domain/`): Pure business logic, no I/O
    - `greeting.py` - Pure greeting function returning string
    - `errors.py` - Domain-specific `IntentionalFailure` exception
  - **Application Layer** (`application/`): Use cases and ports
    - `ports/output.py` - `OutputPort` Protocol interface
    - `use_cases/greeting.py` - `GreetingUseCase`
    - `use_cases/failure.py` - `FailureUseCase`
    - `use_cases/info.py` - `InfoUseCase`
  - **Adapters Layer** (`adapters/`): Framework implementations
    - `output/stdout.py` - `StdoutAdapter` implementing `OutputPort`
    - `cli/` - CLI transport using rich-click (moved from root)
  - **Composition Layer** (`composition/`): Dependency wiring
    - `container.py` - Factory functions for creating wired use cases
- Updated import-linter contracts to enforce clean architecture layers
- Updated tests to test all architecture layers
- **Type hints modernized** - Using Python 3.10+ union syntax (`X | None`) and
  built-in generics (`tuple[...]`) instead of `typing` module equivalents

### Removed
- Deleted `behaviors.py` (replaced by domain + application layers)
- Deleted root `cli/` directory (moved to `adapters/cli/`)
- **Backward compatibility wrappers** - Removed `emit_greeting()`,
  `raise_intentional_failure()`, `noop_main()` from package exports (use
  composition layer directly via `container` module)
- **Backward compatibility constant** - Removed `DEFAULT_PATTERNS` from
  `scripts/clean.py` (use `get_clean_patterns()` directly)
- **Future import** - Removed unnecessary `from __future__ import annotations`
  from all source files (Python 3.10+ native syntax supported)

### Security
- Completed security review: no vulnerabilities found in production code
- Verified: no path traversal, command injection, or unsafe deserialization
- Edge case handling validated: None values, missing attributes, stream errors
- **Scripts hardening** (development tools only, not distributed):
  - Replaced `bash -lc` patterns with direct subprocess calls (command injection prevention)
  - Added random suffix to temp file names (TOCTOU attack prevention)
  - Added path traversal validation to `clean.py` glob patterns
  - Enhanced semver validation with bounds checking

### Performance
- Added `@lru_cache` memoization to development automation scripts:
  - `load_pyproject_config()` - 6000x+ speedup on repeated calls
  - `_normalize_slug()` - 200x+ speedup on repeated calls
  - `cmd_exists()` - 1200x+ speedup on repeated calls
  - `_parse_version_constraint()` - 1200x+ speedup on repeated calls
  - `_normalize_name()` - cached for repeated dependency normalizations
- Refactored manual dict-based caching to standard `@lru_cache` decorator in
  `_load_pyproject()` and `get_project_metadata()`
- Note: Main package (src/) unchanged - CLI tool is I/O-focused with single-invocation patterns

## [1.9.2] - 2025-12-15

### Changed
- Replaced `tomli`/`tomllib` with `rtoml` for TOML parsing across tests and CI
- Removed conditional `tomli` dependency (was only needed for Python <3.11)
- Updated CI workflow to use `rtoml` instead of version-conditional `tomli`/`tomllib`

## [1.9.1] - 2025-12-15

### Changed
- Bumped `lib_cli_exit_tools` dependency from 2.2.1 to 2.2.2
- Bumped `ruff` dev dependency from 0.14.8 to 0.14.9
- Bumped `textual` dev dependency from 6.8.0 to 6.9.0
- Added `rtoml>=0.13.0` dev dependency for TOML parsing
- Updated GitHub Actions `actions/cache` from v4 to v5 in CI workflow
- Updated GitHub Actions `actions/upload-artifact` from v5 to v6 in release workflow
- Reformatted docstrings in `__init__conf__.py` to follow consistent structure

## [1.9.0] - 2025-12-11

### Changed
- Broadened Python compatibility from 3.13+ to 3.10+
- Updated `target-version` in ruff configuration from `py313` to `py310`
- Updated documentation to reflect Python 3.10+ support

## [1.8.1] - 2025-12-08

### Changed
- Bumped `lib_cli_exit_tools` dependency from 2.1.0 to 2.1.1
- Bumped `import-linter` dev dependency from 2.7 to 2.8

### Fixed
- Added `PYTHONIOENCODING=utf-8` to CI workflow to prevent encoding issues

## [1.8.0] - 2025-12-07

### Changed
- Enforced strict data architecture rules across all source and test files:
  - Replaced raw dict usage in Click context with typed `CLIContextData` dataclass
  - Added `ClickContextSettings` dataclass for Click context configuration
  - Converted `TypedDict` to `@dataclass` in test fixtures for type safety
- Refactored test suite to clean architecture principles:
  - `conftest.py`: Centralized fixtures with immutable `CLIConfigSnapshot` dataclass
  - `test_behaviors.py`: 10 focused tests for core behaviors
  - `test_cli.py`: 29 tests using real CLI execution via `CliRunner`
  - `test_metadata.py`: 20 tests validating pyproject.toml synchronization
  - `test_module_entry.py`: 14 tests for module entry point via `runpy`
- All 79 tests now marked with `@pytest.mark.os_agnostic` for cross-platform clarity
- Increased test coverage to 94.51% (88 tests including doctests)

### Fixed
- Eliminated all raw dict parameter violations in production code
- Removed dict key access patterns (`ctx.obj["key"]`) in favour of typed field
  access (`context_data.field`)
- Fixed pyright type errors in test files with proper type annotations

### Documentation
- Clarified `--no-traceback` as the default error display mode in README
- Added Traceback Mode section explaining `--traceback` vs `--no-traceback` usage

## [1.7.0] - 2025-10-13
### Added
- Static metadata portrait generated from ``pyproject.toml`` and exported via
  ``bitranox_template_py_cli.__init__conf__``; automation keeps the constants in
  sync during tests and push workflows.
- Help-first CLI experience: invoking the command without subcommands now
  prints the rich-click help screen; ``--traceback`` without subcommands still
  executes the placeholder domain entry.
- `ProjectMetadata` now captures version, summary, author, and console-script
  name, providing richer diagnostics for automation scripts.

### Changed
- Refactored CLI helpers into prose-like functions with explicit docstrings for
  intent, inputs, outputs, and side effects.
- Overhauled module headers and system design docs to align with the clean
  narrative style; `docs/systemdesign/module_reference.md` reflects every helper.
- Scripts (`test`, `push`) synchronise metadata before running, ensuring the
  portrait stays current without runtime lookups.

### Fixed
- Eliminated runtime dependency on ``importlib.metadata`` by generating the
  metadata file ahead of time, removing a failure point in minimal installs.
- Hardened tests around CLI help output, metadata constants, and automation
  scripts to keep coverage exhaustive.

## [1.6.0] - 2025-10-10

### Added
- Type-hardened CLI, module-entry, and behaviour tests covering metadata output
  and invalid command handling.
- Import-linter contract aligning the CLI with the behaviour module structure.

### Changed
- Removed stale packaging references (Conda/Homebrew/Nix) from documentation and
  environment templates.
- Updated contributor and development guides to reflect the streamlined build
  workflow.
- Removed all legacy compatibility shims; only the canonical behaviour helpers
  remain exported.

### Fixed
- Eliminated tracked coverage artifacts and unused dev-only dependencies.

## [0.0.1] - 2025-09-25
- Bootstrap `bitranox_template_py_cli` using the shared scaffold.
- Replace implementation-specific modules with placeholders ready for Rich-based logging.
