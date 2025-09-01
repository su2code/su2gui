
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the current directory to the path to import installer modules
sys.path.insert(0, str(Path(__file__).parent))

from installer import install as installer_install, uninstall as installer_uninstall
from installer.constants import InstallMode, SU2_RELEASE
from installer.detect import (
    detect_installation_capabilities,
    get_system_info,
    get_default_prefix
)
from installer.env import validate_env
from installer.conda import check_conda_installation


def print_banner():
    """Print the SU2 installation banner."""
    print("=" * 60)
    print(" SU2 Installation Tool")
    print(f"   Version: {SU2_RELEASE}")
    print("=" * 60)


def show_system_info():
    """Show system information and installation capabilities."""
    print_banner()
    print("\n System Information:")
    print("-" * 40)
    
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n Installation Capabilities:")
    print("-" * 40)
    
    capabilities = detect_installation_capabilities()
    for method, available in capabilities.items():
        status = "correct" if available else "wrong"
        print(f"  {status} {method.title()}")
        
        # Add helpful notes
        if method == "binaries" and not available:
            print("      Pre-compiled binaries not available for this platform")
        elif method == "conda" and not available:
            print("      Conda not found in PATH")
        elif method == "source" and not available:
            print("      Build tools (cmake, compiler) not available")
    
    print("\n Conda Information:")
    print("-" * 40)
    
    conda_info = check_conda_installation()
    for key, value in conda_info.items():
        status = "correct" if value else "wrong"
        key_formatted = key.replace('_', ' ').title()
        print(f"  {status} {key_formatted}")


def validate_installation(prefix: Optional[Path] = None):
    """Validate SU2 installation."""
    if prefix is None:
        prefix = get_default_prefix()
    
    print_banner()
    print(f"\n Validating SU2 installation at: {prefix}")
    print("-" * 40)
    
    if not prefix.exists():
        print(f" Installation directory {prefix} does not exist")
        print("   Run installation first, then validate")
        return False
    
    try:
        results = validate_env(prefix)
        
        # Filter out informational checks for the main summary
        main_checks = {k: v for k, v in results.items() if not k.endswith('_actually_exists')}
        info_checks = {k: v for k, v in results.items() if k.endswith('_actually_exists')}
        
        print("\n Validation Results:")
        for check, passed in main_checks.items():
            status = " " if passed else " "
            check_name = check.replace('_', ' ').title()
            print(f"  {status} {check_name}")
        
        # Show additional info if any
        if info_checks:
            print("\n Additional Information:")
            for check, passed in info_checks.items():
                status = "correct" if passed else "error"
                check_name = check.replace('_actually_exists', '').replace('_', ' ').title()
                note = "(optional component)"
                print(f"  {status} {check_name} {note}")
        
        passed_checks = sum(1 for passed in main_checks.values() if passed)
        total_checks = len(main_checks)
        
        print(f"\n Summary: {passed_checks}/{total_checks} essential checks passed")
        
        if passed_checks == total_checks:
            print(" SU2 installation validation passed!")
            return True
        else:
            failed_checks = [check for check, passed in main_checks.items() if not passed]
            print(f"Failed checks: {', '.join(failed_checks)}")
            return False
            
    except Exception as e:
        print(f"Validation failed: {e}")
        return False


def install_su2(
    mode: str = InstallMode.BIN,
    prefix: Optional[Path] = None,
    pywrapper: bool = False,
    mpi: bool = False,
    autodiff: bool = False,
    jobs: int = 4,
    dry_run: bool = False
):
    """Install SU2 with the specified options."""
    print_banner()
    
    # Set defaults
    if prefix is None:
        prefix = get_default_prefix()
    
    # Show installation plan
    print(f"\n Installation Plan:")
    print("-" * 40)
    print(f"  Mode: {mode}")
    print(f"  Version: {SU2_RELEASE}")
    print(f"  Install Path: {prefix}")
    
    if mode == InstallMode.SRC:
        print(f"  Python Wrapper: {'Yes' if pywrapper else 'No'}")
        print(f"  MPI Support: {'Yes' if mpi else 'No'}")
        print(f"  Autodiff: {'Yes' if autodiff else 'No'}")
        print(f"  Build Jobs: {jobs}")
    
    if dry_run:
        print("\n  Dry run mode - no changes will be made.")
        return True
    
    # Check capabilities
    capabilities = detect_installation_capabilities()
    
    if mode == InstallMode.BIN and not capabilities["binaries"]:
        print("Error: Binary installation not available for this platform.")
        print("   Try --mode conda or --mode source instead.")
        return False
    
    if mode == InstallMode.CONDA and not capabilities["conda"]:
        print(" Error: Conda not available.")
        print("   Install conda/miniconda or try --mode binaries instead.")
        return False
    
    if mode == InstallMode.SRC and not capabilities["source"]:
        print("Error: Source build dependencies not available.")
        print("   Install cmake and a C++ compiler, or try --mode binaries instead.")
        return False
    
    # Perform installation
    try:
        print("\n Starting installation...")
        print("-" * 40)
        
        installer_install(
            mode=mode,
            prefix=prefix,
            enable_pywrapper=pywrapper,
            enable_mpi=mpi,
            enable_autodiff=autodiff,
            jobs=jobs
        )
        
        print("\n Installation completed successfully!")
        
        # Automatically validate the installation
        print("\n Running post-installation validation...")
        validation_success = validate_installation(prefix)
        
        if validation_success:
            print("\n SU2 is ready to use!")
            print(f"   Installation location: {prefix}")
            
            # Show quick usage info
            bin_dir = prefix / "bin"
            if bin_dir.exists():
                print(f"   Executables location: {bin_dir}")
                print("   Add to PATH or use full paths to run SU2 commands")
        else:
            print("\n Installation completed but validation failed.")
            print("   Some components may not be working correctly.")
        
        return validation_success
        
    except Exception as e:
        print(f"\n Installation failed: {e}")
        return False


def uninstall_su2(prefix: Optional[Path] = None, remove_env: bool = False):
    """Uninstall SU2."""
    if prefix is None:
        prefix = get_default_prefix()
    
    print_banner()
    print(f"\n Uninstalling SU2 from: {prefix}")
    print("-" * 40)
    
    # Confirmation
    response = input("Are you sure you want to uninstall SU2? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Uninstallation cancelled.")
        return True
    
    try:
        import shutil
        
        # Remove installation directory
        if prefix.exists():
            shutil.rmtree(prefix)
            print(f"Removed installation directory: {prefix}")
        else:
            print(f" Installation directory not found: {prefix}")
        
        # Remove environment variables
        if remove_env:
            from installer.env import remove_env as remove_env_vars
            if remove_env_vars():
                print("Removed environment variables")
            else:
                print("  No environment variables found to remove")
        
        print("\n Uninstallation completed!")
        return True
        
    except Exception as e:
        print(f"\n Uninstallation failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Standalone SU2 Installation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
     
"""
    )
    
    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--install", 
        action="store_true", 
        default=True,
        help="Install SU2 (default action)"
    )
    action_group.add_argument(
        "--validate", 
        action="store_true",
        help="Validate existing SU2 installation"
    )
    action_group.add_argument(
        "--info", 
        action="store_true",
        help="Show system information and capabilities"
    )
    action_group.add_argument(
        "--uninstall", 
        action="store_true",
        help="Uninstall SU2"
    )
    
    # Installation options
    parser.add_argument(
        "--mode",
        choices=[InstallMode.BIN, InstallMode.SRC, InstallMode.CONDA],
        default=InstallMode.BIN,
        help="Installation mode (default: binaries)"
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        help="Installation directory (default: auto-detected)"
    )
    parser.add_argument(
        "--pywrapper",
        action="store_true",
        help="Enable Python wrapper (source build only)"
    )
    parser.add_argument(
        "--mpi",
        action="store_true",
        help="Enable MPI support (source build only)"
    )
    parser.add_argument(
        "--autodiff",
        action="store_true",
        help="Enable automatic differentiation (source build only)"
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=None,
        help="Number of parallel build jobs (default: auto-detect)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually installing"
    )
    parser.add_argument(
        "--remove-env",
        action="store_true",
        help="Also remove environment variables when uninstalling"
    )
    
    args = parser.parse_args()
    
    # Set default jobs if not specified
    if args.jobs is None:
        import os
        args.jobs = os.cpu_count() or 4
    
    # Handle special case where no action is explicitly set but other args suggest install
    if not any([args.validate, args.info, args.uninstall]):
        args.install = True
    
    # Execute the requested action
    success = True
    
    try:
        if args.info:
            show_system_info()
            
        elif args.validate:
            success = validate_installation(args.prefix)
            
        elif args.uninstall:
            success = uninstall_su2(args.prefix, args.remove_env)
            
        elif args.install:
            success = install_su2(
                mode=args.mode,
                prefix=args.prefix,
                pywrapper=args.pywrapper,
                mpi=args.mpi,
                autodiff=args.autodiff,
                jobs=args.jobs,
                dry_run=args.dry_run
            )
    
    except KeyboardInterrupt:
        print("\n\n Operation cancelled by user.")
        success = False
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        success = False
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
