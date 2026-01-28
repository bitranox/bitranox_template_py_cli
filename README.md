# bitranox_template_py_cli

<!-- Badges -->
[![CI](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/default_cicd_public.yml/badge.svg)](https://github.com/bitranox/bitranox_template_py_cli/actions/workflows/default_cicd_public.yml)
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

`bitranox_template_py_cli` is a template CLI application demonstrating configuration management and structured logging. It showcases rich-click for ergonomics and lib_cli_exit_tools for exits, providing a solid foundation for building CLI applications.
- CLI entry point styled with rich-click (rich output + click ergonomics).
- Layered configuration system with lib_layered_config (defaults → app → host → user → .env → env).
- Rich structured logging with lib_log_rich (console, journald, eventlog, Graylog/GELF).
- Exit-code and messaging helpers powered by lib_cli_exit_tools.
- Metadata helpers ready for packaging, testing, and release automation.

## Install - recommended via uv

[uv](https://docs.astral.sh/uv/) is an ultrafast Python package manager written in Rust (10-20x faster than pip/poetry).

### Install uv (if not already installed) 
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### One-shot run (no install needed)

```bash
uvx bitranox_template_py_cli@latest --help
```

### Persistent install as CLI tool

```bash
# install the CLI tool (isolated environment, added to PATH)
uv tool install bitranox_template_py_cli

# upgrade to latest
uv tool upgrade bitranox_template_py_cli
```

### Install as project dependency

```bash
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
uv pip install bitranox_template_py_cli
```

For alternative install paths (pip, pipx, source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`bitranox_template_py_cli` and `bitranox-template-py-cli` commands on your PATH.

### Python 3.10+ Baseline

- The project targets **Python 3.10 and newer**.
- Runtime dependencies stay on the current stable releases (`rich-click>=1.9.6`
  and `lib_cli_exit_tools>=2.2.4`) and keeps pytest, ruff, pyright, bandit,
  build, twine, codecov-cli, pip-audit, textual, and import-linter pinned to
  their newest majors.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.10 through 3.13
  alongside the latest available 3.x release provided by Actions.


## Quick Start

```bash
# Install
uv tool install bitranox_template_py_cli

# Verify
bitranox-template-py-cli --version

# Try it out
bitranox-template-py-cli hello
bitranox-template-py-cli info
bitranox-template-py-cli config
```

---

## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.

### Available Commands

```bash
# Display package information
bitranox-template-py-cli info

# Greeting and error-handling demos
bitranox-template-py-cli hello
bitranox-template-py-cli fail
bitranox-template-py-cli --traceback fail

# Configuration management
bitranox-template-py-cli config                         # Show current configuration
bitranox-template-py-cli config --format json           # Show as JSON
bitranox-template-py-cli config --section lib_log_rich  # Show specific section
bitranox-template-py-cli config --profile production    # Use a named profile

# Deploy configuration templates to target directories
# Without profile:
bitranox-template-py-cli config-deploy --target app    # → /etc/xdg/{slug}/config.toml
bitranox-template-py-cli config-deploy --target host   # → /etc/xdg/{slug}/hosts/{hostname}.toml
bitranox-template-py-cli config-deploy --target user   # → ~/.config/{slug}/config.toml

# With profile:
bitranox-template-py-cli config-deploy --target app --profile production   # → /etc/xdg/{slug}/profile/production/config.toml
bitranox-template-py-cli config-deploy --target host --profile production  # → /etc/xdg/{slug}/profile/production/hosts/{hostname}.toml
bitranox-template-py-cli config-deploy --target user --profile production  # → ~/.config/{slug}/profile/production/config.toml

# Deploy configuration examples
bitranox-template-py-cli config-generate-examples --destination ./examples

# Override configuration at runtime (repeatable --set)
bitranox-template-py-cli --set lib_log_rich.console_level=DEBUG config
bitranox-template-py-cli --set email.smtp_hosts='["smtp.example.com:587"]' config --format json

# Logging demo
bitranox-template-py-cli logdemo
bitranox-template-py-cli --set lib_log_rich.console_level=DEBUG logdemo

# Send email
bitranox-template-py-cli send-email \
    --to recipient@example.com \
    --subject "Test Email" \
    --body "Hello from bitranox!"

# Send email with HTML body and attachments
bitranox-template-py-cli send-email \
    --to recipient@example.com \
    --subject "Monthly Report" \
    --body "See attached." \
    --body-html "<h1>Report</h1><p>Details in the PDF.</p>" \
    --attachment report.pdf

# Send plain-text notification
bitranox-template-py-cli send-notification \
    --to ops@example.com \
    --subject "Deploy OK" \
    --message "Application deployed successfully"

# All commands work with any entry point
python -m bitranox_template_py_cli info
uvx bitranox_template_py_cli info
```

---

### Configuration Files


#### Precedence Order (lowest → highest)

**Path placeholders for this project:**
- `{slug}` = `bitranox-template-py-cli` (Linux)
- `{vendor}` = `bitranox` (Windows)
- `{app}` = `Bitranox Template Py Cli` (Windows)  


#### Paths without Profile

| Layer       | Linux Path                              | Windows Path                                                 | Purpose                               |
|-------------|-----------------------------------------|--------------------------------------------------------------|---------------------------------------|
| 1. defaults | (bundled with package)                  | (bundled with package)                                       | Fallback values shipped with app      |
| 2. app      | `/etc/xdg/{slug}/config.toml`           | `C:\ProgramData\{vendor}\{app}\config.toml`                  | System-wide defaults for ALL machines |
| 3. host     | `/etc/xdg/{slug}/hosts/{hostname}.toml` | `C:\ProgramData\{vendor}\{app}\hosts\{hostname}.toml`        | Overrides for THIS specific machine   |
| 4. user     | `~/.config/{slug}/config.toml`          | `C:\Users\{user}\AppData\Roaming\{vendor}\{app}\config.toml` | User's personal settings              |
| 5. .env     | (project directory)                     | (project directory)                                          | Project-level overrides               |
| 6. env vars | `BITRANOX_TEMPLATE_PY_CLI___...`        | `BITRANOX_TEMPLATE_PY_CLI___...`                             | Runtime overrides                     |
| 7. CLI      | `--set section.key=value`               | `--set section.key=value`                                    | Command-line overrides (highest)      |
 The defaultconfig.d/ templates become the fallback defaults - the baseline that exists when no external configs are deployed.

#### Paths with Profile "test"

| Layer       | Linux Path                                            | Windows Path                                                               | Purpose                               |
|-------------|-------------------------------------------------------|----------------------------------------------------------------------------|---------------------------------------|
| 1. defaults | (bundled with package)                                | (bundled with package)                                                     | Fallback values shipped with app      |
| 2. app      | `/etc/xdg/{slug}/profile/test/config.toml`            | `C:\ProgramData\{vendor}\{app}\profile\test\config.toml`                   | System-wide defaults for ALL machines |
| 3. host     | `/etc/xdg/{slug}/profile/test/hosts/{hostname}.toml`  | `C:\ProgramData\{vendor}\{app}\profile\test\hosts\{hostname}.toml`         | Overrides for THIS specific machine   |
| 4. user     | `~/.config/{slug}/profile/test/config.toml`           | `C:\Users\{user}\AppData\Roaming\{vendor}\{app}\profile\test\config.toml`  | User's personal settings              |
| 5. .env     | (project directory)                                   | (project directory)                                                        | Project-level overrides               |
| 6. env vars | `BITRANOX_TEMPLATE_PY_CLI___...`                      | `BITRANOX_TEMPLATE_PY_CLI___...`                                           | Runtime overrides                     |
| 7. CLI      | `--set section.key=value`                             | `--set section.key=value`                                                  | Command-line overrides (highest)      |

The defaultconfig.d/ templates become the fallback defaults - the baseline that exists when no external configs are deployed.

#### layers effected by profile : 

The default_file parameter is always provided, independent of the profile parameter.

Profile only affects layers 2-4 (app, host, user) by inserting a `profile/<name>/` subdirectory. The other layers are unchanged:

| Layer       | Affected by profile?                |
|-------------|-------------------------------------|
| 1. defaults | No - always loaded                  |
| 2. app      | Yes - uses `profile/<name>/` subdir |
| 3. host     | Yes - uses `profile/<name>/` subdir |
| 4. user     | Yes - uses `profile/<name>/` subdir |
| 5. .env     | No - project directory              |
| 6. env vars | No - environment                    |
| 7. CLI      | No - command line                   |       


####  Deploy layers with profile

```bash
      # Deploy app layer with profile
      config-deploy --target app --profile profile1  # Creates: /etc/xdg/{slug}/profile/profile1/config.toml

      # Deploy user layer without profile
      config-deploy --target user                    # Creates: ~/.config/{slug}/config.toml
```

#### Reading behavior with profiles

| Read Command                | Sees app layer?            | Sees user layer?          |
|-----------------------------|----------------------------|---------------------------|
| `config` (no profile)       | No (app only has profile1) | Yes                       |
| `config --profile profile1` | Yes                        | No (user has no profile1) |

Profile directories are separate namespaces. Config deployed with a profile is only visible when reading with that same profile.        

---

### Email Sending

The application includes email sending capabilities via [btx-lib-mail](https://pypi.org/project/btx-lib-mail/), supporting both simple notifications and rich HTML emails with attachments.

#### Email Configuration

Configure email settings via environment variables, `.env` file, or configuration files:

**Environment Variables:**

Environment variables use the format: `<PREFIX>___<SECTION>__<KEY>=value`
- Triple underscore (`___`) separates PREFIX from SECTION
- Double underscore (`__`) separates SECTION from KEY

```bash
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_HOSTS="smtp.gmail.com:587,smtp.backup.com:587"
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__FROM_ADDRESS="alerts@myapp.com"
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_USERNAME="your-email@gmail.com"
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_PASSWORD="your-app-password"
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__USE_STARTTLS="true"
export BITRANOX_TEMPLATE_PY_CLI___EMAIL__TIMEOUT="60.0"
```

**Configuration File** (`~/.config/bitranox-template-py-cli/config.toml`):
```toml
[email]
smtp_hosts = ["smtp.gmail.com:587", "smtp.backup.com:587"]  # Fallback to backup if primary fails
from_address = "alerts@myapp.com"
smtp_username = "myuser@gmail.com"
smtp_password = "secret_password"  # Consider using environment variables for sensitive data
use_starttls = true
timeout = 60.0
```

**`.env` File:**
```bash
# Email configuration for local testing
BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_HOSTS=smtp.gmail.com:587
BITRANOX_TEMPLATE_PY_CLI___EMAIL__FROM_ADDRESS=noreply@example.com
```

#### Gmail Configuration Example

For Gmail, create an [App Password](https://support.google.com/accounts/answer/185833) instead of using your account password:

```bash
BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_HOSTS=smtp.gmail.com:587
BITRANOX_TEMPLATE_PY_CLI___EMAIL__FROM_ADDRESS=your-email@gmail.com
BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_USERNAME=your-email@gmail.com
BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_PASSWORD=your-16-char-app-password
```

#### Send Simple Email

```bash
# Send basic email to one recipient
bitranox-template-py-cli send-email \
    --to recipient@example.com \
    --subject "Test Email" \
    --body "Hello from bitranox!"

# Send to multiple recipients
bitranox-template-py-cli send-email \
    --to user1@example.com \
    --to user2@example.com \
    --subject "Team Update" \
    --body "Please review the latest changes"
```

#### Send HTML Email with Attachments

```bash
bitranox-template-py-cli send-email \
    --to recipient@example.com \
    --subject "Monthly Report" \
    --body "Please find the monthly report attached." \
    --body-html "<h1>Monthly Report</h1><p>See attached PDF for details.</p>" \
    --attachment report.pdf \
    --attachment data.csv
```

#### Send Notifications

For simple plain-text notifications, use the convenience command:

```bash
# Single recipient
bitranox-template-py-cli send-notification \
    --to ops@example.com \
    --subject "Deployment Success" \
    --message "Application deployed successfully to production at $(date)"

# Multiple recipients
bitranox-template-py-cli send-notification \
    --to admin1@example.com \
    --to admin2@example.com \
    --subject "System Alert" \
    --message "Database backup completed successfully"
```

#### Programmatic Email Usage

```python
from bitranox_template_py_cli.adapters.email.sender import EmailConfig
from bitranox_template_py_cli.composition import send_email, send_notification

# Configure email
config = EmailConfig(
    smtp_hosts=["smtp.gmail.com:587"],
    from_address="alerts@myapp.com",
    smtp_username="myuser@gmail.com",
    smtp_password="app-password",
    timeout=60.0,
)

# Send simple email
send_email(
    config=config,
    recipients="recipient@example.com",
    subject="Test Email",
    body="Hello from Python!",
)

# Send email with HTML and attachments
from pathlib import Path
send_email(
    config=config,
    recipients=["user1@example.com", "user2@example.com"],
    subject="Report",
    body="See attached report",
    body_html="<h1>Report</h1><p>Details in attachment</p>",
    attachments=[Path("report.pdf")],
)

# Send notification
send_notification(
    config=config,
    recipients="ops@example.com",
    subject="Deployment Complete",
    message="Production deployment finished successfully",
)
```

#### Email Troubleshooting

**Connection Failures:**
- Verify SMTP hostname and port are correct
- Check firewall allows outbound connections on SMTP port
- Test connectivity: `telnet smtp.gmail.com 587`

**Authentication Errors:**
- For Gmail: Use App Password, not account password
- Ensure username/password are correct
- Check for 2FA requirements

**Emails Not Arriving:**
- Check recipient's spam folder
- Verify `from_address` is valid and not blacklisted
- Review SMTP server logs for delivery status

### Configuration Management

The application uses [lib_layered_config](https://github.com/bitranox/lib_layered_config) for hierarchical configuration with the following precedence (lowest to highest):

**defaults → app → host → user → .env → environment variables**

#### Configuration Locations

Platform-specific paths:
- **Linux (user)**: `~/.config/bitranox-template-py-cli/config.toml`
- **Linux (app)**: `/etc/xdg/bitranox-template-py-cli/config.toml`
- **Linux (host)**: `/etc/bitranox-template-py-cli/hosts/{hostname}.toml`
- **macOS (user)**: `~/Library/Application Support/bitranox/Bitranox Template Py Cli/config.toml`
- **Windows (user)**: `%APPDATA%\bitranox\Bitranox Template Py Cli\config.toml`

#### Profile-Specific Configuration

Profiles allow environment-specific configuration (e.g., production, staging, test). When a profile is specified, configuration is loaded from profile-specific subdirectories:

- **Linux (user, profile=production)**: `~/.config/bitranox-template-py-cli/profile/production/config.toml`
- **Linux (app, profile=staging)**: `/etc/xdg/bitranox-template-py-cli/profile/staging/config.toml`

Use profiles to maintain separate configurations for different environments while keeping a common base configuration.

#### View Configuration

```bash
# Show merged configuration from all sources
bitranox-template-py-cli config

# Show as JSON for scripting
bitranox-template-py-cli config --format json

# Show specific section only
bitranox-template-py-cli config --section lib_log_rich

# Show configuration for a specific profile
bitranox-template-py-cli config --profile production

# Combine options
bitranox-template-py-cli config --profile staging --format json --section email
```

#### Deploy Configuration Files

```bash
# Create user configuration file
bitranox-template-py-cli config-deploy --target user

# Deploy to system-wide location (requires privileges)
sudo bitranox-template-py-cli config-deploy --target app

# Deploy to multiple locations at once
bitranox-template-py-cli config-deploy --target user --target host

# Overwrite existing configuration
bitranox-template-py-cli config-deploy --target user --force

# Deploy to a specific profile directory
bitranox-template-py-cli config-deploy --target user --profile production

# Deploy production profile and overwrite if exists
bitranox-template-py-cli config-deploy --target user --profile production --force
```

#### Environment Variable Overrides

Configuration can be overridden via environment variables using two methods:

**Method 1: Native lib_log_rich variables (highest precedence)**
```bash
LOG_CONSOLE_LEVEL=DEBUG bitranox-template-py-cli hello
LOG_ENABLE_GRAYLOG=true LOG_GRAYLOG_ENDPOINT="logs.example.com:12201" bitranox-template-py-cli hello
```

**Method 2: Application-prefixed variables**

Format: `<PREFIX>___<SECTION>__<KEY>=value`

```bash
BITRANOX_TEMPLATE_PY_CLI___LIB_LOG_RICH__CONSOLE_LEVEL=DEBUG bitranox-template-py-cli hello
```

#### .env File Support

Create a `.env` file in your project directory for local development:

```bash
# .env
LOG_CONSOLE_LEVEL=DEBUG
LOG_CONSOLE_FORMAT_PRESET=short
LOG_ENABLE_GRAYLOG=false
```

The application automatically discovers and loads `.env` files from the current directory or parent directories.

### Library Use

You can import the documented helpers directly:

```python
import bitranox_template_py_cli as btcacl

print(btcacl.build_greeting())
btcacl.print_info()

config = btcacl.get_config()
print(config.as_dict())
```


## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)
