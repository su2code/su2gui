"""
Command-line interface for SU2GUI installer
"""
import click
import sys
from pathlib import Path
from typing import Optional

from .installer import install as installer_install
from .installer.constants import InstallMode, SU2_RELEASE
from .installer.detect import (
    detect_installation_capabilities,
    get_system_info,
    get_default_prefix
)
from .installer.conda import check_conda_installation


@click.group()
def su2gui():
    """SU2GUI - Graphical User Interface for SU2."""
    pass


@su2gui.command()
@click.option(
    "--mode", 
    type=click.Choice([InstallMode.BIN, InstallMode.SRC, InstallMode.CONDA]),
    default=InstallMode.BIN,
    help="Installation mode"
)
@click.option(
    "--prefix",
    type=click.Path(path_type=Path),
    help="Installation prefix directory"
)
@click.option(
    "--pywrapper/--no-pywrapper",
    default=False,
    help="Enable Python wrapper (source build only)"
)
@click.option(
    "--mpi/--no-mpi",
    default=False,
    help="Enable MPI support (source build only)"
)
@click.option(
    "--autodiff/--no-autodiff",
    default=False,
    help="Enable automatic differentiation (source build only)"
)
@click.option(
    "-j", "--jobs",
    type=int,
    default=None,
    help="Number of parallel build jobs"
)
@click.option(
    "--clean",
    is_flag=True,
    help="Clean build directory before building (source build only)"
)
@click.option(
    "--version",
    default=SU2_RELEASE,
    help="SU2 version to install"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually installing"
)
def install(
    mode: str,
    prefix: Optional[Path],
    pywrapper: bool,
    mpi: bool,
    autodiff: bool,
    jobs: Optional[int],
    clean: bool,
    version: str,
    dry_run: bool
):
    """Install or update SU2."""
    
    # Set defaults
    if prefix is None:
        prefix = get_default_prefix()
    
    if jobs is None:
        import os
        jobs = os.cpu_count() or 4
    
    # Show installation plan
    click.echo(f"SU2 Installation Plan:")
    click.echo(f"  Mode: {mode}")
    click.echo(f"  Version: {version}")
    click.echo(f"  Prefix: {prefix}")
    
    if mode == InstallMode.SRC:
        click.echo(f"  Python wrapper: {pywrapper}")
        click.echo(f"  MPI support: {mpi}")
        click.echo(f"  Autodiff: {autodiff}")
        click.echo(f"  Build jobs: {jobs}")
        click.echo(f"  Clean build: {clean}")
    
    if dry_run:
        click.echo("\nDry run mode - no changes will be made.")
        return
    
    # Check capabilities
    capabilities = detect_installation_capabilities()
    
    if mode == InstallMode.BIN and not capabilities["binaries"]:
        click.echo("Error: Binary installation not available for this platform.", err=True)
        sys.exit(1)
    
    if mode == InstallMode.CONDA and not capabilities["conda"]:
        click.echo("Error: Conda not available.", err=True)
        sys.exit(1)
    
    if mode == InstallMode.SRC and not capabilities["source"]:
        click.echo("Error: Source build dependencies not available.", err=True)
        sys.exit(1)
    
    # Perform installation
    try:
        click.echo("\nStarting installation...")
        
        installer_install(
            mode=mode,
            prefix=prefix,
            enable_pywrapper=pywrapper,
            enable_mpi=mpi,
            enable_autodiff=autodiff,
            jobs=jobs
        )
        
        click.echo(" Installation completed successfully!")
        
    except Exception as e:
        click.echo(f" Installation failed: {e}", err=True)
        sys.exit(1)


@su2gui.command()
def info():
    """Show system information and installation capabilities."""
    
    click.echo("System Information:")
    click.echo("=" * 50)
    
    info = get_system_info()
    for key, value in info.items():
        click.echo(f"  {key.replace('_', ' ').title()}: {value}")
    
    click.echo("\nInstallation Capabilities:")
    click.echo("=" * 50)
    
    capabilities = detect_installation_capabilities()
    for method, available in capabilities.items():
        status = "" if available else ""
        click.echo(f"  {status} {method.title()}")
    
    click.echo("\nConda Information:")
    click.echo("=" * 50)
    
    conda_info = check_conda_installation()
    for key, value in conda_info.items():
        status = "" if value else ""
        click.echo(f"  {status} {key.replace('_', ' ').title()}")


@su2gui.command()
@click.option(
    "--prefix",
    type=click.Path(path_type=Path),
    help="Installation prefix to validate"
)
def validate(prefix: Optional[Path]):
    """Validate SU2 installation."""
    
    if prefix is None:
        prefix = get_default_prefix()
    
    click.echo(f"Validating SU2 installation at: {prefix}")
    
    from .installer.env import validate_env
    
    try:
        results = validate_env(prefix)
        
        click.echo("\nValidation Results:")
        click.echo("=" * 50)
        
        for check, passed in results.items():
            status = "" if passed else ""
            click.echo(f"  {status} {check.replace('_', ' ').title()}")
        
        all_passed = all(results.values())
        
        if all_passed:
            click.echo("\n Installation validation passed!")
        else:
            click.echo("\n Installation validation failed!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f" Validation failed: {e}", err=True)
        sys.exit(1)


@su2gui.command()
@click.option(
    "--prefix",
    type=click.Path(path_type=Path),
    help="Installation prefix to clean"
)
@click.option(
    "--env",
    is_flag=True,
    help="Also clean environment variables"
)
@click.confirmation_option(
    prompt="Are you sure you want to uninstall SU2?"
)
def uninstall(prefix: Optional[Path], env: bool):
    """Uninstall SU2."""
    
    if prefix is None:
        prefix = get_default_prefix()
    
    try:
        import shutil
        
        # Remove installation directory
        if prefix.exists():
            shutil.rmtree(prefix)
            click.echo(f" Removed installation directory: {prefix}")
        else:
            click.echo(f"Installation directory not found: {prefix}")
        
        # Remove environment variables
        if env:
            from .installer.env import remove_env
            if remove_env():
                click.echo(" Removed environment variables")
            else:
                click.echo("No environment variables found to remove")
        
        click.echo(" Uninstallation completed!")
        
    except Exception as e:
        click.echo(f" Uninstallation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    su2gui()
