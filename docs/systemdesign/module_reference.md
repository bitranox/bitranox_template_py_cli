# Feature Documentation: Clean Architecture CLI Template

## Status

Complete

## Links & References
**Feature Requirements:** Clean Architecture implementation
**Task/Ticket:** None documented
**Related Files:**

### Domain Layer
* src/bitranox_template_py_cli/domain/__init__.py
* src/bitranox_template_py_cli/domain/greeting.py
* src/bitranox_template_py_cli/domain/errors.py

### Application Layer
* src/bitranox_template_py_cli/application/__init__.py
* src/bitranox_template_py_cli/application/ports/__init__.py
* src/bitranox_template_py_cli/application/ports/output.py
* src/bitranox_template_py_cli/application/use_cases/__init__.py
* src/bitranox_template_py_cli/application/use_cases/greeting.py
* src/bitranox_template_py_cli/application/use_cases/failure.py
* src/bitranox_template_py_cli/application/use_cases/info.py

### Adapters Layer
* src/bitranox_template_py_cli/adapters/__init__.py
* src/bitranox_template_py_cli/adapters/output/__init__.py
* src/bitranox_template_py_cli/adapters/output/stdout.py
* src/bitranox_template_py_cli/adapters/cli/__init__.py
* src/bitranox_template_py_cli/adapters/cli/constants.py
* src/bitranox_template_py_cli/adapters/cli/traceback.py
* src/bitranox_template_py_cli/adapters/cli/context.py
* src/bitranox_template_py_cli/adapters/cli/root.py
* src/bitranox_template_py_cli/adapters/cli/main.py
* src/bitranox_template_py_cli/adapters/cli/commands/__init__.py
* src/bitranox_template_py_cli/adapters/cli/commands/info.py

### Composition Layer
* src/bitranox_template_py_cli/composition/__init__.py
* src/bitranox_template_py_cli/composition/container.py

### Package Root
* src/bitranox_template_py_cli/__main__.py
* src/bitranox_template_py_cli/__init__.py
* src/bitranox_template_py_cli/__init__conf__.py

### Tests
* tests/test_cli.py
* tests/test_module_entry.py
* tests/test_behaviors.py (tests domain/application layers)
* tests/test_metadata.py
* tests/conftest.py

---

## Problem Statement

The template needed a proper clean architecture implementation following the
principles from `python_clean_architecture.md`:
- Dependencies point inward only
- Domain pure (no I/O, logs, frameworks)
- Use cases free of framework types
- Boundary validation at edges
- Import enforcement via import-linter

## Solution Overview

Implemented a 4-layer clean architecture:

1. **Domain Layer** (`domain/`): Pure business logic
   - `greeting.py`: Returns greeting string without I/O
   - `errors.py`: Domain-specific `IntentionalFailure` exception

2. **Application Layer** (`application/`): Use cases and ports
   - `ports/output.py`: `OutputPort` Protocol defining output interface
   - `use_cases/`: `GreetingUseCase`, `FailureUseCase`, `InfoUseCase`

3. **Adapters Layer** (`adapters/`): Framework implementations
   - `output/stdout.py`: `StdoutAdapter` implementing `OutputPort`
   - `cli/`: CLI transport using rich-click

4. **Composition Layer** (`composition/`): Dependency wiring
   - `container.py`: Factory functions creating wired use cases

---

## Architecture Integration

**Layer Dependencies:**
```
Composition → Adapters → Application → Domain
```

Inner layers never import from outer layers. Enforced by import-linter contract:

```toml
[[tool.importlinter.contracts]]
name = "Clean architecture layers"
type = "layers"
layers = [
  "bitranox_template_py_cli.adapters",
  "bitranox_template_py_cli.application",
  "bitranox_template_py_cli.domain",
]
```

**Data Flow:**
1. CLI parses options with rich-click
2. CLI commands call composition container to create use cases
3. Use cases execute domain logic via ports
4. Adapters implement ports and handle I/O
5. Exit codes and tracebacks rendered by `lib_cli_exit_tools`

**System Dependencies:**
* `rich_click` for CLI UX
* `lib_cli_exit_tools` for exit-code normalisation and traceback output

---

## Core Components

### Domain Layer

#### domain.greeting
* **Purpose:** Pure greeting logic
* **Functions:**
  - `get_greeting() -> str`: Returns "Hello World" without I/O
* **Constants:**
  - `CANONICAL_GREETING`: The greeting string
* **Location:** src/bitranox_template_py_cli/domain/greeting.py

#### domain.errors.IntentionalFailure
* **Purpose:** Domain error for testing failure flows
* **Input:** None
* **Output:** Raises with message "I should fail"
* **Location:** src/bitranox_template_py_cli/domain/errors.py

### Application Layer

#### application.ports.OutputPort
* **Purpose:** Protocol interface for text output
* **Methods:**
  - `write(text: str) -> None`
  - `write_line(text: str) -> None`
* **Location:** src/bitranox_template_py_cli/application/ports/output.py

#### application.use_cases.GreetingUseCase
* **Purpose:** Emit greeting via output port
* **Input:** `OutputPort` instance via constructor
* **Output:** Writes greeting to output port
* **Location:** src/bitranox_template_py_cli/application/use_cases/greeting.py

#### application.use_cases.FailureUseCase
* **Purpose:** Raise intentional failure
* **Input:** None
* **Output:** Raises `IntentionalFailure`
* **Location:** src/bitranox_template_py_cli/application/use_cases/failure.py

#### application.use_cases.InfoUseCase
* **Purpose:** Output package metadata
* **Input:** `OutputPort` instance via constructor
* **Output:** Writes metadata via `__init__conf__.print_info()`
* **Location:** src/bitranox_template_py_cli/application/use_cases/info.py

### Adapters Layer

#### adapters.output.StdoutAdapter
* **Purpose:** Write text to stdout or custom stream
* **Input:** Optional `TextIO` stream (defaults to stdout)
* **Output:** Text written to stream
* **Location:** src/bitranox_template_py_cli/adapters/output/stdout.py

#### adapters.cli.constants
* **Purpose:** Centralise shared CLI configuration values
* **Contents:**
  - `CLICK_CONTEXT_SETTINGS` - Shared Click settings for help display
  - `TRACEBACK_SUMMARY_LIMIT` - Character budget for truncated tracebacks
  - `TRACEBACK_VERBOSE_LIMIT` - Character budget for verbose tracebacks
* **Location:** src/bitranox_template_py_cli/adapters/cli/constants.py

#### adapters.cli.traceback
* **Purpose:** Manage traceback state synchronisation with `lib_cli_exit_tools`
* **Contents:**
  - `TracebackState` - Type alias for traceback configuration state
  - `apply_traceback_preferences(enabled)` - Enable/disable verbose tracebacks
  - `snapshot_traceback_state()` - Capture current traceback config
  - `restore_traceback_state(state)` - Restore previously captured config
* **Location:** src/bitranox_template_py_cli/adapters/cli/traceback.py

#### adapters.cli.context
* **Purpose:** Provide typed helpers for Click context state management
* **Contents:**
  - `CLIContextData` - Typed dataclass for CLI context data
  - `store_cli_context(ctx, traceback)` - Store CLI state in Click context
  - `get_cli_context(ctx)` - Retrieve CLI state from Click context
* **Location:** src/bitranox_template_py_cli/adapters/cli/context.py

#### adapters.cli.root
* **Purpose:** Define the root Click command group with global options
* **Contents:**
  - `cli` - Root command group with `--traceback` and `--version` options
  - `cli_main()` - Domain entry when no subcommand is specified
* **Location:** src/bitranox_template_py_cli/adapters/cli/root.py

#### adapters.cli.main
* **Purpose:** Provide the single entry point for CLI execution
* **Contents:**
  - `main(argv, restore_traceback)` - Execute CLI with error handling
* **Location:** src/bitranox_template_py_cli/adapters/cli/main.py

#### adapters.cli.commands.info
* **Purpose:** Implement basic CLI commands
* **Contents:**
  - `cli_info` - Display package metadata
  - `cli_hello` - Emit canonical greeting
  - `cli_fail` - Trigger intentional failure for testing
* **Location:** src/bitranox_template_py_cli/adapters/cli/commands/info.py

### Composition Layer

#### composition.container
* **Purpose:** Factory functions for creating wired use cases
* **Contents:**
  - `create_greeting_use_case(stream)` - Create GreetingUseCase with StdoutAdapter
  - `create_failure_use_case()` - Create FailureUseCase
  - `create_info_use_case(stream)` - Create InfoUseCase with StdoutAdapter
  - `noop()` - Placeholder callable
* **Location:** src/bitranox_template_py_cli/composition/container.py

### Package Root

#### __main__._module_main
* **Purpose:** Provide `python -m` entry point mirroring the console script
* **Input:** None
* **Output:** Exit code from `adapters.cli.main`
* **Location:** src/bitranox_template_py_cli/__main__.py

#### __init__conf__.print_info
* **Purpose:** Render the statically-defined project metadata for the CLI `info` command
* **Input:** None
* **Output:** Writes the hard-coded metadata block to `stdout`
* **Location:** src/bitranox_template_py_cli/__init__conf__.py

#### Package Exports (__init__.py)
* Re-exports domain constants and composition layer for convenient access
* Exports: `CANONICAL_GREETING`, `get_greeting`, `IntentionalFailure`, `container`, `print_info`

---

## Implementation Details

**Dependencies:**
* External: `rich_click`, `lib_cli_exit_tools`
* Internal: Domain → Application → Adapters → Composition

**Key Configuration:**
* No environment variables required
* Traceback preferences controlled via CLI `--traceback` flag

**Database Changes:**
* None

**Error Handling Strategy:**
* Domain layer raises domain exceptions (`IntentionalFailure`)
* CLI adapter catches exceptions and maps to exit codes via `lib_cli_exit_tools`
* `apply_traceback_preferences` ensures colour output for `--traceback`
* `restore_traceback_state` restores previous preferences after each run

---

## Testing Approach

**Manual Testing Steps:**
1. `bitranox_template_py_cli` → prints CLI help (no default action)
2. `bitranox_template_py_cli hello` → prints greeting
3. `bitranox_template_py_cli fail` → prints truncated traceback
4. `bitranox_template_py_cli --traceback fail` → prints full rich traceback
5. `python -m bitranox_template_py_cli --traceback fail` → matches console output

**Automated Tests:**
* `tests/test_behaviors.py` tests all layers: domain, application, adapters, composition
* `tests/test_cli.py` exercises CLI help, commands, traceback flags
* `tests/test_module_entry.py` ensures `python -m` entry mirrors the console script
* `tests/test_metadata.py` validates pyproject.toml synchronization
* Doctests embedded in modules provide micro-regression tests

**Integration Tests:**
* Run via `make test-slow` (not run in CI)
* Mark tests with `@pytest.mark.integration`
* Use for slow tests requiring external resources
* No integration tests exist yet - infrastructure prepared for future use

**Edge Cases:**
* Running without subcommand shows help (or noop if --traceback explicit)
* Repeated invocations respect previous traceback preference

**Test Data:**
* No fixtures required; tests rely on built-in `CliRunner` and monkeypatching

---

## Security Considerations

**Input Validation:**
* CLI uses Click framework with type validation
* Pydantic models validate configuration at boundaries
* No user-supplied paths or shell commands in production code

**Error Handling Strategy:**
* Exceptions propagate to top-level handler in `adapters/cli/main.py`
* `lib_cli_exit_tools` renders tracebacks and maps exit codes
* I/O errors (broken pipe, etc.) handled gracefully

**Edge Cases Handled:**
* None values: `getattr()` with defaults in traceback.py
* Missing attributes: `isinstance()` guards in context.py
* Streams without flush: Safe `callable()` check in stdout.py

**Security Review:** 2026-01-15 - No vulnerabilities found in production code.

---

## Performance Considerations

**Caching Analysis:** 2026-01-15 - No `lru_cache` optimizations needed.

This CLI tool has no suitable caching candidates because:
* **I/O-focused**: Operations are user input/output, not computation
* **Single invocation**: Functions called once per command, not in loops
* **Trivial pure functions**: Domain functions return constants (no computation)
* **Clean architecture**: Dependency injection requires fresh instances

---

## Known Issues & Future Improvements

**Current Limitations:**
* InfoUseCase still uses `print_info()` directly rather than output port

**Future Enhancements:**
* Introduce structured logging once the logging stack lands
* Expand the module reference when new commands or use cases are added

---

## Risks & Considerations

**Technical Risks:**
* Traceback behaviour depends on `lib_cli_exit_tools`; upstream changes may
  require adjustments to the adapter functions

**User Impact:**
* None expected; CLI surface and public imports remain stable

---

## Documentation & Resources

**Internal References:**
* README.md – usage examples
* INSTALL.md – installation options
* DEVELOPMENT.md – developer workflow
* CLAUDE.md – architecture overview

**External References:**
* rich-click documentation
* lib_cli_exit_tools project README
* python_clean_architecture.md guidelines

---

**Created:** 2025-09-26 by Codex (automation)
**Last Updated:** 2026-01-15
**Review Cycle:** Evaluate during next feature milestone

---

## Instructions for Use

1. Trigger this document whenever architecture or layer structure changes
2. Keep module descriptions in sync with code during future refactors
3. Extend with new components when additional use cases are added
