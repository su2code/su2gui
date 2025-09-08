# Conda-specific installation logic
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .constants import CONDA_PKG, CONDA_CHANNEL, SU2_RELEASE
from .detect import has_conda, has_mamba, get_conda_command


class CondaError(Exception):
    pass


class CondaManager:
    
    def __init__(self, prefix: Optional[Path] = None):
        self.prefix = Path(prefix).resolve() if prefix else None
        self.conda_cmd = get_conda_command()
        
    def run_conda_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Run conda command with error handling.
        
        Args:
            args: Command arguments
            **kwargs: Additional subprocess arguments
            
        Returns:
            CompletedProcess result
            
        Raises:
            CondaError: If command fails
        """
        cmd = [self.conda_cmd] + args
        print(f"$ {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                **kwargs
            )
            
            if result.stdout:
                print(result.stdout)
                
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Conda command failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\nError output: {e.stderr}"
            raise CondaError(error_msg)
        except FileNotFoundError:
            raise CondaError(f"Conda command not found: {self.conda_cmd}")
    
    def check_conda_available(self) -> None:
        """
        Check if conda is available.
        
        Raises:
            CondaError: If conda is not available
        """
        if not has_conda():
            raise CondaError("Conda not found. Please install Miniconda or Anaconda.")
    
    def get_available_versions(self) -> List[str]:
        """
        Get available SU2 versions from conda.
        
        Returns:
            List of available versions
        """
        try:
            result = self.run_conda_command([
                "search", "-c", CONDA_CHANNEL, CONDA_PKG, "--json"
            ])
            
            import json
            packages = json.loads(result.stdout)
            
            versions = []
            for package_list in packages.values():
                for package in package_list:
                    if package["name"] == CONDA_PKG:
                        versions.append(package["version"])
            
            return sorted(set(versions), reverse=True)
            
        except Exception as e:
            print(f"Warning: Could not get available versions: {e}")
            return []
    
    def install_su2(
        self,
        version: Optional[str] = None,
        update: bool = False,
        extra_packages: Optional[List[str]] = None
    ) -> None:
        """
        Install SU2 via conda.
        
        Args:
            version: Specific version to install
            update: Whether to update existing installation
            extra_packages: Additional packages to install
            
        Raises:
            CondaError: If installation fails
        """
        self.check_conda_available()
        
        # Determine version
        if version is None:
            version = SU2_RELEASE.lstrip('v')
        
        # Build package specification
        package_spec = f"{CONDA_PKG}={version}"
        
        # Build command
        cmd_args = ["install", "-y", "-c", CONDA_CHANNEL]
        
        if self.prefix:
            cmd_args.extend(["--prefix", str(self.prefix)])
        
        cmd_args.append(package_spec)
        
        # Add extra packages
        if extra_packages:
            cmd_args.extend(extra_packages)
        
        # Add update flag
        if update:
            cmd_args.append("--update-deps")
        
        print(f"Installing SU2 {version} via conda...")
        self.run_conda_command(cmd_args)
    
    def uninstall_su2(self) -> None:
        """
        Uninstall SU2 via conda.
        
        Raises:
            CondaError: If uninstallation fails
        """
        self.check_conda_available()
        
        cmd_args = ["remove", "-y", CONDA_PKG]
        
        if self.prefix:
            cmd_args.extend(["--prefix", str(self.prefix)])
        
        print("Uninstalling SU2 via conda...")
        self.run_conda_command(cmd_args)
    
    def is_su2_installed(self) -> bool:
        """
        Check if SU2 is installed via conda.
        
        Returns:
            True if SU2 is installed
        """
        try:
            cmd_args = ["list", CONDA_PKG]
            
            if self.prefix:
                cmd_args.extend(["--prefix", str(self.prefix)])
            
            result = self.run_conda_command(cmd_args)
            return CONDA_PKG in result.stdout
            
        except:
            return False
    
    def get_installed_info(self) -> Optional[Dict[str, str]]:
        """
        Get information about installed SU2 package.
        
        Returns:
            Dictionary with package information or None
        """
        try:
            cmd_args = ["list", "--json", CONDA_PKG]
            
            if self.prefix:
                cmd_args.extend(["--prefix", str(self.prefix)])
            
            result = self.run_conda_command(cmd_args)
            
            import json
            packages = json.loads(result.stdout)
            
            for package in packages:
                if package["name"] == CONDA_PKG:
                    return {
                        "name": package["name"],
                        "version": package["version"],
                        "build": package.get("build_string", ""),
                        "channel": package.get("channel", ""),
                        "size": package.get("size", 0)
                    }
            
            return None
            
        except:
            return None
    
    def create_environment(
        self,
        env_name: str,
        python_version: str = "3.9",
        packages: Optional[List[str]] = None
    ) -> None:
        """
        Create a new conda environment with SU2.
        
        Args:
            env_name: Name of the environment
            python_version: Python version for the environment
            packages: Additional packages to install
            
        Raises:
            CondaError: If environment creation fails
        """
        self.check_conda_available()
        
        # Build package list
        package_list = [f"python={python_version}"]
        
        # Add SU2
        version = SU2_RELEASE.lstrip('v')
        package_list.append(f"{CONDA_PKG}={version}")
        
        # Add extra packages
        if packages:
            package_list.extend(packages)
        
        # Create environment
        cmd_args = ["create", "-y", "-n", env_name, "-c", CONDA_CHANNEL] + package_list
        
        print(f"Creating conda environment '{env_name}' with SU2...")
        self.run_conda_command(cmd_args)
    
    def get_environment_info(self) -> Dict[str, str]:
        """
        Get current conda environment information.
        
        Returns:
            Dictionary with environment information
        """
        try:
            result = self.run_conda_command(["info", "--json"])
            
            import json
            info = json.loads(result.stdout)
            
            return {
                "conda_version": info.get("conda_version", "unknown"),
                "python_version": info.get("python_version", "unknown"),
                "platform": info.get("platform", "unknown"),
                "active_prefix": info.get("active_prefix", "none"),
                "default_prefix": info.get("default_prefix", "none")
            }
            
        except:
            return {}


def install_via_conda(
    prefix: Optional[Path] = None,
    version: Optional[str] = None,
    update: bool = False,
    extra_packages: Optional[List[str]] = None
) -> None:
    """
    Install SU2 via conda.
    
    Args:
        prefix: Installation prefix
        version: Specific version to install
        update: Whether to update existing installation
        extra_packages: Additional packages to install
        
    Raises:
        CondaError: If installation fails
    """
    manager = CondaManager(prefix)
    manager.install_su2(version, update, extra_packages)


def check_conda_installation() -> Dict[str, bool]:
    """
    Check conda installation and capabilities.
    
    Returns:
        Dictionary of check results
    """
    results = {
        "conda_available": has_conda(),
        "mamba_available": has_mamba(),
        "su2_available": False,
        "can_install": False
    }
    
    if results["conda_available"]:
        try:
            manager = CondaManager()
            
            # Check if SU2 is available in conda-forge
            versions = manager.get_available_versions()
            results["su2_available"] = len(versions) > 0
            results["can_install"] = True
            
        except:
            pass
    
    return results
