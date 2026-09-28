"""Load the layered configuration for the CLI, and refuse a command that needs a broken one.

The root group loads the configuration before any subcommand's options are parsed, so it
cannot report a failure the way the subcommand would, and it must not block a command that
never reads the configuration: ``config-deploy`` is how a broken file gets replaced, and
``info`` or ``--help`` have to keep working meanwhile. The root therefore records the
failure, and each command that reads the configuration asks for it through
:func:`require_config`.

Contents:
    * :func:`load_config` - load with profile, ``.env`` and ``--set``, or say why not.
    * :func:`require_config` - the configuration, or exit 78 naming the failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from lib_layered_config import Config, ConfigError

from bitranox_template_py_cli.adapters.config.overrides import apply_overrides

from . import safe_console
from .exit_codes import ExitCode

if TYPE_CHECKING:
    from bitranox_template_py_cli.composition import AppServices

    from .context import CLIContext

#: Every way loading can fail: a broken or invalid file (ConfigError), a profile name the
#: loader rejects (ValueError), and a file the running user cannot read (OSError).
_LOAD_ERRORS = (ConfigError, ValueError, OSError)


def load_config(
    services: AppServices, *, profile: str | None, env_file: str | None, set_overrides: tuple[str, ...]
) -> tuple[Config, str]:
    """Load the layered configuration, or say why it could not be loaded.

    Args:
        services: The composition's services; only ``get_config`` is used.
        profile: The profile to load, or None for none.
        env_file: An explicit ``.env`` file, or None to search for one.
        set_overrides: The ``--set`` values, applied only to a configuration that loaded.

    Returns:
        The configuration and ``""``, or an empty configuration and the reason it failed.

    Raises:
        click.UsageError: A ``--set`` value is malformed; that is a command-line error
            (exit 2), not a configuration one.

    Example:
        >>> from bitranox_template_py_cli.composition import build_testing
        >>> config, error = load_config(build_testing(), profile=None, env_file=None, set_overrides=("a.b=1",))
        >>> config.get("a"), error
        ({'b': 1}, '')
    """
    try:
        config = services.get_config(profile=profile, dotenv_path=env_file)
    except _LOAD_ERRORS as exc:
        return Config({}, {}), str(exc)
    try:
        return apply_overrides(config, set_overrides), ""
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


def require_config(ctx: click.Context, cli_ctx: CLIContext) -> Config:
    """Return the configuration the root loaded, or end the command with exit 78.

    Args:
        ctx: The running command's click context.
        cli_ctx: The state the root group stored.

    Returns:
        The loaded configuration.

    Raises:
        click.exceptions.Exit: The configuration could not be loaded; one stderr line names
            the reason.
    """
    if cli_ctx.config_error:
        safe_console.echo(f"Error: {cli_ctx.config_error}", err=True)
        ctx.exit(ExitCode.CONFIG_ERROR)
    return cli_ctx.config


__all__ = ["load_config", "require_config"]
