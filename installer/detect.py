# Platform and architecture detection utilities
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import PLATFORM_ARCH_MAP, BUILD_DEPENDENCIES, OPTIONAL_DEPENDENCIES


def get_platform_info() -> Tuple[str, str]:
    # Get current platform system and machine architecture
    return platform.system(), platform.machine()


def get_arch_tag() -> Optional[str]:
    # Get the architecture tag for binary downloads
    return PLATFORM_ARCH_MAP.get(get_platform_info())


def is_windows() -> bool:
    # Check if running on Windows
    return platform.system() == "Windows"


def is_macos() -> bool:
    # Check if running on macOS
    return platform.system() == "Darwin"


def is_linux() -> bool:
    # Check if running on Linux
    return platform.system() == "Linux"


def is_apple_silicon() -> bool:
    # Check if running on Apple Silicon (M1/M2)
    return is_macos() and platform.machine() == "arm64"


def is_wsl() -> bool:
    # Check if running under Windows Subsystem for Linux
    if not is_linux():
        return False
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except (FileNotFoundError, PermissionError):
        return False


def get_shell_type() -> str:
    """
    Detect the user's shell type.
    
    Returns:
        Shell name (bash, zsh, fish, etc.)
    """
    shell = Path(os.environ.get("SHELL", "/bin/bash")).name
    return shell


def get_rc_file() -> Path:
    """
    Get the appropriate shell RC file for environment variables.
    
    Returns:
        Path to RC file
    """
    if is_windows():
        return Path.home() / ".su2_env.bat"
    
    shell = get_shell_type()
    rc_files = {
        "bash": ".bashrc",
        "zsh": ".zshrc", 
        "fish": ".config/fish/config.fish",
        "csh": ".cshrc",
        "tcsh": ".tcshrc"
    }
    
    return Path.home() / rc_files.get(shell, ".bashrc")


def has_command(cmd: str) -> bool:
    """
    Check if a command is available in PATH.
    
    Args:
        cmd: Command name to check
        
    Returns:
        True if command is available
    """
    return shutil.which(cmd) is not None


def has_conda() -> bool:
    """Check if conda is available."""
    return has_command("conda")


def has_mamba() -> bool:
    """Check if mamba is available."""
    return has_command("mamba")


def get_conda_command() -> str:
    """Get the preferred conda command (mamba if available, otherwise conda)."""
    return "mamba" if has_mamba() else "conda"


def check_build_dependencies() -> Dict[str, bool]:
    """
    Check availability of build dependencies.
    
    Returns:
        Dictionary mapping dependency names to availability status
    """
    return {dep: has_command(dep) for dep in BUILD_DEPENDENCIES.keys()}


def check_optional_dependencies(features: List[str]) -> Dict[str, Dict[str, bool]]:
    """
    Check availability of optional dependencies for specific features.
    
    Args:
        features: List of feature names to check
        
    Returns:
        Nested dictionary of feature -> dependency -> availability
    """
    result = {}
    for feature in features:
        if feature in OPTIONAL_DEPENDENCIES:
            result[feature] = {
                dep: has_command(dep) 
                for dep in OPTIONAL_DEPENDENCIES[feature]
            }
    return result


def get_cpu_count() -> int:
    """
    Get the number of CPU cores, with fallback.
    
    Returns:
        Number of CPU cores
    """
    try:
        import os
        return os.cpu_count() or 4
    except:
        return 4


def get_python_version() -> Tuple[int, int]:
    """
    Get Python version tuple.
    
    Returns:
        Tuple of (major, minor) version numbers
    """
    return sys.version_info[:2]


def is_python_compatible() -> bool:
    """Check if Python version is compatible (3.8+)."""
    major, minor = get_python_version()
    return major >= 3 and minor >= 8


def get_virtual_env() -> Optional[Path]:
    """
    Get current virtual environment path.
    
    Returns:
        Path to virtual environment or None
    """
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        return Path(venv_path)
    
    # Check for conda environment
    conda_env = os.environ.get("CONDA_PREFIX")
    if conda_env:
        return Path(conda_env)
    
    return None


def get_default_prefix() -> Path:
    """
    Get default installation prefix.
    
    Returns:
        Default installation path
    """
    venv = get_virtual_env()
    base = venv if venv else Path.home()
    return base / "SU2_RUN"


def detect_installation_capabilities() -> Dict[str, bool]:
    """
    Detect what installation methods are available.
    
    Returns:
        Dictionary of installation method capabilities
    """
    capabilities = {
        "binaries": get_arch_tag() is not None,
        "conda": has_conda(),
        "source": all(check_build_dependencies().values()),
        "python_compatible": is_python_compatible()
    }
    
    return capabilities


def get_system_info() -> Dict[str, str]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary of system information
    """
    system, machine = get_platform_info()
    
    return {
        "system": system,
        "machine": machine,
        "arch_tag": get_arch_tag() or "unsupported",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "shell": get_shell_type(),
        "is_wsl": str(is_wsl()),
        "is_apple_silicon": str(is_apple_silicon()),
        "cpu_count": str(get_cpu_count()),
        "virtual_env": str(get_virtual_env()) if get_virtual_env() else "None"
    }
