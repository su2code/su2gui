import os
import json
import platform
from pathlib import Path

def get_config_dir():
    
    if platform.system() == "Windows":
        base_dir = os.getenv("APPDATA")
        return Path(base_dir) / "su2gui"
    else:  # Unix-like (Linux, macOS)
        return Path.home() / ".su2gui"

def get_config_file():
    
    return get_config_dir() / "UserConfig.json"

def read_config():
    
    config_file = get_config_file()
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def write_config(config):
    
    config_dir = get_config_dir()
    config_file = get_config_file()
    
    # Ensure the directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def clear_config():
    
    config_file = get_config_file()
    if config_file.exists():
        config_file.unlink()
        return True
    return False

def get_su2_path():
    
    config = read_config()
    return config.get('su2_cfd_path')

def set_su2_path(path):
    
    config = read_config()
    config['su2_cfd_path'] = path
    write_config(config)
