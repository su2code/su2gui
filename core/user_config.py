"""
Configuration settings management for SU2GUI.
This module handles reading, writing, and validating user configuration.
"""

import os
import json
import platform
from pathlib import Path

def get_config_dir():
    """Return the platform-specific directory for configuration files."""
    if platform.system() == "Windows":
        base_dir = os.getenv("APPDATA")
        return Path(base_dir) / "su2gui"
    else:  # Unix-like (Linux, macOS)
        return Path.home() / ".su2gui"

def get_config_file():
    """Return the path to the configuration file."""
    return get_config_dir() / "UserConfig.json"

def read_config():
    """Read and return the configuration dictionary."""
    config_file = get_config_file()
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def write_config(config):
    """Write the configuration dictionary to file."""
    config_dir = get_config_dir()
    config_file = get_config_file()
    
    # Ensure the directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def clear_config():
    """Clear all stored configuration settings."""
    config_file = get_config_file()
    if config_file.exists():
        config_file.unlink()
        return True
    return False

def get_su2_path():
    """Get the path to SU2_CFD executable."""
    config = read_config()
    return config.get('su2_cfd_path')

def set_su2_path(path):
    """Set the path to SU2_CFD executable."""
    config = read_config()
    config['su2_cfd_path'] = path
    write_config(config)
