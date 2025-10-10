# Changelog

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
