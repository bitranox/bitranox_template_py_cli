# Module Reference: Architecture & Component Documentation

## Status

Complete (v1.0.0)

## Related Files

### Domain Layer
* src/bitranox_template_py_cli/domain/behaviors.py
* src/bitranox_template_py_cli/domain/enums.py

### Application Layer
* src/bitranox_template_py_cli/application/ports.py (callable Protocol definitions for adapter functions)

### Adapters Layer
* src/bitranox_template_py_cli/adapters/config/loader.py
* src/bitranox_template_py_cli/adapters/config/deploy.py
* src/bitranox_template_py_cli/adapters/config/display.py
* src/bitranox_template_py_cli/adapters/config/overrides.py
* src/bitranox_template_py_cli/adapters/email/sender.py
* src/bitranox_template_py_cli/adapters/logging/setup.py
* src/bitranox_template_py_cli/adapters/cli/ (package)
  - __init__.py (public facade)
  - constants.py (shared constants)
  - exit_codes.py (POSIX exit codes — ExitCode IntEnum)
  - traceback.py (traceback state management)
  - context.py (Click context helpers)
  - root.py (root command group)
  - main.py (entry point)
  - commands/__init__.py
  - commands/info.py (info, hello, fail)
  - commands/config.py (config, config-deploy, config-generate-examples)
  - commands/email.py (send-email, send-notification)
  - commands/logging.py (logdemo)

### Adapters Layer (In-Memory / Testing)
* src/bitranox_template_py_cli/adapters/memory/__init__.py (public facade + Protocol conformance assertions)
* src/bitranox_template_py_cli/adapters/memory/config.py (in-memory config: get, deploy, display)
* src/bitranox_template_py_cli/adapters/memory/email.py (in-memory email: send, notify, load config)
* src/bitranox_template_py_cli/adapters/memory/logging.py (in-memory logging: no-op init)

### Composition Layer
* src/bitranox_template_py_cli/composition/__init__.py

### Entry Points
* src/bitranox_template_py_cli/__main__.py
* src/bitranox_template_py_cli/__init__.py
* src/bitranox_template_py_cli/__init__conf__.py

### Deployment Templates
* src/bitranox_template_py_cli/defaultconfig.d/50-mail.toml
* src/bitranox_template_py_cli/defaultconfig.d/90-logging.toml

### Tests
* tests/test_behaviors.py
* tests/test_cache_effectiveness.py
* tests/test_cli.py
* tests/test_config_overrides.py
* tests/test_display.py
* tests/test_exit_codes.py
* tests/test_mail.py
* tests/test_metadata.py
* tests/test_module_entry.py
* tests/test_ports.py
* tests/test_scripts.py

---

## Design Purpose

This package provides a CLI application template with integrated configuration
management, structured logging, and email capabilities. It serves as a
production-ready scaffold for building CLI tools following Clean Architecture
principles with explicit layer directories.

The architecture separates concerns into domain (pure logic), application
(port definitions), adapters (infrastructure), and composition (wiring) layers,
enforced by ``import-linter`` contracts.

---

## Architecture Integration

**App Layer Fit:** This package follows Clean Architecture with explicit layer directories.

### Layer Assignments

| Directory/Module | Layer | Responsibility |
|------------------|-------|----------------|
| ``domain/behaviors.py`` | Domain | Pure domain functions (greeting) — no I/O, logging, or frameworks |
| ``domain/enums.py`` | Domain | Type-safe enums (OutputFormat, DeployTarget) |
| ``application/ports.py`` | Application | Callable Protocol definitions for adapter functions |
| ``adapters/config/loader.py`` | Adapters | Configuration loading with caching; validates profile names against path traversal |
| ``adapters/config/deploy.py`` | Adapters | Configuration deployment |
| ``adapters/config/display.py`` | Adapters | Configuration display (orjson for JSON output); redacts sensitive values via ``lib_layered_config`` redaction API; renders nested dicts as TOML sub-sections |
| ``adapters/config/overrides.py`` | Adapters | CLI ``--set`` override parsing (orjson), value coercion, and deep-merge via ``Config.with_overrides()`` |
| ``adapters/email/sender.py`` | Adapters | SMTP email with EmailConfig (Pydantic BaseModel) |
| ``adapters/logging/setup.py`` | Adapters | lib_log_rich initialization |
| ``adapters/cli/`` | Adapters | Click CLI framework integration |
| ``adapters/memory/`` | Adapters | In-memory implementations for testing (no I/O, no SMTP, no logging framework) |
| ``composition/__init__.py`` | Composition | Wires adapters to ports |
| ``__init__conf__.py`` | Entry Point | Package metadata constants |
| ``__main__.py`` | Entry Point | Thin shim delegating to ``adapters.cli.main()`` |

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Dependencies point inward only | Pass |
| Domain pure (no I/O, logs, frameworks) | Pass |
| No circular imports | Pass |
| Boundary validation (EmailConfig via Pydantic) | Pass |
| Clear layer separation | Pass |
| Explicit layer directories | Pass |

### Import Enforcement

Layer boundaries enforced via ``import-linter`` contracts in ``pyproject.toml``:
- **Domain is pure**: Domain cannot import from adapters or composition
- **Clean Architecture layers**: Validates dependency direction (composition -> adapters -> application -> domain)

Run ``lint-imports`` to verify compliance (automatically runs on ``make test``).

**Data Flow:**
1. CLI parses options with rich-click.
2. Traceback preferences are applied via ``apply_traceback_preferences``.
3. Commands delegate to behaviour helpers.
4. Exit codes and tracebacks are rendered by ``lib_cli_exit_tools``.

**System Dependencies:**
* ``rich_click`` for CLI UX
* ``lib_cli_exit_tools`` for exit-code normalisation and traceback output
* ``__init__conf__`` static constants to present package metadata

---

## Core Components

### domain.behaviors.build_greeting

* **Purpose:** Return the canonical greeting string used in smoke tests and documentation.
* **Signature:** ``build_greeting() -> str``
* **Input:** None.
* **Output:** Returns ``"Hello World"`` as a string.
* **Location:** src/bitranox_template_py_cli/domain/behaviors.py

### adapters.cli.traceback.apply_traceback_preferences

* **Purpose:** Synchronise traceback configuration between the CLI and ``python -m`` paths.
* **Signature:** ``apply_traceback_preferences(enabled: bool) -> None``
* **Parameters:**
  - ``enabled`` (``bool``) — ``True`` enables full tracebacks with colour.
* **Output:** Updates ``lib_cli_exit_tools.config.traceback`` and ``traceback_force_color``.
* **Location:** src/bitranox_template_py_cli/adapters/cli/traceback.py

### adapters.cli.traceback.snapshot_traceback_state / restore_traceback_state

* **Purpose:** Capture and restore traceback configuration state.
* **Signatures:**
  - ``snapshot_traceback_state() -> TracebackState``
  - ``restore_traceback_state(state: TracebackState) -> None``
* **Input:** None for snapshot; ``TracebackState`` dataclass for restore.
* **Output:** ``TracebackState`` dataclass (traceback_enabled, force_color) for snapshot; None for restore.
* **Location:** src/bitranox_template_py_cli/adapters/cli/traceback.py

### adapters.cli.context.store_cli_context

* **Purpose:** Store CLI state in the Click context for subcommand access.
* **Signature:** ``store_cli_context(ctx: click.Context, *, traceback: bool, config: Config, profile: str | None = None) -> None``
* **Parameters:**
  - ``ctx`` (``click.Context``) — Click context associated with the current invocation.
  - ``traceback`` (``bool``, keyword-only) — Whether verbose tracebacks were requested.
  - ``config`` (``Config``, keyword-only) — Loaded layered configuration object.
  - ``profile`` (``str | None``, keyword-only, default ``None``) — Optional configuration profile name.
* **Output:** None (sets ``context.obj`` to a ``CLIContext`` dataclass).
* **Location:** src/bitranox_template_py_cli/adapters/cli/context.py

### adapters.cli.context.get_cli_context

* **Purpose:** Retrieve typed CLI state from Click context.
* **Signature:** ``get_cli_context(ctx: click.Context) -> CLIContext``
* **Parameters:**
  - ``ctx`` (``click.Context``) — Click context containing CLI state.
* **Output:** ``CLIContext`` dataclass with typed access to CLI state.
* **Raises:** ``RuntimeError`` if CLI context was not properly initialized.
* **Location:** src/bitranox_template_py_cli/adapters/cli/context.py

### adapters.cli.exit_codes.ExitCode

* **Purpose:** POSIX-conventional exit codes for all CLI error paths.
* **Type:** ``IntEnum`` with members: SUCCESS (0), GENERAL_ERROR (1), FILE_NOT_FOUND (2), PERMISSION_DENIED (13), INVALID_ARGUMENT (22), SMTP_FAILURE (69), CONFIG_ERROR (78), TIMEOUT (110), SIGNAL_INT (130), BROKEN_PIPE (141), SIGNAL_TERM (143).
* **Usage:** CLI command error handlers raise ``SystemExit(ExitCode.XXX)`` instead of ``SystemExit(1)``.
* **Note:** Signal codes (130, 141, 143) are informational constants — ``lib_cli_exit_tools`` handles signal-to-exit-code translation automatically.
* **Location:** src/bitranox_template_py_cli/adapters/cli/exit_codes.py

### adapters.config.overrides.apply_overrides

* **Purpose:** Parse and deep-merge CLI ``--set SECTION.KEY=VALUE`` overrides into a Config instance.
* **Signature:** ``apply_overrides(config: Config, raw_overrides: tuple[str, ...]) -> Config``
* **Parameters:**
  - ``config`` (``Config``) — Original immutable Config from file/env layers.
  - ``raw_overrides`` (``tuple[str, ...]``) — Tuple of ``SECTION.KEY=VALUE`` strings from ``--set``.
* **Output:** New Config with overrides applied, or the original if ``raw_overrides`` is empty.
* **Raises:** ``ValueError`` if any override string is malformed.
* **Location:** src/bitranox_template_py_cli/adapters/config/overrides.py

### adapters.config.display.display_config

* **Purpose:** Display configuration in human-readable (TOML-like) or JSON format.
* **Signature:** ``display_config(config: Config, *, format: OutputFormat = OutputFormat.HUMAN, section: str | None = None) -> None``
* **Parameters:**
  - ``config`` (``Config``) — Already-loaded layered configuration object to display.
  - ``format`` (``OutputFormat``, keyword-only, default ``OutputFormat.HUMAN``) — Output format.
  - ``section`` (``str | None``, keyword-only, default ``None``) — Optional section filter.
* **Output:** Writes formatted configuration to stdout. Sensitive values are redacted.
* **Raises:** ``ValueError`` if a requested section doesn't exist or is empty.
* **Location:** src/bitranox_template_py_cli/adapters/config/display.py

### adapters.cli.root.cli

* **Purpose:** Root Click command group handling global options (--version, --traceback, --profile, --set).
* **Signature:** ``cli(ctx, traceback, profile, set_overrides) -> None``
* **Parameters:**
  - ``ctx`` (``click.Context``) — Click context.
  - ``traceback`` (``bool``, default ``False``) — Whether to show full tracebacks.
  - ``profile`` (``str | None``, default ``None``) — Named profile to load.
  - ``set_overrides`` (``tuple[str, ...]``, default ``()``) — Configuration override strings.
* **Output:** None (delegates to subcommands or shows help).
* **Location:** src/bitranox_template_py_cli/adapters/cli/root.py

### adapters.cli.main.main

* **Purpose:** Execute the click command group with shared exit handling.
* **Signature:** ``main(argv: Sequence[str] | None = None, *, restore_traceback: bool = True) -> int``
* **Parameters:**
  - ``argv`` (``Sequence[str] | None``, default ``None``) — Optional CLI arguments. ``None`` uses ``sys.argv``.
  - ``restore_traceback`` (``bool``, keyword-only, default ``True``) — Whether to restore prior traceback configuration after execution.
* **Output:** Integer exit code (0 on success, mapped error codes otherwise).
* **Location:** src/bitranox_template_py_cli/adapters/cli/main.py

### adapters.cli.constants

* **Purpose:** Shared CLI constants for consistent behaviour across commands.
* **Constants:**
  - ``CLICK_CONTEXT_SETTINGS`` (``dict``) — Help option names: ``["-h", "--help"]``.
  - ``TRACEBACK_SUMMARY_LIMIT`` (``int``, ``500``) — Character budget for truncated tracebacks.
  - ``TRACEBACK_VERBOSE_LIMIT`` (``int``, ``10_000``) — Character budget for verbose tracebacks.
* **Location:** src/bitranox_template_py_cli/adapters/cli/constants.py

### __main__

* **Purpose:** Thin shim providing ``python -m`` entry point; delegates to ``adapters.cli.main()``.
* **Input:** None.
* **Output:** Exit code from ``cli.main``.
* **Location:** src/bitranox_template_py_cli/__main__.py

### __init__conf__.print_info

* **Purpose:** Render the statically-defined project metadata for the CLI ``info`` command.
* **Signature:** ``print_info() -> None``
* **Input:** None.
* **Output:** Writes the hard-coded metadata block to ``stdout``.
* **Location:** src/bitranox_template_py_cli/__init__conf__.py

### In-Memory Adapters (Testing)

The ``adapters/memory/`` package provides lightweight implementations of all
application ports that operate entirely in memory.  They are distributed inside
``src/`` (see [ADR 0001](../adr/0001-memory-adapters-in-src.md)) so both tests
and library consumers can reuse them.

**Modules:**

| Module | Functions | Protocol Satisfied |
|--------|-----------|-------------------|
| ``memory/config.py`` | ``get_config_in_memory``, ``get_default_config_path_in_memory``, ``deploy_configuration_in_memory``, ``display_config_in_memory`` | ``GetConfig``, ``GetDefaultConfigPath``, ``DeployConfiguration``, ``DisplayConfig`` |
| ``memory/email.py`` | ``send_email_in_memory``, ``send_notification_in_memory``, ``load_email_config_from_dict_in_memory`` | ``SendEmail``, ``SendNotification``, ``LoadEmailConfigFromDict`` |
| ``memory/logging.py`` | ``init_logging_in_memory`` | ``InitLogging`` |

**Protocol conformance** is verified at type-check time via ``TYPE_CHECKING``
assertions in ``memory/__init__.py``.

### composition.build_testing

* **Purpose:** Wire in-memory adapters into an ``AppServices`` container for test isolation.
* **Signature:** ``build_testing() -> AppServices``
* **Output:** Frozen ``AppServices`` dataclass with all ports backed by no-op in-memory implementations.
* **Location:** src/bitranox_template_py_cli/composition/__init__.py

**Usage in tests:**

```python
from bitranox_template_py_cli.composition import build_testing

services = build_testing()
config = services.get_config()       # returns empty Config({}, {})
services.send_email(...)             # returns True without SMTP
services.init_logging(config)        # no-op
```

### Package Exports

* ``__init__.py`` re-exports behaviour helpers and ``print_info`` for library
  consumers. New code should import from the canonical module paths.

---

## CLI Commands

### Root Command Group

**Command:** ``bitranox-template-py-cli``

Shows help when invoked without a subcommand (``invoke_without_command=True``).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--version`` | flag | — | Show version and exit |
| ``--traceback / --no-traceback`` | bool flag | ``False`` | Show full Python traceback on errors |
| ``--profile NAME`` | ``str`` | ``None`` | Load configuration from a named profile |
| ``--set SECTION.KEY=VALUE`` | ``str`` (repeatable) | ``()`` | Override a configuration setting |
| ``-h, --help`` | flag | — | Show help and exit |

### info

**Command:** ``bitranox-template-py-cli info``
**Location:** adapters/cli/commands/info.py

Print resolved package metadata (name, version, homepage, author, etc.).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success)

### hello

**Command:** ``bitranox-template-py-cli hello``
**Location:** adapters/cli/commands/info.py

Emit the canonical greeting (``"Hello World"``).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success)

### fail

**Command:** ``bitranox-template-py-cli fail``
**Location:** adapters/cli/commands/info.py

Trigger an intentional ``RuntimeError("I should fail")`` for testing error handling.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 1 (GENERAL_ERROR via lib_cli_exit_tools exception handling)

### config

**Command:** ``bitranox-template-py-cli config``
**Location:** adapters/cli/commands/config.py

Display the current merged configuration from all sources.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--format`` | ``Choice["human", "json"]`` | ``"human"`` | Output format (human-readable or JSON) |
| ``--section NAME`` | ``str`` | ``None`` | Show only a specific configuration section |
| ``--profile NAME`` | ``str`` | ``None`` | Override profile from root command |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success), 22 (INVALID_ARGUMENT — section not found)

### config-deploy

**Command:** ``bitranox-template-py-cli config-deploy``
**Location:** adapters/cli/commands/config.py

Deploy default configuration to system or user directories.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--target`` | ``Choice["app", "host", "user"]`` (required, repeatable) | — | Target configuration layer(s) to deploy to |
| ``--force`` | bool flag | ``False`` | Overwrite existing configuration files |
| ``--profile NAME`` | ``str`` | ``None`` | Override profile from root command |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success), 1 (GENERAL_ERROR), 13 (PERMISSION_DENIED)

### config-generate-examples

**Command:** ``bitranox-template-py-cli config-generate-examples``
**Location:** adapters/cli/commands/config.py

Generate example configuration files in a target directory.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--destination DIR`` | ``Path`` (required, directory only) | — | Directory to write example files |
| ``--force`` | bool flag | ``False`` | Overwrite existing files |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success), 1 (GENERAL_ERROR)

### send-email

**Command:** ``bitranox-template-py-cli send-email``
**Location:** adapters/cli/commands/email.py

Send an email using configured SMTP settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--to ADDRESS`` | ``str`` (repeatable) | ``None`` (uses config default) | Recipient email address |
| ``--subject TEXT`` | ``str`` (required) | — | Email subject line |
| ``--body TEXT`` | ``str`` | ``""`` | Plain-text email body |
| ``--body-html TEXT`` | ``str`` | ``""`` | HTML email body (sent as multipart) |
| ``--from ADDRESS`` | ``str`` | ``None`` (uses config default) | Override sender address |
| ``--attachment PATH`` | ``Path`` (repeatable, must exist) | ``()`` | File to attach |
| ``--smtp-host HOST:PORT`` | ``str`` (repeatable) | ``()`` | Override SMTP host |
| ``--smtp-username USER`` | ``str`` | ``None`` | Override SMTP username |
| ``--smtp-password PASS`` | ``str`` | ``None`` | Override SMTP password |
| ``--use-starttls / --no-use-starttls`` | bool flag | ``None`` | Override STARTTLS setting |
| ``--timeout SECONDS`` | ``float`` | ``None`` | Override socket timeout |
| ``--raise-on-missing-attachments / --no-...`` | bool flag | ``None`` | Override missing attachment handling |
| ``--raise-on-invalid-recipient / --no-...`` | bool flag | ``None`` | Override invalid recipient handling |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success), 2 (FILE_NOT_FOUND), 22 (INVALID_ARGUMENT), 69 (SMTP_FAILURE), 78 (CONFIG_ERROR — no SMTP hosts configured)

### send-notification

**Command:** ``bitranox-template-py-cli send-notification``
**Location:** adapters/cli/commands/email.py

Send a simple plain-text notification email.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--to ADDRESS`` | ``str`` (repeatable) | ``None`` (uses config default) | Recipient email address |
| ``--subject TEXT`` | ``str`` (required) | — | Notification subject line |
| ``--message TEXT`` | ``str`` (required) | — | Notification message (plain text) |
| ``--from ADDRESS`` | ``str`` | ``None`` (uses config default) | Override sender address |
| ``--smtp-host HOST:PORT`` | ``str`` (repeatable) | ``()`` | Override SMTP host |
| ``--smtp-username USER`` | ``str`` | ``None`` | Override SMTP username |
| ``--smtp-password PASS`` | ``str`` | ``None`` | Override SMTP password |
| ``--use-starttls / --no-use-starttls`` | bool flag | ``None`` | Override STARTTLS setting |
| ``--timeout SECONDS`` | ``float`` | ``None`` | Override socket timeout |
| ``--raise-on-missing-attachments / --no-...`` | bool flag | ``None`` | Override missing attachment handling |
| ``--raise-on-invalid-recipient / --no-...`` | bool flag | ``None`` | Override invalid recipient handling |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success), 22 (INVALID_ARGUMENT), 69 (SMTP_FAILURE), 78 (CONFIG_ERROR — no SMTP hosts configured)

### logdemo

**Command:** ``bitranox-template-py-cli logdemo``
**Location:** adapters/cli/commands/logging.py

Run a logging demonstration to preview log output.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ``--theme NAME`` | ``str`` | ``"classic"`` | Logging theme to preview |
| ``-h, --help`` | flag | — | Show help and exit |

**Exit codes:** 0 (success)

---

## User-Visible Messages

### CLI Output Messages (click.echo)

| Command | Message | Meaning |
|---------|---------|---------|
| hello | ``Hello World`` | Canonical greeting — success path |
| info | Metadata block (name, title, version, homepage, author, etc.) | Package installation details |
| config | TOML-like or JSON configuration output | Effective merged configuration (sensitive values redacted) |
| config | ``Error: Section '{name}' not found or empty`` (stderr) | Requested ``--section`` does not exist |
| config-deploy | ``Configuration deployed successfully (profile: {name}):`` followed by ``  {path}`` lines | Files were created at listed paths |
| config-deploy | ``No files were created (all target files already exist).`` | No new files; use ``--force`` to overwrite |
| config-deploy | ``Error: Permission denied. {details}`` (stderr) | Insufficient permissions for system-wide deploy |
| config-deploy | ``Hint: System-wide deployment (--target app/host) may require sudo.`` (stderr) | Follows permission error |
| config-generate-examples | ``Generated {n} example file(s):`` followed by paths | Example files created |
| config-generate-examples | ``No files generated (all already exist). Use --force to overwrite.`` | All target files exist |
| send-email | ``Email sent successfully!`` | SMTP delivery completed |
| send-email | ``Email sending failed.`` (stderr) | SMTP delivery returned false |
| send-notification | ``Notification sent successfully!`` | SMTP delivery completed |
| send-notification | ``Notification sending failed.`` (stderr) | SMTP delivery returned false |
| send-email / send-notification | ``Error: No SMTP hosts configured. Please configure email.smtp_hosts in your config file.`` (stderr) | Missing SMTP host configuration |
| send-email / send-notification | ``See: {shell_command} config-deploy --target user`` (stderr) | Follows SMTP config error |
| send-email / send-notification | ``Error: Invalid email parameters - {details}`` (stderr) | Validation failure |
| send-email | ``Error: Attachment file not found - {details}`` (stderr) | Attachment deleted between parse and send |
| send-email / send-notification | ``Error: Failed to send email - {details}`` (stderr) | SMTP delivery error |
| send-email / send-notification | ``Error: Unexpected error - {details}`` (stderr) | Unhandled exception during send |
| logdemo | ``Log demo completed (theme: {theme})`` | Log demo finished |
| root (no subcommand) | Help text | No subcommand provided |
| root (``--set`` invalid) | ``Error: {details}`` (UsageError) | Malformed ``--set`` override |

### Log Messages (logging)

| Level | Source | Message | Meaning |
|-------|--------|---------|---------|
| INFO | commands/info.py | ``Displaying package information`` | ``info`` command executing |
| INFO | commands/info.py | ``Executing hello command`` | ``hello`` command executing |
| WARNING | commands/info.py | ``Executing intentional failure command`` | ``fail`` command about to raise |
| INFO | commands/config.py | ``Displaying configuration`` | ``config`` command executing |
| INFO | commands/config.py | ``Deploying configuration`` | ``config-deploy`` starting |
| INFO | commands/config.py | ``Generating example configuration files`` | ``config-generate-examples`` starting |
| ERROR | commands/config.py | ``Permission denied when deploying configuration`` | Deploy failed (EACCES) |
| ERROR | commands/config.py | ``Failed to deploy configuration`` | Deploy failed (other) |
| ERROR | commands/config.py | ``Failed to generate examples`` | Example generation failed |
| INFO | commands/email.py | ``Sending email`` | ``send-email`` starting |
| INFO | commands/email.py | ``Email sent via CLI`` | ``send-email`` succeeded |
| INFO | commands/email.py | ``Sending notification`` | ``send-notification`` starting |
| INFO | commands/email.py | ``Notification sent via CLI`` | ``send-notification`` succeeded |
| ERROR | commands/email.py | ``No SMTP hosts configured`` | Missing email.smtp_hosts |
| ERROR | commands/email.py | Various (``Invalid email parameters``, ``SMTP delivery failed``, etc.) | Send operation errors |

---

## Implementation Details

**Dependencies:**

* External: ``rich_click``, ``lib_cli_exit_tools``, ``lib_layered_config``, ``lib_log_rich``, ``btx-lib-mail``, ``orjson``
* Internal: ``behaviors`` module, ``__init__conf__`` static metadata constants, ``config``, ``adapters.email.sender``

**Key Configuration:**

* No environment variables required for basic operation.
* Traceback preferences controlled via CLI ``--traceback`` flag.

**Error Handling Strategy:**

* ``lib_cli_exit_tools`` centralises exception rendering and signal handling
  (SIGINT->130, SIGTERM->143 via ``run_cli(install_signals=True)``).
* CLI commands raise ``SystemExit(ExitCode.XXX)`` with POSIX-conventional codes
  defined in ``adapters/cli/exit_codes.py``.
* ``apply_traceback_preferences`` ensures colour output for ``--traceback``.
* ``restore_traceback_state`` restores previous preferences after each run.

---

## Testing Approach

**Manual Testing Steps:**

1. ``bitranox-template-py-cli`` -> prints CLI help (no default action).
2. ``bitranox-template-py-cli hello`` -> prints greeting.
3. ``bitranox-template-py-cli fail`` -> prints truncated traceback.
4. ``bitranox-template-py-cli --traceback fail`` -> prints full rich traceback.
5. ``python -m bitranox_template_py_cli --traceback fail`` -> matches console output.

**Automated Tests:**

* ``tests/test_cli.py`` exercises the help-first behaviour, failure path,
  metadata output, and invalid command handling for the click surface.
* ``tests/test_module_entry.py`` ensures ``python -m`` entry mirrors the console
  script, including traceback behaviour.
* ``tests/test_behaviors.py`` verifies pure domain functions (greeting string).
* ``tests/test_cache_effectiveness.py`` validates LRU cache behaviour for
  ``get_config()`` and ``get_default_config_path()``.
* ``tests/test_config_overrides.py`` tests ``--set`` parsing, coercion, and deep-merge.
* ``tests/test_display.py`` tests configuration display formatting, section
  filtering, redaction, and nested dict rendering.
* ``tests/test_exit_codes.py`` verifies all ExitCode enum members and their values.
* ``tests/test_mail.py`` tests email configuration, validation, and sending.
* ``tests/test_metadata.py`` verifies ``__init__conf__`` constants match ``pyproject.toml``.
* ``tests/test_ports.py`` validates Protocol conformance assertions.
* ``tests/test_scripts.py`` tests build/automation scripts.

**Test Data:**

* Shared fixtures in ``conftest.py``: ``config_factory`` (creates real ``Config``
  instances), ``inject_config`` (injects config into CLI path), ``cli_runner``,
  ``strip_ansi``, ``clear_config_cache``,
  ``preserve_traceback_state``, ``isolated_traceback_config``.
* SMTP mocking (``patch("smtplib.SMTP")``) is the only justified mock usage —
  all other tests use real ``Config`` objects via ``Config(data, {})``.

---

## Documentation & Resources

**Internal References:**

* README.md — usage examples
* INSTALL.md — installation options
* DEVELOPMENT.md — developer workflow

---

## Instructions for Use

1. Trigger this document whenever CLI commands or architecture components change.
2. Keep module descriptions in sync with code during refactors.
3. Extend with new components when additional commands ship.

**Last Updated:** 2026-01-27
