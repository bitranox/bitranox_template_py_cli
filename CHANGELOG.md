# Changelog

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
