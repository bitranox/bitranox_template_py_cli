"""Configuration display and deployment CLI commands.

Provides commands to inspect and deploy application configuration.

Contents:
    * :func:`cli_config` - Display merged configuration.
    * :func:`cli_config_deploy` - Deploy configuration to target locations.
"""

from __future__ import annotations

import logging
from pathlib import Path

import rich_click as click
import lib_log_rich.runtime
from lib_layered_config import Config

from ....adapters.config import loader as config_module
from ....adapters.config import deploy as config_deploy_module
from ....adapters.config.display import display_config
from ....domain.enums import DeployTarget, OutputFormat
from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import get_cli_context
from ..exit_codes import ExitCode

logger = logging.getLogger(__name__)


@click.command("config", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.HUMAN.value,
    help="Output format (human-readable or JSON)",
)
@click.option(
    "--section",
    type=str,
    default=None,
    help="Show only a specific configuration section (e.g., 'lib_log_rich')",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@click.pass_context
def cli_config(ctx: click.Context, format: str, section: str | None, profile: str | None) -> None:
    """Display the current merged configuration from all sources.

    Shows configuration loaded from defaults, application/user config files,
    .env files, and environment variables.

    Precedence: defaults -> app -> host -> user -> dotenv -> env

    Example:
        >>> from click.testing import CliRunner
        >>> from unittest.mock import MagicMock
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli.py
    """
    effective_config, effective_profile = _resolve_config(ctx, profile)
    output_format = OutputFormat(format.lower())

    extra = {"command": "config", "format": output_format.value, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config", extra=extra):
        logger.info(
            "Displaying configuration",
            extra={"format": output_format.value, "section": section, "profile": effective_profile},
        )
        try:
            display_config(effective_config, format=output_format, section=section)
        except ValueError as exc:
            click.echo(f"\nError: {exc}", err=True)
            raise SystemExit(ExitCode.INVALID_ARGUMENT) from exc


def _get_effective_profile(ctx: click.Context, profile_override: str | None) -> str | None:
    """Get effective profile: override takes precedence over context."""
    return profile_override if profile_override else get_cli_context(ctx).profile


def _resolve_config(ctx: click.Context, profile: str | None) -> tuple[Config, str | None]:
    """Resolve configuration from context or reload with profile override.

    Args:
        ctx: Click context containing stored config.
        profile: Optional profile override.

    Returns:
        Tuple of (config, effective_profile).
    """
    effective_profile = _get_effective_profile(ctx, profile)
    if profile:
        return config_module.get_config(profile=profile), effective_profile
    cli_ctx = get_cli_context(ctx)
    return cli_ctx.config, effective_profile


@click.command("config-deploy", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--target",
    "targets",
    type=click.Choice([t.value for t in DeployTarget], case_sensitive=False),
    multiple=True,
    required=True,
    help="Target configuration layer(s) to deploy to (can specify multiple)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing configuration files",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@click.pass_context
def cli_config_deploy(ctx: click.Context, targets: tuple[str, ...], force: bool, profile: str | None) -> None:
    r"""Deploy default configuration to system or user directories.

    Creates configuration files in platform-specific locations:

    \b
    - app:  System-wide application config (requires privileges)
    - host: System-wide host config (requires privileges)
    - user: User-specific config (~/.config on Linux)

    By default, existing files are not overwritten. Use --force to overwrite.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli.py
    """
    effective_profile = _get_effective_profile(ctx, profile)
    deploy_targets = tuple(DeployTarget(t.lower()) for t in targets)
    target_values = tuple(t.value for t in deploy_targets)

    extra = {"command": "config-deploy", "targets": target_values, "force": force, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config-deploy", extra=extra):
        logger.info(
            "Deploying configuration",
            extra={"targets": target_values, "force": force, "profile": effective_profile},
        )
        _execute_deploy(deploy_targets, force, effective_profile)


def _execute_deploy(targets: tuple[DeployTarget, ...], force: bool, profile: str | None) -> None:
    """Execute configuration deployment with error handling.

    Args:
        targets: Deployment target layers.
        force: Whether to overwrite existing files.
        profile: Optional profile name.

    Raises:
        SystemExit: On permission or other errors.
    """
    try:
        deployed_paths = config_deploy_module.deploy_configuration(targets=targets, force=force, profile=profile)
        _report_deployment_result(deployed_paths, profile)
    except PermissionError as exc:
        logger.error("Permission denied when deploying configuration", extra={"error": str(exc)})
        click.echo(f"\nError: Permission denied. {exc}", err=True)
        click.echo("Hint: System-wide deployment (--target app/host) may require sudo.", err=True)
        raise SystemExit(ExitCode.PERMISSION_DENIED) from exc
    except Exception as exc:
        logger.error("Failed to deploy configuration", extra={"error": str(exc), "error_type": type(exc).__name__})
        click.echo(f"\nError: Failed to deploy configuration: {exc}", err=True)
        raise SystemExit(ExitCode.GENERAL_ERROR) from exc


def _report_deployment_result(deployed_paths: list[Path], profile: str | None) -> None:
    """Report deployment results to the user.

    Args:
        deployed_paths: List of paths where configs were deployed.
        profile: Optional profile name for display.
    """
    if deployed_paths:
        profile_msg = f" (profile: {profile})" if profile else ""
        click.echo(f"\nConfiguration deployed successfully{profile_msg}:")
        for path in deployed_paths:
            click.echo(f"  ✓ {path}")
    else:
        click.echo("\nNo files were created (all target files already exist).")
        click.echo("Use --force to overwrite existing configuration files.")


@click.command("config-generate-examples", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--destination", type=click.Path(file_okay=False), required=True, help="Directory to write example files")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files")
@click.pass_context
def cli_config_generate_examples(ctx: click.Context, destination: str, force: bool) -> None:
    """Generate example configuration files in a target directory."""
    from lib_layered_config import generate_examples

    from .... import __init__conf__

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
                click.echo(f"\nGenerated {len(paths)} example file(s):")
                for p in paths:
                    click.echo(f"  {p}")
            else:
                click.echo("\nNo files generated (all already exist). Use --force to overwrite.")
        except Exception as exc:
            logger.error("Failed to generate examples", extra={"error": str(exc)})
            click.echo(f"\nError: {exc}", err=True)
            raise SystemExit(ExitCode.GENERAL_ERROR) from exc


__all__ = ["cli_config", "cli_config_deploy", "cli_config_generate_examples"]
