"""Configuration display and deployment CLI commands.

Provides commands to inspect, deploy, and generate example configuration.

Contents:
    * :func:`cli_config` - Display merged configuration.
    * :func:`cli_config_deploy` - Deploy configuration to target locations.
    * :func:`cli_config_generate_examples` - Generate example configuration files.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import click.exceptions as click_exceptions
import lib_log_rich.runtime
import rich_click as click
from lib_layered_config import Config, generate_examples

from bitranox_template_py_cli import __init__conf__
from bitranox_template_py_cli.adapters.config.permissions import (
    check_deploy_mode,
    get_modes_for_target,
    get_permission_defaults,
    parse_octal_mode_string,
)
from bitranox_template_py_cli.domain.enums import DeployTarget, OutputFormat
from bitranox_template_py_cli.domain.errors import ConfigurationError

from .. import safe_console
from ..config_load import load_config, require_config
from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import CLIContext, get_cli_context
from ..exit_codes import ExitCode
from ..typed_click import get_current_context, option

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@click.command("config", context_settings=CLICK_CONTEXT_SETTINGS)
@option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.HUMAN.value,
    help="Output format (human-readable or JSON)",
)
@option(
    "--section",
    type=str,
    default=None,
    help="Show only a specific configuration section (e.g., 'lib_log_rich')",
)
@option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@click.pass_context
def cli_config(ctx: click.Context, output_format: str, section: str | None, profile: str | None) -> None:
    """Display the current merged configuration from all sources.

    Shows configuration loaded from defaults, application/user config files,
    .env files, and environment variables.

    Precedence: defaults -> app -> host -> user -> dotenv -> env

    Example:
        >>> from click.testing import CliRunner
        >>> from unittest.mock import MagicMock
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli_config.py
    """
    cli_ctx = get_cli_context(ctx)
    effective_config, effective_profile = _resolve_config(ctx, cli_ctx, profile)
    fmt = OutputFormat(output_format.lower())

    extra = {"command": "config", "format": fmt.value, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config", extra=extra):
        logger.info(
            "Displaying configuration",
            extra={"format": fmt.value, "section": section, "profile": effective_profile},
        )
        safe_console.echo()
        try:
            cli_ctx.services.display_config(
                effective_config, output_format=fmt, section=section, profile=effective_profile
            )
        except ValueError as exc:
            safe_console.echo(f"\nError: {exc}", err=True)
            ctx.exit(ExitCode.INVALID_ARGUMENT)


def _get_effective_profile(cli_ctx: CLIContext, profile_override: str | None) -> str | None:
    """Get effective profile: override takes precedence over context."""
    return profile_override if profile_override else cli_ctx.profile


def _resolve_config(ctx: click.Context, cli_ctx: CLIContext, profile: str | None) -> tuple[Config, str | None]:
    """Resolve configuration from context or reload with profile override.

    When a subcommand-level profile override is specified, reloads config
    with that profile, the root's ``--env-file`` and any root-level ``--set``
    overrides stored in the CLI context.

    Args:
        ctx: The running command's click context, exited with 78 when loading failed.
        cli_ctx: CLI context containing stored config and services.
        profile: Optional profile override.

    Returns:
        Tuple of (config, effective_profile).
    """
    effective_profile = _get_effective_profile(cli_ctx, profile)
    if not profile:
        return require_config(ctx, cli_ctx), effective_profile
    config, error = load_config(
        cli_ctx.services, profile=profile, env_file=cli_ctx.env_file, set_overrides=cli_ctx.set_overrides
    )
    if error:
        safe_console.echo(f"Error: {error}", err=True)
        ctx.exit(ExitCode.CONFIG_ERROR)
    return config, effective_profile


def _parse_deploy_mode(value: str | None, *, is_directory: bool) -> int | None:
    """Parse an octal mode string (``750`` or ``0o750``) and refuse an unsafe one.

    Args:
        value: Octal mode string from the CLI, or None when the option was not given.
        is_directory: Whether the value is ``--dir-mode`` or ``--file-mode``.

    Returns:
        The permission mode, or None if value was None.

    Raises:
        click.BadParameter: The value is not a plain octal literal, lies outside 0..0o7777
            (either would reach ``chmod`` as unintended bits or an ``OverflowError``), or is
            unsafe for configuration that can hold secrets (see ``check_deploy_mode``).
    """
    if value is None:
        return None
    try:
        mode = parse_octal_mode_string(value)
        check_deploy_mode(mode, is_directory=is_directory)
    except ValueError as exc:
        raise click.BadParameter(str(exc)) from exc
    return mode


def _parse_dir_mode(_ctx: click.Context, _param: click.Parameter, value: str | None) -> int | None:
    """The ``--dir-mode`` callback; see :func:`_parse_deploy_mode`."""
    return _parse_deploy_mode(value, is_directory=True)


def _parse_file_mode(_ctx: click.Context, _param: click.Parameter, value: str | None) -> int | None:
    """The ``--file-mode`` callback; see :func:`_parse_deploy_mode`."""
    return _parse_deploy_mode(value, is_directory=False)


@click.command("config-deploy", context_settings=CLICK_CONTEXT_SETTINGS)
@option(
    "--target",
    "targets",
    type=click.Choice([t.value for t in DeployTarget], case_sensitive=False),
    multiple=True,
    required=True,
    help="Target configuration layer(s) to deploy to (can specify multiple)",
)
@option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing configuration files",
)
@option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@option(
    "--permissions/--no-permissions",
    "set_permissions",
    default=None,
    help="Set Unix permissions (755/644 for app/host, 700/600 for user). Default: enabled.",
)
@option(
    "--dir-mode",
    type=str,
    default=None,
    callback=_parse_dir_mode,
    help="Override directory mode (octal, e.g., 750 or 0o750)",
)
@option(
    "--file-mode",
    type=str,
    default=None,
    callback=_parse_file_mode,
    help="Override file mode (octal, e.g., 640 or 0o640)",
)
@click.pass_context
def cli_config_deploy(
    ctx: click.Context,
    *,
    targets: tuple[str, ...],
    force: bool,
    profile: str | None,
    set_permissions: bool | None,
    dir_mode: int | None,
    file_mode: int | None,
) -> None:
    r"""Deploy default configuration to system or user directories.

    Creates configuration files in platform-specific locations:

    \b
    - app:  System-wide application config (requires privileges)
    - host: System-wide host config (requires privileges)
    - user: User-specific config (~/.config on Linux)

    By default, existing files are not overwritten. Use --force to overwrite.

    \b
    Permission options (POSIX only, no-op on Windows):
    - --permissions/--no-permissions: Enable/disable permission setting
    - --dir-mode: Override directory mode (octal, e.g., 750)
    - --file-mode: Override file mode (octal, e.g., 640)

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli_config.py
    """
    cli_ctx = get_cli_context(ctx)
    if cli_ctx.config_error:
        # Deploying is how a broken configuration gets replaced, so it runs anyway, with the
        # permission defaults of an empty configuration; the user is told which file was skipped.
        safe_console.echo(
            f"Warning: configuration not loaded, using default permissions: {cli_ctx.config_error}", err=True
        )
    effective_profile = _get_effective_profile(cli_ctx, profile)
    deploy_targets = tuple(DeployTarget(t.lower()) for t in targets)
    target_values = tuple(t.value for t in deploy_targets)

    extra = {"command": "config-deploy", "targets": target_values, "force": force, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config-deploy", extra=extra):
        logger.info(
            "Deploying configuration",
            extra={"targets": target_values, "force": force, "profile": effective_profile},
        )
        _execute_deploy(
            cli_ctx,
            targets=deploy_targets,
            force=force,
            profile=effective_profile,
            set_permissions=set_permissions,
            dir_mode=dir_mode,
            file_mode=file_mode,
        )


def _execute_deploy(
    cli_ctx: CLIContext,
    *,
    targets: tuple[DeployTarget, ...],
    force: bool,
    profile: str | None,
    set_permissions: bool | None,
    dir_mode: int | None,
    file_mode: int | None,
) -> None:
    """Execute configuration deployment with error handling.

    Args:
        cli_ctx: CLI context containing services.
        targets: Deployment target layers.
        force: Whether to overwrite existing files.
        profile: Optional profile name.
        set_permissions: Whether to set Unix permissions. None uses config default.
        dir_mode: Directory mode for every target; None uses each target's configured mode.
        file_mode: File mode for every target; None uses each target's configured mode.

    Raises:
        click.exceptions.Exit: On invalid permission settings (78), a permission error or any
            other failure, raised through ``ctx.exit`` so ``main()`` returns the code instead of
            printing a bare ``SystemExit``.
    """
    try:
        perm_defaults = get_permission_defaults(cli_ctx.config)
    except ConfigurationError as exc:
        # A bad permission setting is a configuration error, not a deploy failure: it gets its
        # own exit code and one line naming the key, and nothing is deployed.
        safe_console.echo(f"Error: Invalid configuration: {exc}", err=True)
        get_current_context().exit(ExitCode.CONFIG_ERROR)

    # CLI --permissions/--no-permissions overrides config enabled setting
    effective_set_permissions = set_permissions if set_permissions is not None else perm_defaults.enabled

    try:
        deployed_paths: list[Path] = []
        for target in targets:
            # One call per target: the configured modes differ per layer, while the deploy
            # port takes one directory and one file mode for all the targets it is given.
            target_dir_mode, target_file_mode = get_modes_for_target(
                target, cli_ctx.config, dir_mode_override=dir_mode, file_mode_override=file_mode
            )
            deployed_paths += cli_ctx.services.deploy_configuration(
                targets=(target,),
                force=force,
                profile=profile,
                set_permissions=effective_set_permissions,
                dir_mode=target_dir_mode,
                file_mode=target_file_mode,
            )
        _report_deployment_result(deployed_paths, profile, effective_set_permissions)
    except PermissionError as exc:
        logger.error("Permission denied when deploying configuration", extra={"error": str(exc)})
        safe_console.echo(f"\nError: Permission denied. {exc}", err=True)
        safe_console.echo("Hint: System-wide deployment (--target app/host) may require sudo.", err=True)
        get_current_context().exit(ExitCode.PERMISSION_DENIED)
    except click_exceptions.Exit:
        # click's Exit subclasses RuntimeError. It is a deliberate exit with its own code,
        # not a deploy failure, so it must not be relabelled GENERAL_ERROR by the branch below.
        raise
    except Exception as exc:
        logger.error("Failed to deploy configuration", extra={"error": str(exc), "error_type": type(exc).__name__})
        safe_console.echo(f"\nError: Failed to deploy configuration: {exc}", err=True)
        get_current_context().exit(ExitCode.GENERAL_ERROR)


def _report_deployment_result(deployed_paths: list[Path], profile: str | None, set_permissions: bool) -> None:
    """Report deployment results to the user.

    Args:
        deployed_paths: List of paths where configs were deployed.
        profile: Optional profile name for display.
        set_permissions: Whether permissions were set.
    """
    if deployed_paths:
        profile_msg = f" (profile: {profile})" if profile else ""
        perm_msg = "" if set_permissions else " (permissions not set)"
        safe_console.echo(f"\nConfiguration deployed successfully{profile_msg}{perm_msg}:")
        for path in deployed_paths:
            # ASCII marker on purpose: a non-ASCII glyph here crashes config-deploy with a
            # UnicodeEncodeError on a legacy Windows console codepage (cp1252) even though the
            # files were already written, so exit 1 misreports a deploy that actually succeeded.
            safe_console.echo(f"  + {path}")
    else:
        safe_console.echo("\nNo files were created (all target files already exist).")
        safe_console.echo("Use --force to overwrite existing configuration files.")


@click.command("config-generate-examples", context_settings=CLICK_CONTEXT_SETTINGS)
@option("--destination", type=click.Path(file_okay=False), required=True, help="Directory to write example files")
@option("--force", is_flag=True, default=False, help="Overwrite existing files")
@click.pass_context
def cli_config_generate_examples(ctx: click.Context, destination: str, force: bool) -> None:
    """Generate example configuration files in a target directory.

    Creates example TOML configuration files showing all available options
    with their default values and documentation comments. Useful for learning
    the configuration structure, creating initial configuration files, or
    documenting available settings.

    By default, existing files are not overwritten. Use --force to overwrite.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli_config.py
    """
    extra = {"command": "config-generate-examples", "destination": destination, "force": force}
    with lib_log_rich.runtime.bind(job_id="cli-config-generate-examples", extra=extra):
        logger.info("Generating example configuration files", extra={"destination": destination, "force": force})
        try:
            paths = generate_examples(
                destination=destination,
                slug=__init__conf__.LAYEREDCONF_SLUG,
                vendor=__init__conf__.LAYEREDCONF_VENDOR,
                app=__init__conf__.LAYEREDCONF_APP,
                force=force,
            )
            if paths:
                safe_console.echo(f"\nGenerated {len(paths)} example file(s):")
                for p in paths:
                    safe_console.echo(f"  {p}")
            else:
                safe_console.echo("\nNo files generated (all already exist). Use --force to overwrite.")
        except Exception as exc:
            logger.error("Failed to generate examples", extra={"error": str(exc)})
            safe_console.echo(f"\nError: {exc}", err=True)
            ctx.exit(ExitCode.GENERAL_ERROR)


__all__ = ["cli_config", "cli_config_deploy", "cli_config_generate_examples"]
