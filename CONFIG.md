# Configuration System

This project uses [`lib_layered_config`](https://github.com/bitranox/lib_layered_config) to manage configuration through a layered merging system. Configuration values are loaded from multiple sources and merged in a defined order, allowing flexible overrides from system-wide defaults down to individual command-line arguments.

## Key Concepts

- **Layered merging**: Configuration is assembled from multiple files and sources, with later layers overriding earlier ones
- **Cross-platform paths**: Follows XDG conventions on Linux, standard locations on macOS and Windows
- **Profile support**: Named profiles allow environment-specific configurations (e.g., `production`, `staging`, `test`)
- **TOML format**: All configuration files use TOML syntax
- **Runtime overrides**: Values can be overridden via environment variables or CLI flags without modifying files

---

## Configuration Layers

Configuration is loaded and merged in the following order (lowest to highest precedence):

| Priority | Layer        | Description                                      |
|:--------:|--------------|--------------------------------------------------|
| 1        | **defaults** | Bundled with the package (`defaultconfig.toml`)  |
| 2        | **app**      | System-wide settings for all machines            |
| 3        | **host**     | Machine-specific overrides                       |
| 4        | **user**     | User's personal settings                         |
| 5        | **.env**     | Project directory dotenv file                    |
| 6        | **env vars** | Environment variables                            |
| 7        | **CLI**      | Command-line `--set` flags (highest priority)    |

**Merge behavior**: Each layer only needs to specify values it wants to override. Unspecified values inherit from lower layers.

---

## File Locations

### Platform-Specific Paths

| Layer    | Linux                                   | macOS                                                              | Windows                                                      |
|----------|-----------------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------|
| defaults | (bundled with package)                  | (bundled with package)                                             | (bundled with package)                                       |
| app      | `/etc/xdg/{slug}/config.toml`           | `/Library/Application Support/{vendor}/{app}/config.toml`          | `C:\ProgramData\{vendor}\{app}\config.toml`                  |
| host     | `/etc/xdg/{slug}/hosts/{hostname}.toml` | `/Library/Application Support/{vendor}/{app}/hosts/{hostname}.toml`| `C:\ProgramData\{vendor}\{app}\hosts\{hostname}.toml`        |
| user     | `~/.config/{slug}/config.toml`          | `~/Library/Application Support/{vendor}/{app}/config.toml`         | `%APPDATA%\{vendor}\{app}\config.toml`                       |

### Path Placeholders

| Placeholder  | Linux                        | macOS / Windows              |
|--------------|------------------------------|------------------------------|
| `{slug}`     | `bitranox-template-py-cli`   | —                            |
| `{vendor}`   | —                            | `bitranox`                   |
| `{app}`      | —                            | `Bitranox Template Py Cli`   |
| `{hostname}` | System hostname              | System hostname              |

### Concrete Examples

**Linux:**
- User config: `~/.config/bitranox-template-py-cli/config.toml`
- App config: `/etc/xdg/bitranox-template-py-cli/config.toml`
- Host config: `/etc/xdg/bitranox-template-py-cli/hosts/myserver.toml`

**macOS:**
- User config: `~/Library/Application Support/bitranox/Bitranox Template Py Cli/config.toml`

**Windows:**
- User config: `%APPDATA%\bitranox\Bitranox Template Py Cli\config.toml`

---

## CLI Commands

### View Configuration

```bash
# Show merged configuration from all sources
bitranox-template-py-cli config

# Output as JSON (useful for scripting)
bitranox-template-py-cli config --format json

# Show specific section only
bitranox-template-py-cli config --section lib_log_rich

# Load configuration for a specific profile
bitranox-template-py-cli config --profile production

# Combine options
bitranox-template-py-cli config --profile staging --format json --section email
```

### Deploy Configuration Files

```bash
# Create user configuration file
bitranox-template-py-cli config-deploy --target user

# Deploy to system-wide location (requires privileges)
sudo bitranox-template-py-cli config-deploy --target app

# Deploy host-specific configuration
bitranox-template-py-cli config-deploy --target host

# Deploy to multiple locations at once
bitranox-template-py-cli config-deploy --target user --target host

# Overwrite existing configuration
bitranox-template-py-cli config-deploy --target user --force

# Deploy to a specific profile directory
bitranox-template-py-cli config-deploy --target user --profile production

# Deploy production profile and overwrite if exists
bitranox-template-py-cli config-deploy --target user --profile production --force
```

### Generate Example Configuration Files

Create example TOML files showing all available options with default values and documentation comments:

```bash
# Generate examples in a specific directory
bitranox-template-py-cli config-generate-examples --destination ./examples

# Overwrite existing example files
bitranox-template-py-cli config-generate-examples --destination ./examples --force

# Generate examples in current directory
bitranox-template-py-cli config-generate-examples --destination .
```

Generated files include:
- `config.toml` — Main configuration file with all sections
- `config.d/*.toml` — Modular configuration files (email, logging, etc.)

Each file contains commented documentation explaining available options and their default values.

### Runtime Overrides

Use `--set` to override configuration values without modifying files (repeatable):

```bash
bitranox-template-py-cli --set lib_log_rich.console_level=DEBUG config
bitranox-template-py-cli --set email.smtp_hosts='["smtp.example.com:587"]' config
```

---

## Profiles

Profiles provide isolated configuration namespaces for different environments (e.g., `production`, `staging`, `test`).

### Profile Name Requirements

Profile names are validated for security and cross-platform compatibility:

| Rule | Description |
|------|-------------|
| **Maximum length** | 64 characters |
| **Allowed characters** | ASCII letters (`a-z`, `A-Z`), digits (`0-9`), hyphens (`-`), underscores (`_`) |
| **Start character** | Must start with a letter or digit (not `-` or `_`) |
| **Reserved names** | Windows reserved names rejected: `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9` |
| **Path safety** | No path separators (`/`, `\`) or traversal sequences (`..`) |

**Valid examples:** `production`, `staging-v2`, `test_env`, `dev01`

**Invalid examples:** `../etc` (path traversal), `-invalid` (starts with hyphen), `CON` (Windows reserved)

### Which Layers Are Affected?

| Layer    | Affected by Profile? | Notes                               |
|----------|:--------------------:|-------------------------------------|
| defaults | No                   | Always loaded from package          |
| app      | Yes                  | Uses `profile/<name>/` subdirectory |
| host     | Yes                  | Uses `profile/<name>/` subdirectory |
| user     | Yes                  | Uses `profile/<name>/` subdirectory |
| .env     | No                   | Project directory                   |
| env vars | No                   | Environment                         |
| CLI      | No                   | Command line                        |

### Profile Path Examples

**Without profile:**
- `~/.config/bitranox-template-py-cli/config.toml`

**With profile `production`:**
- `~/.config/bitranox-template-py-cli/profile/production/config.toml`

### Reading Behavior

Profile directories are **separate namespaces**. Configuration deployed with a profile is only visible when reading with that same profile.

| Command                         | Sees `app` layer?                  | Sees `user` layer?                 |
|---------------------------------|------------------------------------|------------------------------------|
| `config` (no profile)           | Only if deployed without profile   | Only if deployed without profile   |
| `config --profile production`   | Only if deployed with `production` | Only if deployed with `production` |

**Example**: If you deploy `app` with `--profile production` but `user` without a profile:

| Command                       | app layer | user layer |
|-------------------------------|:---------:|:----------:|
| `config`                      | No        | Yes        |
| `config --profile production` | Yes       | No         |

---

## Environment Variables

Configuration can be overridden via environment variables using two methods:

### Method 1: Native lib_log_rich Variables

For logging configuration, use the native `LOG_*` variables (highest precedence):

```bash
LOG_CONSOLE_LEVEL=DEBUG bitranox-template-py-cli hello
LOG_ENABLE_GRAYLOG=true LOG_GRAYLOG_ENDPOINT="logs.example.com:12201" bitranox-template-py-cli hello
```

### Method 2: Application-Prefixed Variables

For any configuration section, use the format: `<PREFIX>___<SECTION>__<KEY>=value`

```bash
BITRANOX_TEMPLATE_PY_CLI___LIB_LOG_RICH__CONSOLE_LEVEL=DEBUG bitranox-template-py-cli hello
BITRANOX_TEMPLATE_PY_CLI___EMAIL__SMTP_HOSTS='["smtp.example.com:587"]' bitranox-template-py-cli hello
```

**Separator reference:**
- `___` (triple underscore) — separates prefix from section
- `__` (double underscore) — separates section from key

---

## .env File Support

Create a `.env` file in your project directory for local development overrides:

```bash
# .env
LOG_CONSOLE_LEVEL=DEBUG
LOG_CONSOLE_FORMAT_PRESET=short
LOG_ENABLE_GRAYLOG=false
```

The application automatically discovers and loads `.env` files from the current directory or parent directories.

---

## Default Configuration

The `defaultconfig.toml` and files in `defaultconfig.d/` (bundled with the package) provide baseline values. These serve as the fallback when no external configuration files are deployed.

---

## Customization Best Practices

**Do NOT modify deployed configuration files directly.** These files may be overwritten during package updates.

Instead, create your own override files in the appropriate layer directory using a high-numbered prefix:

```bash
# User-level customization (Linux)
~/.config/bitranox-template-py-cli/999-myconfig.toml

# User-level customization (macOS)
~/Library/Application Support/bitranox/Bitranox Template Py Cli/999-myconfig.toml

# User-level customization (Windows)
%APPDATA%\bitranox\Bitranox Template Py Cli\999-myconfig.toml

# System-wide customization (Linux)
/etc/xdg/bitranox-template-py-cli/999-myconfig.toml
```

**Why this works:**
- Files in each layer directory are loaded in alphabetical order
- Higher-numbered files (e.g., `999-`) load last and override earlier values
- Your custom file won't be touched by updates that regenerate `config.toml`

**Example `999-myconfig.toml`:**

```toml
# My custom overrides - survives package updates

[lib_log_rich]
console_level = "DEBUG"

[email]
smtp_hosts = ["smtp.mycompany.com:587"]
```

This approach keeps your customizations separate and safe from updates while still benefiting from new default values added in future versions.

---

## Library Use

You can import the configuration system directly in Python:

```python
import bitranox_template_py_cli as btcli

# Get the merged configuration object
config = btcli.get_config()
print(config.as_dict())

# Access specific sections
log_config = config.get("lib_log_rich", default={})
email_config = config.get("email", default={})
```
