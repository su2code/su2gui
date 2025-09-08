# Constants and configuration for SU2 installation
from pathlib import Path

# SU2 Release Information
SU2_RELEASE = "v8.2.0"
SU2_GITHUB_URL = "https://github.com/su2code/SU2"
BIN_BASE_URL = "https://github.com/su2code/SU2/releases/download"

# Conda Configuration
CONDA_PKG = "su2"
CONDA_CHANNEL = "conda-forge"

# Platform Architecture Mappings (short tags matching GitHub release assets)
PLATFORM_ARCH_MAP = {
    ("Linux", "x86_64"): "linux64",
    ("Linux", "aarch64"): "linux64",
    ("Darwin", "x86_64"): "macos64",
    ("Darwin", "arm64"): "macos64",
    ("Windows", "AMD64"): "win64",
}

# Installation Modes
class InstallMode:
    BIN = "binaries"
    SRC = "source"
    CONDA = "conda"

# Default Settings
DEFAULT_CHUNK_SIZE = 2**16  # 64KB chunks for downloads
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Environment Variables
ENV_VARS = {
    "SU2_RUN": "bin",
    "SU2_HOME": "",
    "PATH": "bin",
    "PYTHONPATH": "bin"
}

# Build Dependencies
BUILD_DEPENDENCIES = {
    "git": "Git version control system",
    "ninja": "Ninja build system", 
    "python": "Python interpreter (3.8+)",
    "meson": "Meson build system"
}

# Optional Dependencies
OPTIONAL_DEPENDENCIES = {
    "mpi": ["mpicc", "mpicxx", "mpirun"],
    "autodiff": ["codi"],
    "python": ["python3-dev", "python3-distutils"]
}
