# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.


## [Unreleased]

### Fixed
- **`build_testing()` can run a command.** The in-memory logging initializer was a no-op while every
  command binds job context onto the lib_log_rich runtime, so any command under the testing
  composition raised `RuntimeError('lib_log_rich.init() must be called before using the logging
  API')`. It now starts a quiet runtime (no journald, event log, Graylog or queue; console at ERROR;
  no `.env` loading).
- **Tests no longer pass or fail by order.** An autouse fixture shuts the lib_log_rich runtime down
  and restores the root logger's handlers, level and propagate flag after every test; production
  `init_logging` attaches a stdlib handler and raises the root level, which `runtime.shutdown()`
  does not undo.
- **No more `SystemExit: N` on stderr.** The email and config commands raised a bare `SystemExit`,
  which `main()`'s catch-all branch printed as `SystemExit: 78` after the real error message. They
  now exit through click's context (`ctx.exit`), and `main()` returns the exit code rich_click's
  `main()` hands back instead of discarding it and returning 0. `typed_click` gains a typed
  `get_current_context` wrapper for the helpers that have no `ctx` parameter.
- **A failed send is reported once.** click's `Exit` subclasses `RuntimeError`, so the send-result
  exit raised inside the delivery `try` was caught again by the `DeliveryError`/`RuntimeError`
  branch, adding "SMTP delivery failed" / "Failed to send email" to the correct "sending failed".
  The send result is handled in the `try`'s `else`, and `config-deploy` re-raises an `Exit` before
  its catch-all.
- **A non-UTF-8 path no longer crashes output, and the console fallback degrades only what it
  must.** `safe_console.encode_safe` skipped its check for utf-8/16/32, but a lone surrogate (a
  filesystem byte decoded with `surrogateescape`) encodes in none of them, so
  `config-generate-examples` into such a directory wrote its files and then exited 1 on the path
  echo. Once any character failed, the fallback also rewrote every known glyph in the text,
  including ones the stream could print. The fallback is now a registered codec error handler: the
  codec calls it for exactly the characters it rejects, which become their ASCII form or `?`.

- **A broken configuration file no longer disables every command.** The root group loaded the
  configuration before any subcommand option was parsed and let a load error escape, so a
  malformed `config.toml` made every command, `--help` and `config-deploy` (the command that
  replaces the file) exit 1 with empty stdout. The root now records the failure
  (`adapters/cli/config_load.py`); `config`, `send-email` and `send-notification` refuse with exit
  78 and one line naming it, while `config-deploy` (with a warning), `config-generate-examples`,
  `info`, `hello` and help still run. An invalid profile and an unreadable file take the same path.
  `config --profile X` reloads with the root's `--env-file` instead of searching for another `.env`.
- **`[lib_layered_config.default_permissions]` now takes effect.** The per-layer modes were read,
  but only `enabled` was ever used: `get_modes_for_target` had no production caller, so
  `--set lib_layered_config.default_permissions.user_directory=488` still produced a `0o700`
  directory. `config-deploy` now deploys each target with its configured directory and file mode
  (CLI `--dir-mode`/`--file-mode` still win). The section is validated through the
  `PermissionDefaults` pydantic model: a malformed or out-of-range mode, a bare integer, an
  unsafe mode, a non-boolean `enabled`, a section that is not a table or an unknown key stops the
  command with exit 78 and one line naming the key, where it used to fall back to the default,
  crash with `AttributeError`, or print pydantic's multi-line error.

### Changed
- **`click` is a declared dependency.** The package imports it directly (`adapters/cli/main.py`,
  `commands/config.py`) but only had it through rich-click. `permissions.py` no longer imports
  `pydantic_core`, which was never declared either; its validators raise `ValueError`. A new test
  fails when a runtime import is missing from `[project].dependencies`.

### Removed
- `adapters.config.permissions.parse_mode`, whose silent fall-back to the default is what the
  model validation above replaces.

### Security
- **`config-deploy` refuses unsafe and malformed modes.** `--dir-mode -1` passed the unbounded
  octal parser and chmodded the config directory to `0o7777` (setuid, sticky, world-writable); a
  20-digit value raised `OverflowError`. `--dir-mode`/`--file-mode` now accept only a plain octal
  literal in `0`..`0o7777`, and refuse the setuid/setgid/sticky bits, world write, a directory
  without owner `rwx` and a file without owner `rw`, naming each offending bit (exit 2, nothing
  written).
- **The SMTP password no longer prints.** `EmailConfig.smtp_password` was a plain `str`: the
  custom `__repr__` hid it, but `str()`, `format()` and `model_dump()`/`model_dump_json()` printed it.
  It is now a pydantic `SecretStr`, unwrapped only where the SMTP login receives it.
- **No group-writable or executable configuration, and no decimal integer read as a mode.** A
  configured mode given as a bare integer was read as DECIMAL (TOML `user_file = 444`, `--set`, or
  the environment value `444`), and several such values passed the safety rule: `444` deployed
  `config.toml`, the file holding the SMTP password, at `0o674`, and `400` meant as owner-read-only
  became `0o620`. A bare integer is now refused with a hint to write an octal string (`"0o640"`),
  and every mode, from the CLI or the configuration, is also refused when it grants group write
  (on macOS every local account shares the group `staff`) or, for a file, sets any execute bit.
  `--dir-mode 770` and `--file-mode 660`, accepted before, are refused. Migration: quote configured
  modes (`user_file = "640"`), and use the `0o` prefix in environment variables and `--set`.

## [1.7.2] 2026-09-12 02:11:47

### Fixed
- **`--set` overrides now report the CLI as their source.** `Config.with_overrides` returns the
  merged data with the ORIGINAL provenance map by design, so an overridden key kept naming the
  file it replaced and `config` sent a reader to a file holding the old value. The override path
  rebuilds provenance, naming layer `cli` with no path for exactly the keys `--set` supplied and
  leaving every other key's source alone.

## [1.7.1] 2026-08-01 01:02:45

Re-release of 1.7.0, which was tagged but never published: PyPI rejected the upload because
that filename had been used by a file that has since been deleted, and PyPI never permits
filename reuse. Package contents are identical to 1.7.0.

## [1.7.0] 2026-08-01 00:45:53 [NOT PUBLISHED]

### Added
- **`adapters/cli/safe_console.py`, an encode-safe replacement for `click.echo`.** A Windows console at
  codepage 1252 gives Python an `errors="strict"` stream, so writing a check mark raises
  `UnicodeEncodeError: 'charmap' codec can't encode character '✓'` and the command exits 1 *after*
  its work has already succeeded. Click does not protect against this, and Rich raises the same way
  through its own writer. `safe_console.echo` degrades at the sink, so a UTF-8 terminal and every email
  body still receive the character and only a stream that cannot encode it sees `[OK]` / `[X]` /
  `[!]`; `safe_console.safe_stream` wraps a writer handed to Rich.

  The template itself never emitted such a character, but nine repos derived from it have since
  drifted into doing so, which is why the protection and its guard now ship from here.

### Changed
- All 21 `click.echo` call sites route through `safe_console.echo`. `tests/test_safe_console.py` asserts that
  no module calls `click.echo` or builds an unwrapped `Console(file=sys.stdout)` again, so a project
  scaffolded from this template keeps the property by construction.

## [1.6.2] 2026-07-24 12:00:55

### Fixed
- CI (scheduled runs install the latest ruff) went red on `PLR0917` (too many positional arguments) for the four CLI command callbacks. Their option parameters are now keyword-only, which matches how Click actually invokes them (`f(ctx, **ctx.params)`) and drops the positional-argument count without suppressing the rule.

### Changed
- Removed the blanket `[tool.ruff.lint].ignore` list and fixed each cause at the root instead of silencing it: `RUF002` (en-dash to ASCII hyphen), `RUF022` (sorted `__all__`), `TC001`/`TC002`/`TC003` (typing-only imports moved into `TYPE_CHECKING`), and `TC006` (quoted `cast()` type expressions).
- Added `[tool.ruff.lint.flake8-type-checking] runtime-evaluated-base-classes = ["pydantic.BaseModel"]` so the Pydantic models keep their field-type imports at runtime while the type-checking rules still apply everywhere else.
- Genuinely deferred imports (the root/commands circular-import break, lazy heavy imports) now carry a narrow, documented `# noqa: PLC0415`; unjustified deferred imports were moved to module top. Deferred imports inside tests remain a deliberate idiom and are scoped-ignored.

## [1.6.1] - 2026-07-20

Re-release of 1.6.0. PyPI rejected the 1.6.0 upload because that filename was previously used by a file that has since been deleted, and PyPI never permits filename reuse. Package contents are identical to 1.6.0.

### Added
- `send_email()` and `send_notification()` accept an optional `transport` argument, exposing btx_lib_mail's `Transport` port so a delivery double can be injected at a real seam instead of monkeypatching `smtplib`.

### Fixed
- Mail tests failed against btx_lib_mail 1.5.0, which streams the message over the wire protocol directly (MAIL/RCPT plus DATA or BDAT) instead of calling `smtp.sendmail()`. The suite now injects a recording transport and asserts delivery intent (envelope sender, recipients, host failover order, credentials, payload), so it no longer depends on the library's internals.
- `ConfMail.smtp_password` is a `SecretStr` as of btx_lib_mail 1.5.0 and is now unwrapped before comparison.
- `config-deploy` emits an ASCII marker so it cannot crash on a cp1252 Windows console.
- `validate_profile` normalised to raise `ValueError`.
- DEVELOPMENT.md referenced a `make test-slow` target that no longer exists (4 places); the target is `make testintegration`. It also documented the SMTP username environment variable as `EMAIL__SMTP_USER`, but the field is `smtp_username`, so the correct name is `EMAIL__SMTP_USERNAME`.

### Documentation
- DEVELOPMENT.md documents the SMTP test seam: inject a `transport` double instead of patching `smtplib`, and leave `transport` off the application ports.

### Changed
- Raised the `btx_lib_mail` floor to `>=1.5.0`, which the injected transport seam requires. Other dependency floors refreshed and the current bmk Makefile adopted.
- CI: configurable pytest marker exclusion, pip-audit scoped to the project dependency tree with direct-URL dependencies filtered out, `actions/checkout` v7 and `actions/cache` v6.
- `codecov-cli` disabled (it capped `click<8.3.0` and held click on CVE-2026-7246); the redundant PYSEC-2026-2132 ignore dropped.
- LF line endings pinned via `.gitattributes`; file modes normalised so the executable bit is set only on shebang scripts.
- Quickstart notebook installs the package with uv.

## [1.6.0] - 2026-07-20 [NOT PUBLISHED]

Tagged and released on GitHub, but never published to PyPI: the upload was rejected because the `1.6.0` filename had been used by a previously deleted file. Superseded by 1.6.1, which carries the same changes.

## [1.5.4] 2026-06-14

### Changed
- Added a `typed_click.py` facade wrapping rich-click's `option` / `version_option` decorators behind explicit, fully-known signatures, keeping the CLI strict-clean under pyright 1.1.410 (`reportUnknownMemberType`) without disabling the rule (ignore isolated to the facade).
- Bumped internal dependency floors: `lib_cli_exit_tools>=2.3.2`, `lib_log_rich>=6.3.5`, `lib_layered_config>=5.5.2`, `btx_lib_mail>=1.3.2`.

## [1.5.3] - 2026-03-30

### Changed
- Bumped Codecov GitHub Action to V6
- Updated CVE exclusion list: removed stale entries, added inline documentation for remaining exclusions
- pip-audit set to warning-only to reduce CI noise

### Fixed
- Email transport: minor improvements to SMTP handling

## [1.5.2] - 2026-03-05

### Fixed
- Re-release as 1.5.2: PyPI rejected 1.5.1 due to filename reuse after prior upload deletion

### Changed
- `get_permission_defaults()` now returns a `PermissionDefaults` Pydantic model instead of a raw dict, with typed field access and `dir_mode_for()`/`file_mode_for()` methods
- `EmailSpy` now stores captured calls as `CapturedEmail` and `CapturedNotification` frozen dataclasses instead of `list[dict[str, Any]]`

### Added
- Tests for `--env-file` CLI option (argument passing, validation, end-to-end integration)

## [1.5.1] - 2026-03-05 [YANKED]

### Changed
- `get_permission_defaults()` now returns a `PermissionDefaults` Pydantic model instead of a raw dict, with typed field access and `dir_mode_for()`/`file_mode_for()` methods
- `EmailSpy` now stores captured calls as `CapturedEmail` and `CapturedNotification` frozen dataclasses instead of `list[dict[str, Any]]`

### Added
- Tests for `--env-file` CLI option (argument passing, validation, end-to-end integration)

## [1.5.0] - 2026-03-02

### Added
- `--env-file PATH` global CLI option to load an explicit `.env` file instead of searching upward from the working directory
- `dotenv_path` parameter added to `GetConfig` protocol, config loader, and in-memory adapter
- `__all__` to `__init__conf__.py` listing all public symbols
- `@pytest.mark.integration` marker on email integration tests

### Fixed
- Subprocess tests (`test_module_entry_subprocess_help`, `test_module_entry_subprocess_version`) now pass without editable install by setting `PYTHONPATH` to `src/`
- pip-audit CVE-2025-8869 ignore (pip is environment-level, not a project dependency)

### Changed
- CI workflow: dynamic Python version matrix extracted from `pyproject.toml` classifiers
- CI workflow: ruff cache restricted to GitHub-hosted runners
- CI workflow: bandit reads configuration from `pyproject.toml` (`-c pyproject.toml`)
- CI workflow: Codecov upload uses dynamically resolved latest Python version
- Release workflow: `actions/upload-artifact` upgraded to v7
- Added `[tool.hatch.metadata]` and `[tool.bashate]` sections to `pyproject.toml`
- Documentation updates: CONFIG.md, README.md, DEVELOPMENT.md for `--env-file` option

## [1.4.1] - 2026-02-13

### Fixed
- `reset_git_history.sh`: fixed shellcheck SC1083 warning by quoting `HEAD^{tree}` and normalized indentation to 4 spaces (shfmt)

### Changed
- Updated Makefile from v2.2.1 to v2.3.3
- Bumped dependency minimums: `lib_cli_exit_tools` >=2.3.0, `lib_log_rich` >=6.3.3, `lib_layered_config` >=5.4.1
- Added CVE ignore entries for CVE-2026-26007 and CVE-2026-25990
- Updated CI/CD workflows and added Bash 4+ requirement for macOS

## [1.4.0] - 2026-02-13

### Changed
- **Build automation**: replaced `scripts/` directory with `bmk`-based Makefile (`uvx bmk@latest`); all build, test, bump, push, and release tasks now delegated to `bmk`
- Makefile updated to v2.2.1 with alias targets, trailing argument forwarding, and new commands (config, email, info, logdemo)

## [1.3.1] - 2026-02-13

### Fixed
- `tests/test_metadata_sync.py`: replaced `importlib.metadata` lookups with direct `pyproject.toml` reads - tests no longer fail when the package is not installed in the test environment (uvx)
- Makefile `dev` target now correctly installs dev extras (`uv pip install -e ".[dev]"`)

### Changed
- CLAUDE.md: updated project structure trees to reflect actual codebase (added `entry.py`, `domain/errors.py`, `adapters/memory/`, `adapters/config/permissions.py`, `adapters/email/validation.py`; removed deleted `traceback.py`)
- CLAUDE.md: rewrote Make targets table to match new `bmk`-based Makefile (added aliases, new targets; removed obsolete `menu`, `test-slow`)
- CLAUDE.md: corrected versioning documentation - runtime metadata is served from `__init__conf__.py` constants, not `importlib.metadata`
- CLAUDE.md: replaced stale `scripts/` instrumentation section with `bmk` delegation note
- CLAUDE.md: updated `make test-slow` references to `make testintegration`

## [1.3.0] - 2026-02-01

### Added
- **File permission options for `config-deploy`**: `--permissions/--no-permissions`, `--dir-mode`, `--file-mode`
- **Configurable permission defaults** in `[lib_layered_config.default_permissions]` (app/host: 755/644, user: 700/600)
- **Octal string support** in config files (`"0o755"`, `"755"`, or decimal `493`)

### Changed
- `deploy_configuration()` accepts `set_permissions`, `dir_mode`, `file_mode` parameters
- CONFIG.md: comprehensive CLI options reference, `sudo -u` deployment examples

## [1.2.1] - 2026-02-01

### Changed
- **Profile validation** now delegates to `lib_layered_config.validate_profile_name()` with comprehensive security checks:
  - Maximum length enforcement (64 characters)
  - Empty string rejection
  - Windows reserved name rejection (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
  - Leading character validation (must start with alphanumeric)
  - Path traversal prevention (/, \, ..)
- `validate_profile()` now accepts optional `max_length` parameter for customization

### Added
- `40-layered-config.toml` in `defaultconfig.d/` documenting lib_layered_config integration settings
- Profile validation tests for length limits, empty strings, Windows reserved names, and leading character rules
- Profile name requirements documentation in CONFIG.md and README.md

### Removed
- Custom `_PROFILE_PATTERN` regex - replaced by lib_layered_config's built-in validation

## [1.2.0] - 2026-01-30

### Added
- **Attachment security settings** for email configuration (`[email.attachments]` section in `50-mail.toml`)
  - `allowed_extensions` / `blocked_extensions` - whitelist/blacklist file extensions
  - `allowed_directories` / `blocked_directories` - whitelist/blacklist attachment source directories
  - `max_size_bytes` - maximum attachment file size (default 25 MiB, 0 to disable)
  - `allow_symlinks` - whether symbolic links are permitted (default false)
  - `raise_on_security_violation` - raise or skip on violations (default true)
- New `EmailConfig` fields for attachment security with Pydantic validators
- `load_email_config_from_dict()` now flattens nested `[email.attachments]` section

### Changed
- Bumped `btx_lib_mail` dependency from `>=1.2.1` to `>=1.3.0` for attachment security features

## [1.1.2] - 2026-01-28

### Fixed
- Coverage SQLite "database is locked" errors on Python 3.14 free-threaded builds and network mounts (SMB/NFS)
- Removed bogus `COVERAGE_NO_SQL=1` environment variable from `scripts/test.py` (not a real coverage.py setting)
- CI workflow now sets `COVERAGE_FILE` to `runner.temp` so coverage always writes to local disk
- **Import-linter was a silent no-op** in `make test` / `make push` - `python -m importlinter.cli lint` silently exits 0 without checking; replaced with `lint-imports` (the working console entry point)
- CI/local parameter mismatches: ruff now targets `.` (not hardcoded `src tests notebooks`), pytest uses `python -m pytest` with `--cov=src/$PACKAGE_MODULE`, `--cov-fail-under=90`, and `-vv` matching local runs
- `scripts/test.py` bandit source path now reads `src-path` from `[tool.scripts.test]` instead of hardcoding `Path("src")`
- `scripts/test.py` module-level `_default_env` now rebuilt with configured `src_path` before running checks
- `run_slow_tests()` now reads pytest verbosity from `[tool.scripts.test].pytest-verbosity` instead of hardcoding `"-vv"`

### Changed
- **pyproject.toml as single source of truth**: CI workflow extracts all tool configuration (src-path, pytest-verbosity, coverage-report-file, fail_under, bandit skips) from `pyproject.toml` via metadata step - workflow is portable across projects without editing
- `scripts/test.py` removed module-level `PACKAGE_SRC` constant; bandit source path computed from `config.src_path` inside the functions that need it
- `make push` now accepts an unquoted message as trailing words (e.g. `make push fix typo in readme`); commit message format is `<version> - <message>`, defaulting to `<version> - chores` when no message is given
- Removed interactive commit-message prompt from `push.py` - message is either provided via CLI args / `COMMIT_MESSAGE` env var, or defaults to `"chores"`

### Added
- `pytest_configure` hook in `tests/conftest.py` that redirects coverage data to `tempfile.gettempdir()` and purges stale SQLite journal files before each run

## [1.1.1] - 2026-01-28

### Fixed
- CLAUDE.md: replaced stale package name `bitranox_template_cli_app_config_log_mail` with `bitranox_template_py_cli` throughout
- Brittle SMTP mock assertions in `test_cli.py` now use structured `call_args` attributes instead of `str()` coercion
- Stale docstring in `__init__conf__.py` claiming "adapters/platform layer" - corrected to "Package-level metadata module"
- Weak OR assertion in `test_cli.py` for SMTP host display - replaced with two independent assertions
- Removed stale `# type: ignore[reportUnknownVariableType]` from `sender.py` (`btx_lib_mail.ConfMail` now has proper type annotations)
- Late function-body imports in `adapters/cli/commands/config.py` moved to module-level for consistency

### Removed
- Dead code: unused `_format_value()` and `_format_source()` wrappers in `adapters/config/display.py`

### Added
- `__all__` to `__init__conf__.py` listing all public symbols
- `tests/test_enums.py` with parametrized tests for `OutputFormat` and `DeployTarget`
- Expanded `tests/test_behaviors.py` with return type, constant value, and constant-usage checks
- Python 3.14 classifier in `pyproject.toml`
- Codecov upload step in CI workflow (gated to `ubuntu-latest` + `3.13`)
- Edge-case tests for `parse_override`: bare `=value`, bare `=`, and CLI `--set ""` empty string
- Duplication-tracking comments for CI metadata extraction scripts

### Changed
- `tests/test_display.py` rewritten to test `_format_raw_value` and `_format_source_line` directly (replacing dead wrapper tests)

## [1.1.0] - 2026-01-27

### Changed
- Replaced `MockConfig` in-memory adapter with real `Config` objects in all tests (`config_factory` / `inject_config` fixtures)
- Replaced `MagicMock` Config objects in CLI email tests with real `Config` instances
- Unified test names to BDD-style `test_when_<condition>_<behavior>` pattern in `test_cli.py`
- Email integration tests now load configuration via `lib_layered_config` instead of dedicated `TEST_SMTP_SERVER` / `TEST_EMAIL_ADDRESS` environment variables

### Added
- Cache effectiveness tests for `get_config()` and `get_default_config_path()` LRU caches (`tests/test_cache_effectiveness.py`)
- Callable Protocol definitions in `application/ports.py` for all adapter functions, with static conformance assertions and `tests/test_ports.py`
- `ExitCode` IntEnum (`adapters/cli/exit_codes.py`) with POSIX-conventional exit codes for all CLI error paths
- `logdemo` and `config-generate-examples` CLI commands
- `--set SECTION.KEY=VALUE` repeatable CLI option for runtime configuration overrides (`adapters.config.overrides` module)
- Unit tests for config overrides and display module (sensitive key matching, redaction, nested rendering)

### Removed
- Dead code: `raise_intentional_failure()`, `noop_main()`, `cli_main()`, duplicate `cli_session` orchestration, catch-log-reraise in `send_email()`
- Replaced dead `ConfigPort`/`EmailPort` protocol classes with callable Protocol definitions

### Fixed
- POSIX-conventional exit codes across all CLI error paths (replacing hardcoded `SystemExit(1)`)
- Sensitive value redaction: word-boundary matching to avoid false positives, nested dict/list redaction, TOML sub-section rendering
- Email validation: reject bogus addresses (`@`, `user@`, `@domain`); IPv6 SMTP host support; credential construction
- Profile name validation against path traversal
- Security: list-based subprocess calls in scripts, sensitive env-var redaction in test output, stale CVE exclusion cleanup
- Documentation: wrong project name references, truncated CLI command names, stale import paths, wrong layer descriptions
- CI: `actions/download-artifact` version mismatch, stale `codecov.yml` ignore patterns
- Unified `__main__.py` and `adapters/cli/main.py` error handling via delegation

### Changed
- Precompile all regex patterns in `scripts/` as module-level constants for consistent compilation
- **LIBRARIES**: Replace custom redaction/validation with `lib_layered_config` redaction API and `btx_lib_mail` validators; bump both libraries
- **LIBRARIES**: Replace stdlib `json` with `orjson`; replace `urllib` with `httpx` in scripts
- **ARCHITECTURE**: Purified domain layer - `emit_greeting()` renamed to `build_greeting()` (returns `str`, no I/O); decoupled `display.py` from Click
- **DATA ARCHITECTURE**: Consolidated `EmailConfig` into single Pydantic `BaseModel` (eliminated dataclass conversion chain)

## [1.0.0] - 2026-01-15

### Added
- Slow integration test infrastructure (`make test-slow`, `@pytest.mark.slow` marker)
- `pydantic>=2.0.0` dependency for boundary validation
- `CLIContext` dataclass replacing untyped `ctx.obj` dict
- Pydantic models: `EmailSectionModel`, `LoggingConfigModel`
- `application/ports.py` with Protocol definitions; `composition/__init__.py` wiring layer

### Changed
- **BREAKING**: Full Clean Architecture refactoring into explicit layer directories (`domain/`, `application/`, `adapters/`, `composition/`)
- CLI restructured from monolithic `cli.py` into focused `cli/` package with single-responsibility modules
- Type hints modernized to Python 3.10+ style
- Removed backward compatibility re-exports; tests import from canonical module paths
- `import-linter` contracts enforce layer dependency direction
- `make test` excludes slow tests by default

## [0.2.5] - 2026-01-01

### Changed
- Bumped `lib_log_rich` to >=6.1.0 and `lib_layered_config` to >=5.2.0

## [0.2.4] - 2025-12-27

### Fixed
- Intermittent test failures on Windows when parsing JSON config output (switched to `result.stdout`)

## [0.2.3] - 2025-12-15

### Changed
- Lowered minimum Python version from 3.13 to 3.10; expanded CI matrix accordingly

## [0.2.2] - 2025-12-15

### Added
- Global `--profile` option for profile-specific configuration across all commands

### Changed
- **BREAKING**: Configuration loaded once in root CLI command and stored in Click context for subcommands
- Subcommand `--profile` options act as overrides that reload config when specified

## [0.2.0] - 2025-12-07

### Added
- `--profile` option for `config` and `config-deploy` commands
- `OutputFormat` and `DeployTarget` enums for type-safe CLI options
- LRU caching for `get_config()` (maxsize=4) and `get_default_config_path()`

### Fixed
- UTF-8 encoding issues in subprocess calls across different locales

## [0.1.0] - 2025-12-07

### Added
- Email sending via `btx-lib-mail` integration: `send-email` and `send-notification` CLI commands
- Email configuration support with `EmailConfig` dataclass and validation
- Real SMTP integration tests using `.env` configuration

## [0.0.1] - 2025-11-11
- Bootstrap
