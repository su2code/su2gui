"""
Environment variable management and shell integration
"""
import os
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

from .detect import get_rc_file, is_windows, get_shell_type
from .constants import ENV_VARS


class EnvironmentManager:
    """Manages SU2 environment variables and shell integration."""
    
    def __init__(self, prefix: Path):
        self.prefix = Path(prefix).resolve()
        self.env_vars = self._build_env_vars()
        
    def _build_env_vars(self) -> Dict[str, str]:
        """Build environment variables dictionary."""
        env_vars = {}
        
        # Use a simple, fast approach - just check if bin directory exists
        # without doing expensive directory scanning
        standard_bin = self.prefix / "bin"
        
        for var, subpath in ENV_VARS.items():
            if var == "SU2_HOME":
                env_vars[var] = str(self.prefix)
            elif var in ("SU2_RUN", "PATH", "PYTHONPATH"):
                # Use standard bin path if it exists, otherwise use default
                if standard_bin.exists():
                    env_vars[var] = str(standard_bin)
                else:
                    env_vars[var] = str(self.prefix / subpath)
            
        return env_vars
    
    def _find_bin_directory(self) -> Optional[Path]:
        """
        Find the actual bin directory containing SU2 executables.
        
        Returns:
            Path to bin directory or None if not found
        """
        if not self.prefix.exists():
            return None
        
        # Possible locations for bin directory
        possible_locations = [
            self.prefix / "bin",  # Standard location
            self.prefix,  # Executables in root
        ]
        
        # Check for nested SU2 directories (common in binary distributions)
        # Add timeout and error handling to prevent hangs
        try:
            if self.prefix.exists():
                for item in self.prefix.iterdir():
                    if item.is_dir() and "SU2" in item.name.upper():
                        possible_locations.extend([
                            item / "bin",
                            item
                        ])
        except (PermissionError, OSError):
            # If we can't read the directory, just use the default locations
            pass
        
        # Find directory containing SU2_CFD executable
        exe_name = "SU2_CFD" + (".exe" if is_windows() else "")
        
        for location in possible_locations:
            try:
                if location.exists() and (location / exe_name).exists():
                    return location
            except (PermissionError, OSError):
                # Skip locations we can't access
                continue
        
        return None
    
    def get_env_script(self) -> str:
        """Generate environment setup script."""
        if is_windows():
            return self._get_windows_env_script()
        else:
            return self._get_unix_env_script()
    
    def _get_unix_env_script(self) -> str:
        """Generate Unix/Linux environment script."""
        lines = ["# >>> SU2 automatically added by SU2_GUI <<<"]
        
        # Set SU2-specific variables
        lines.append(f'export SU2_HOME="{self.env_vars["SU2_HOME"]}"')
        lines.append(f'export SU2_RUN="{self.env_vars["SU2_RUN"]}"')
        
        # Add to PATH
        lines.append(f'export PATH="{self.env_vars["PATH"]}:$PATH"')
        
        # Add to PYTHONPATH
        lines.append(f'export PYTHONPATH="{self.env_vars["PYTHONPATH"]}:$PYTHONPATH"')
        
        lines.append("# <<< End SU2 block <<<")
        
        return "\n".join(lines)
    
    def _get_windows_env_script(self) -> str:
        """Generate Windows batch script."""
        lines = ["@echo off"]
        lines.append("REM >>> SU2 automatically added by SU2_GUI <<<")
        
        # Set SU2-specific variables
        lines.append(f'set SU2_HOME={self.env_vars["SU2_HOME"]}')
        lines.append(f'set SU2_RUN={self.env_vars["SU2_RUN"]}')
        
        # Add to PATH
        lines.append(f'set PATH={self.env_vars["PATH"]};%PATH%')
        
        # Add to PYTHONPATH
        lines.append(f'set PYTHONPATH={self.env_vars["PYTHONPATH"]};%PYTHONPATH%')
        
        lines.append("REM <<< End SU2 block <<<")
        
        return "\n".join(lines)
    
    def write_env_file(self, rc_file: Optional[Path] = None) -> Path:
        """
        Write environment variables to RC file.
        
        Args:
            rc_file: Optional custom RC file path
            
        Returns:
            Path to RC file that was written
        """
        if rc_file is None:
            rc_file = get_rc_file()
        
        env_script = self.get_env_script()
        
        # Check if already exists
        if rc_file.exists():
            with open(rc_file, 'r') as f:
                content = f.read()
                if "SU2_GUI" in content:
                    print(f"SU2 environment already configured in {rc_file}")
                    return rc_file
        
        # Append to file
        with open(rc_file, 'a') as f:
            f.write('\n' + env_script + '\n')
        
        print(f"Environment variables added to {rc_file}")
        return rc_file
    
    def remove_env_file(self, rc_file: Optional[Path] = None) -> bool:
        """
        Remove SU2 environment variables from RC file.
        
        Args:
            rc_file: Optional custom RC file path
            
        Returns:
            True if environment was removed
        """
        if rc_file is None:
            rc_file = get_rc_file()
        
        if not rc_file.exists():
            return False
        
        # Read current content
        with open(rc_file, 'r') as f:
            lines = f.readlines()
        
        # Filter out SU2 blocks
        filtered_lines = []
        in_su2_block = False
        
        for line in lines:
            if ">>> SU2 automatically added by SU2_GUI <<<" in line:
                in_su2_block = True
                continue
            elif "<<< End SU2 block <<<" in line:
                in_su2_block = False
                continue
            elif not in_su2_block:
                filtered_lines.append(line)
        
        # Write back if changed
        if len(filtered_lines) != len(lines):
            with open(rc_file, 'w') as f:
                f.writelines(filtered_lines)
            print(f"SU2 environment removed from {rc_file}")
            return True
        
        return False
    
    def get_current_env(self) -> Dict[str, Optional[str]]:
        """Get current SU2 environment variables."""
        return {
            var: os.environ.get(var)
            for var in self.env_vars.keys()
        }
    
    def validate_installation(self, detailed: bool = False) -> Dict[str, bool]:
        """
        Validate SU2 installation by checking paths and executables.
        
        Args:
            detailed: If True, perform detailed search. If False, use quick validation.
        
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # Check if directories exist
        results["su2_home_exists"] = Path(self.env_vars["SU2_HOME"]).exists()
        results["su2_run_exists"] = Path(self.env_vars["SU2_RUN"]).exists()
        
        if detailed:
            # Detailed validation with directory scanning (use only when explicitly requested)
            return self._detailed_validation()
        else:
            # Quick validation - just check standard locations
            return self._quick_validation()
    
    def _quick_validation(self) -> Dict[str, bool]:
        """Quick validation that only checks standard bin directory."""
        results = {}
        
        # Check if directories exist
        results["su2_home_exists"] = Path(self.env_vars["SU2_HOME"]).exists()
        results["su2_run_exists"] = Path(self.env_vars["SU2_RUN"]).exists()
        
        # Check for key executables in standard bin directory only
        bin_dir = Path(self.env_vars["SU2_RUN"])
        core_executables = ["SU2_CFD", "SU2_SOL", "SU2_DEF", "SU2_DOT", "SU2_GEO"]
        optional_executables = ["SU2_MSH"]
        
        # Check core executables
        for exe in core_executables:
            exe_name = exe + (".exe" if is_windows() else "")
            exe_path = bin_dir / exe_name
            try:
                results[f"{exe.lower()}_exists"] = exe_path.exists() and exe_path.is_file()
            except (PermissionError, OSError):
                results[f"{exe.lower()}_exists"] = False
        
        # Check optional executables
        for exe in optional_executables:
            exe_name = exe + (".exe" if is_windows() else "")
            exe_path = bin_dir / exe_name
            try:
                exe_found = exe_path.exists() and exe_path.is_file()
                results[f"{exe.lower()}_exists"] = True  # Always pass for optional
                results[f"{exe.lower()}_actually_exists"] = exe_found
            except (PermissionError, OSError):
                results[f"{exe.lower()}_exists"] = True
                results[f"{exe.lower()}_actually_exists"] = False
        
        # Check for Python wrapper
        try:
            su2_module = bin_dir / "SU2"
            python_wrapper_found = (su2_module.exists() and su2_module.is_dir() and 
                                   (su2_module / "__init__.py").exists())
            if not python_wrapper_found:
                # Check for other common Python wrapper files
                wrapper_files = ["pysu2", "pysu2.py", "SU2.py", "SU2_CFD.py"]
                for wrapper_name in wrapper_files:
                    if (bin_dir / wrapper_name).exists():
                        python_wrapper_found = True
                        break
            results["python_wrapper_exists"] = python_wrapper_found
        except (PermissionError, OSError):
            results["python_wrapper_exists"] = False
        
        return results
    
    def _detailed_validation(self) -> Dict[str, bool]:
        """Detailed validation with directory scanning (slower but more thorough)."""
        results = {}
        
        # Check if directories exist
        results["su2_home_exists"] = Path(self.env_vars["SU2_HOME"]).exists()
        results["su2_run_exists"] = Path(self.env_vars["SU2_RUN"]).exists()
        
        # Check for key executables in multiple possible locations
        bin_dir = Path(self.env_vars["SU2_RUN"])
        prefix_dir = Path(self.env_vars["SU2_HOME"])
        
        # Core executables (required for most SU2 operations)
        core_executables = ["SU2_CFD", "SU2_SOL", "SU2_DEF", "SU2_DOT", "SU2_GEO"]
        # Optional executables (not always included in binary distributions)
        optional_executables = ["SU2_MSH"]
        
        # Possible locations for executables after binary extraction
        possible_bin_dirs = [
            bin_dir,  # Standard bin directory
            prefix_dir / "bin",  # Alternative bin location
            prefix_dir,  # Direct in prefix (some binary archives)
        ]
        
        # Look for nested SU2 directory structure (common in binary archives)
        # Add error handling to prevent hangs
        try:
            if prefix_dir.exists():
                for subdir in prefix_dir.iterdir():
                    if subdir.is_dir() and "SU2" in subdir.name.upper():
                        possible_bin_dirs.extend([
                            subdir / "bin",
                            subdir
                        ])
        except (PermissionError, OSError):
            # If we can't read the directory, just use the default locations
            pass
        
        # Check core executables (these should exist for a valid installation)
        for exe in core_executables:
            exe_found = False
            exe_name = exe + (".exe" if is_windows() else "")
            
            for search_dir in possible_bin_dirs:
                try:
                    if search_dir.exists():
                        exe_path = search_dir / exe_name
                        if exe_path.exists() and exe_path.is_file():
                            exe_found = True
                            break
                except (PermissionError, OSError):
                    # Skip directories we can't access
                    continue
            
            results[f"{exe.lower()}_exists"] = exe_found
        
        # Check optional executables (don't mark as critical failures)
        for exe in optional_executables:
            exe_found = False
            exe_name = exe + (".exe" if is_windows() else "")
            
            for search_dir in possible_bin_dirs:
                try:
                    if search_dir.exists():
                        exe_path = search_dir / exe_name
                        if exe_path.exists() and exe_path.is_file():
                            exe_found = True
                            break
                except (PermissionError, OSError):
                    # Skip directories we can't access
                    continue
            
            # Mark as found even if missing (since it's optional)
            # But store the actual result for informational purposes
            results[f"{exe.lower()}_exists"] = True  # Always pass for optional
            results[f"{exe.lower()}_actually_exists"] = exe_found  # Store real result
        
        # Check for Python wrapper in possible locations
        python_wrapper_found = False
        
        # Look for SU2 Python module directory
        for search_dir in possible_bin_dirs:
            try:
                if search_dir.exists():
                    # Check for SU2 Python module
                    su2_module = search_dir / "SU2"
                    if su2_module.exists() and su2_module.is_dir():
                        init_file = su2_module / "__init__.py"
                        if init_file.exists():
                            python_wrapper_found = True
                            break
                    
                    # Check for other Python wrapper indicators
                    wrapper_files = ["pysu2", "pysu2.py", "SU2.py", "SU2_CFD.py"]
                    for wrapper_name in wrapper_files:
                        wrapper_path = search_dir / wrapper_name
                        if wrapper_path.exists():
                            python_wrapper_found = True
                            break
                    
                    if python_wrapper_found:
                        break
            except (PermissionError, OSError):
                # Skip directories we can't access
                continue
        
        results["python_wrapper_exists"] = python_wrapper_found
        
        return results
    
    def get_activation_instructions(self) -> str:
        """Get instructions for activating the environment."""
        rc_file = get_rc_file()
        
        if is_windows():
            return f"""
To activate SU2 environment, run:
    {rc_file}

Or restart your command prompt.
"""
        else:
            shell = get_shell_type()
            return f"""
To activate SU2 environment, run:
    source {rc_file}

Or restart your terminal.
For immediate activation in current session:
    source {rc_file}
"""


def write_env(prefix: Path, rc_file: Optional[Path] = None) -> Path:
    """
    Convenience function to write environment variables.
    
    Args:
        prefix: Installation prefix path
        rc_file: Optional RC file path
        
    Returns:
        Path to RC file that was written
    """
    env_manager = EnvironmentManager(prefix)
    return env_manager.write_env_file(rc_file)


def remove_env(rc_file: Optional[Path] = None) -> bool:
    """
    Convenience function to remove environment variables.
    
    Args:
        rc_file: Optional RC file path
        
    Returns:
        True if environment was removed
    """
    # Use dummy prefix since we're just removing
    env_manager = EnvironmentManager(Path("/dummy"))
    return env_manager.remove_env_file(rc_file)


def validate_env(prefix: Path, detailed: bool = False) -> Dict[str, bool]:
    """
    Convenience function to validate environment.
    
    Args:
        prefix: Installation prefix path
        detailed: If True, perform detailed validation with directory scanning
        
    Returns:
        Dictionary of validation results
    """
    env_manager = EnvironmentManager(prefix)
    return env_manager.validate_installation(detailed=detailed)
