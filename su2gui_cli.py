
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add the current directory to the path to import modules
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
    """Print the SU2GUI banner."""
    print("=" * 60)
    print(" SU2GUI - Graphical User Interface for SU2")
    print(f"   SU2 Version: {SU2_RELEASE}")
    print("=" * 60)


def show_system_info():
    """Show system information and installation capabilities."""
    print_banner()
    print("\n System Information:")
    print("-" * 40)
    
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n  Installation Capabilities:")
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
        print(f"Installation directory {prefix} does not exist")
        print("   Run 'python su2gui_cli.py install' first")
        return False
    
    try:
        results = validate_env(prefix)
        
        # Filter out informational checks for the main summary
        main_checks = {k: v for k, v in results.items() if not k.endswith('_actually_exists')}
        info_checks = {k: v for k, v in results.items() if k.endswith('_actually_exists')}
        
        print("\n Validation Results:")
        for check, passed in main_checks.items():
            status = " correct" if passed else " wrong"
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
            print("   You can now start the GUI with: python su2gui_cli.py")
            return True
        else:
            failed_checks = [check for check, passed in main_checks.items() if not passed]
            print(f" Failed checks: {', '.join(failed_checks)}")
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
        print("\n Dry run mode - no changes will be made.")
        return True
    
    # Check capabilities
    capabilities = detect_installation_capabilities()
    
    if mode == InstallMode.BIN and not capabilities["binaries"]:
        print(" Error: Binary installation not available for this platform.")
        print("   Try: python su2gui_cli.py install --mode conda")
        print("   Or:  python su2gui_cli.py install --mode source")
        return False
    
    if mode == InstallMode.CONDA and not capabilities["conda"]:
        print(" Error: Conda not available.")
        print("   Install conda/miniconda or try: python su2gui_cli.py install --mode binaries")
        return False
    
    if mode == InstallMode.SRC and not capabilities["source"]:
        print(" Error: Source build dependencies not available.")
        print("   Install cmake and a C++ compiler, or try: python su2gui_cli.py install --mode binaries")
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
            print("   Start the GUI with: python su2gui_cli.py")
            
            # Show quick usage info
            bin_dir = prefix / "bin"
            if bin_dir.exists():
                print(f"   Executables location: {bin_dir}")
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
    print(f"\n  Uninstalling SU2 from: {prefix}")
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
            print(f" Removed installation directory: {prefix}")
        else:
            print(f"  Installation directory not found: {prefix}")
        
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
    """Main CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="SU2GUI - Graphical User Interface for SU2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
                    
        """
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install SU2')
    install_parser.add_argument(
        '--mode',
        choices=[InstallMode.BIN, InstallMode.SRC, InstallMode.CONDA],
        default=InstallMode.BIN,
        help='Installation mode (default: binaries)'
    )
    install_parser.add_argument('--prefix', type=Path, help='Installation directory')
    install_parser.add_argument('--pywrapper', action='store_true', help='Enable Python wrapper (source only)')
    install_parser.add_argument('--mpi', action='store_true', help='Enable MPI support (source only)')
    install_parser.add_argument('--autodiff', action='store_true', help='Enable autodiff (source only)')
    install_parser.add_argument('-j', '--jobs', type=int, help='Number of build jobs')
    install_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate SU2 installation')
    validate_parser.add_argument('--prefix', type=Path, help='Installation directory to validate')
    
    # Info command
    subparsers.add_parser('info', help='Show system information')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall SU2')
    uninstall_parser.add_argument('--prefix', type=Path, help='Installation directory to remove')
    uninstall_parser.add_argument('--remove-env', action='store_true', help='Also remove environment variables')
    
    # GUI options (when no subcommand is used)
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port to run the server')
    parser.add_argument('-c', '--case', type=str, help='Name of case to start with')
    parser.add_argument('-m', '--mesh', type=str, help='Path to the SU2 mesh file')
    parser.add_argument('--config', type=str, help='Path to the configuration file')
    parser.add_argument('--restart', type=str, help='Path to the restart file')
    parser.add_argument('--su2', type=str, help='Path to the SU2_CFD executable')
    parser.add_argument('--clear-data', action='store_true', help='Clear all application data')
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')
    parser.add_argument('--install-gui', action='store_true', help='Show installer dialog on GUI startup')
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print(f"SU2GUI version 1.0.2")
        print(f"SU2 target version: {SU2_RELEASE}")
        return 0
    
    # Handle clear data
    if args.clear_data:
        from core.user_config import clear_config
        clear_config()
        print("All application data cleared.")
        return 0
    
    # Set default jobs if not specified
    if hasattr(args, 'jobs') and args.jobs is None:
        import os
        args.jobs = os.cpu_count() or 4
    
    # Handle installation commands
    if args.command == 'install':
        success = install_su2(
            mode=args.mode,
            prefix=args.prefix,
            pywrapper=args.pywrapper,
            mpi=args.mpi,
            autodiff=args.autodiff,
            jobs=args.jobs,
            dry_run=args.dry_run
        )
        return 0 if success else 1
        
    elif args.command == 'validate':
        success = validate_installation(args.prefix)
        return 0 if success else 1
        
    elif args.command == 'info':
        show_system_info()
        return 0
        
    elif args.command == 'uninstall':
        success = uninstall_su2(args.prefix, args.remove_env)
        return 0 if success else 1
    
    # If no command specified, start the GUI
    print_banner()
    print("\n  Starting SU2GUI...")
    print(f"   GUI will be available at: http://localhost:{args.port}")
    print("   Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Import and run the main SU2GUI application
        # We need to modify sys.argv to pass the GUI arguments correctly
        gui_args = ['su2gui.py']
        if args.port != 8080:
            gui_args.extend(['--port', str(args.port)])
        if args.case:
            gui_args.extend(['--case', args.case])
        if args.mesh:
            gui_args.extend(['--mesh', args.mesh])
        if args.config:
            gui_args.extend(['--config', args.config])
        if args.restart:
            gui_args.extend(['--restart', args.restart])
        if args.su2:
            gui_args.extend(['--su2', args.su2])
        if args.install_gui:
            gui_args.append('--install')
        
        # Backup original argv and replace it
        original_argv = sys.argv
        sys.argv = gui_args
        
        try:
            # Import and run the main application
            import su2gui
            su2gui.main()
        finally:
            # Restore original argv
            sys.argv = original_argv
            
    except KeyboardInterrupt:
        print("\n\n GUI stopped by user.")
        return 0
    except Exception as e:
        print(f"\n Failed to start GUI: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        sys.exit(1)
