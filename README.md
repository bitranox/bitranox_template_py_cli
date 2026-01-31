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


### Python 3.10+ Baseline

- The project targets **Python 3.10 and newer**.
- Runtime dependencies require current stable releases (`rich-click>=1.9.6`
  and `lib_cli_exit_tools>=2.2.4`). Dev dependencies (pytest, ruff, pyright,
  bandit, etc.) specify minimum version constraints to ensure compatibility.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.10 through 3.14
  alongside the latest available 3.x release provided by Actions.

---

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

---

## Configuration

See [CONFIG.md](CONFIG.md) for detailed documentation on the layered configuration system, including precedence rules, profile support, and customization best practices.

---

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

# Profile names: alphanumeric, hyphens, underscores; max 64 chars; must start with letter/digit
# See CONFIG.md for full validation rules

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

**Configuration File**:
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

## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)
