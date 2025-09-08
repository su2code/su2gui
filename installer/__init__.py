"""
SU2 Installation Package

This package provides comprehensive SU2 installation capabilities including
binary downloads, source compilation, and conda-based installation.
"""

import os
import platform
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

# Import all required components
from .constants import InstallMode, SU2_RELEASE, BIN_BASE_URL, PLATFORM_ARCH_MAP
from .detect import (
    detect_installation_capabilities, 
    get_system_info, 
    get_default_prefix,
    get_arch_tag,
    is_windows
)
from .env import write_env, remove_env, validate_env
from .fetch import download_file, download_with_retry, DownloadError
from .build import build_from_source, validate_build_environment
from .conda import install_via_conda, check_conda_installation
from .ui import create_installer_app

def install_binaries(prefix: Path) -> None:
    """Install pre-compiled SU2 binaries."""
    print("Installing SU2 from pre-compiled binaries...")
    
    # Get platform-specific architecture tag (short lowercase)
    base_tag = get_arch_tag()
    if not base_tag:
        raise RuntimeError(
            f"Precompiled binaries not available for platform: "
            f"{platform.system()} {platform.machine()}"
        )
    mpi_suffix = "-mpi" if any(os.environ.get(dep) for dep in ["mpicc", "mpicxx"]) else ""
    arch_tag = base_tag + mpi_suffix
    # Always use zip assets
    ext = "zip"
    filename = f"SU2-{SU2_RELEASE}-{arch_tag}.{ext}"
    url = f"{BIN_BASE_URL}/{SU2_RELEASE}/{filename}"
    dst = prefix / filename
    
    print(f"Downloading {filename}...")
    try:
        # Download with retry capability
        download_with_retry(url, dst)
        
        print("Extracting archive...")
        
        # Verify the downloaded file exists and is valid
        if not dst.exists():
            raise RuntimeError(f"Downloaded file {dst} does not exist")
        
        extracted_files = []
        if ext == "zip":
            with zipfile.ZipFile(dst, 'r') as zf:
                # Verify zip file integrity
                zf.testzip()
                # Extract all files
                zf.extractall(prefix)
                extracted_files = zf.namelist()
        else:
            with tarfile.open(dst, "r:gz") as tf:
                tf.extractall(prefix)
                extracted_files = tf.getnames()
        
        print(f"Extracted {len(extracted_files)} files")
        
        # Verify extraction was successful before cleanup
        if extracted_files:
            # Check if at least one SU2 executable was extracted
            su2_exes = ["SU2_CFD", "SU2_SOL", "SU2_DEF", "SU2_DOT", "SU2_GEO", "SU2_MSH"]
            found_exe = False
            for extracted_file in extracted_files:
                if any(exe in extracted_file for exe in su2_exes):
                    found_exe = True
                    break
            
            if not found_exe:
                print("Warning: No SU2 executables found in extracted files")
            
            # Clean up downloaded archive only after successful extraction
            dst.unlink()
            print(f"Binary installation completed for {arch_tag}")
        else:
            raise RuntimeError("No files were extracted from the archive")
        
        # Verify extraction and report actual structure
        print("Verifying extraction...")
        _report_extracted_structure(prefix)
        
    except DownloadError as e:
        raise RuntimeError(f"Failed to download SU2 binaries: {e}")
    except (tarfile.TarError, zipfile.BadZipFile) as e:
        # Clean up corrupted file
        if dst.exists():
            dst.unlink()
        raise RuntimeError(f"Failed to extract SU2 archive: {e}")


def _report_extracted_structure(prefix: Path) -> None:
    """Report the structure of extracted files for debugging."""
    if not prefix.exists():
        print("Warning: Installation directory does not exist")
        return
    
    print(f"Installation directory: {prefix}")
    
    # Look for SU2 executables
    exe_suffix = ".exe" if is_windows() else ""
    su2_executables = ["SU2_CFD", "SU2_SOL", "SU2_DEF", "SU2_DOT", "SU2_GEO", "SU2_MSH"]
    
    found_executables = []
    for root, dirs, files in os.walk(prefix):
        for file in files:
            if any(file.startswith(exe) for exe in su2_executables):
                found_executables.append(Path(root) / file)
    
    if found_executables:
        print("Found SU2 executables:")
        for exe_path in found_executables:
            rel_path = exe_path.relative_to(prefix)
            print(f"  {rel_path}")
    else:
        print("Warning: No SU2 executables found in extracted files")
        print("Contents of installation directory:")
        for item in prefix.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    # Look for Python wrapper files
    python_files = []
    for root, dirs, files in os.walk(prefix):
        for file in files:
            if file.lower().endswith('.py') and ('su2' in file.lower() or 'pysu2' in file.lower()):
                python_files.append(Path(root) / file)
    
    if python_files:
        print("Found Python wrapper files:")
        for py_path in python_files:
            rel_path = py_path.relative_to(prefix)
            print(f"  {rel_path}")
    else:
        print("No Python wrapper files found")

def install(mode: str = InstallMode.BIN, prefix: Optional[Path] = None,
           enable_pywrapper: bool = False, enable_mpi: bool = False,
           enable_autodiff: bool = False, jobs: int = 4) -> None:
    """
    Main SU2 installation function that dispatches to specific installers.
    
    Args:
        mode: Installation mode ('binaries', 'source', or 'conda')
        prefix: Installation directory (defaults to ~/SU2_RUN or $VIRTUAL_ENV/SU2_RUN)
        enable_pywrapper: Enable Python wrapper for source builds
        enable_mpi: Enable MPI support for source builds
        enable_autodiff: Enable automatic differentiation for source builds
        jobs: Number of parallel build jobs for source builds
        
    Raises:
        ValueError: If installation mode is invalid
        RuntimeError: If installation fails
    """
    if prefix is None:
        prefix = get_default_prefix()
    
    prefix = Path(prefix).expanduser().resolve()
    prefix = Path(prefix).expanduser().resolve()
    prefix.mkdir(parents=True, exist_ok=True)
    
    print(f" Installing SU2 {SU2_RELEASE} to {prefix}")
    print(f" Installation mode: {mode}")
    
    # Dispatch to appropriate installer
    try:
        if mode == InstallMode.CONDA:
            print("Using conda installation method...")
            install_via_conda(prefix)
            
        elif mode == InstallMode.BIN:
            print("Using binary installation method...")
            install_binaries(prefix)
            
        elif mode == InstallMode.SRC:
            print("Using source compilation method...")
            print(f"Build options: pywrapper={enable_pywrapper}, "
                  f"mpi={enable_mpi}, autodiff={enable_autodiff}, jobs={jobs}")
            build_from_source(
                prefix=prefix,
                enable_pywrapper=enable_pywrapper,
                enable_mpi=enable_mpi,
                enable_autodiff=enable_autodiff,
                jobs=jobs
            )
            
        else:
            raise ValueError(f"Unknown installation mode: {mode}")
        
        # Set up environment variables
        print("Setting up environment variables...")
        write_env(prefix)
        
        # Validate installation
        print("Validating installation...")
        validation_results = validate_env(prefix)
        
        failed_checks = [check for check, passed in validation_results.items() if not passed]
        if failed_checks:
            print(f" Warning: Some validation checks failed: {', '.join(failed_checks)}")
        else:
            print(" Installation validation passed!")
            
        print(" SU2 installation completed successfully!")
        
    except Exception as e:
        print(f" Installation failed: {e}")
        raise

def uninstall(prefix: Optional[Path] = None) -> None:
    """
    Uninstall SU2 by removing installation directory and environment variables.
    
    Args:
        prefix: Installation directory to remove (defaults to auto-detected)
    """
    if prefix is None:
        prefix = get_default_prefix()
    
    prefix = Path(prefix).expanduser().resolve()
    
    print(f" Uninstalling SU2 from {prefix}")
    
    try:
        # Remove installation directory
        if prefix.exists():
            import shutil
            shutil.rmtree(prefix)
            print(f"Removed installation directory: {prefix}")
        else:
            print(f"Installation directory not found: {prefix}")
        
        # Remove environment variables
        if remove_env():
            print("Removed environment variables")
        else:
            print("No environment variables found to remove")
            
        print("SU2 uninstallation completed!")
        
    except Exception as e:
        print(f"Uninstallation failed: {e}")
        raise

def get_installation_info(prefix: Optional[Path] = None) -> dict:
    """
    Get information about current SU2 installation.
    
    Args:
        prefix: Installation directory to check
        
    Returns:
        Dictionary containing installation information
    """
    if prefix is None:
        prefix = get_default_prefix()
    
    prefix = Path(prefix).expanduser().resolve()
    
    info = {
        "prefix": str(prefix),
        "installed": prefix.exists(),
        "version": "Unknown",
        "validation": {}
    }
    
    if info["installed"]:
        # Try to get version
        try:
            bin_path = prefix / "bin" / ("SU2_CFD.exe" if is_windows() else "SU2_CFD")
            if bin_path.exists():
                result = subprocess.run(
                    [str(bin_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    info["version"] = result.stdout.strip()
        except Exception:
            pass
        
        # Get validation results
        info["validation"] = validate_env(prefix)
    
    return info

# Package version
__version__ = "1.0.0"

__all__ = [
    "install",
    "uninstall",
    "get_installation_info",
    
    # Detection and system info
    "detect_installation_capabilities",
    "get_system_info",
    
    # Environment management
    "write_env",
    "remove_env", 
    "validate_env",
    
    # Download utilities
    "download_file",
    "download_with_retry",
    
    # Build utilities
    "build_from_source",
    "validate_build_environment",
    
    # Conda utilities
    "install_via_conda",
    "check_conda_installation",
    
    # UI components
    "create_installer_app",
    
    # Constants
    "SU2_RELEASE",
    "InstallMode",
    
    # Package info
    "__version__"
]
