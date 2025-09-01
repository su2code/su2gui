# Source code build pipeline

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .constants import SU2_GITHUB_URL, SU2_RELEASE, BUILD_DEPENDENCIES
from .detect import check_build_dependencies, get_cpu_count


class BuildError(Exception):
    pass


class SU2Builder:
    
    def __init__(self, prefix: Path, source_dir: Optional[Path] = None):
        self.prefix = Path(prefix).resolve()
        self.source_dir = source_dir or (self.prefix.parent / "SU2_src")
        self.build_dir = self.source_dir / "build"
        
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, **kwargs) -> None:
        
        print(f"$ {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.source_dir,
                check=True,
                capture_output=True,
                text=True,
                **kwargs
            )
            
            # Print output if available
            if result.stdout:
                print(result.stdout)
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\nError output: {e.stderr}"
            raise BuildError(error_msg)
        except FileNotFoundError:
            raise BuildError(f"Command not found: {cmd[0]}")
    
    def check_dependencies(self) -> None:
        deps = check_build_dependencies()
        missing = [dep for dep, available in deps.items() if not available]
        
        if missing:
            raise BuildError(f"Missing build dependencies: {', '.join(missing)}")
    
    def clone_or_update_source(self) -> None:
        if self.source_dir.exists():
            print("Updating existing source code...")
            self.run_command(["git", "fetch", "--all", "--tags"], cwd=self.source_dir)
            self.run_command(["git", "checkout", SU2_RELEASE], cwd=self.source_dir)
            self.run_command(["git", "pull"], cwd=self.source_dir)
        else:
            print("Cloning SU2 source code...")
            self.run_command([
                "git", "clone", 
                "--branch", SU2_RELEASE,
                "--depth", "1",
                SU2_GITHUB_URL,
                str(self.source_dir)
            ], cwd=self.source_dir.parent)
    
    def configure_build(
        self,
        enable_pywrapper: bool = False,
        enable_mpi: bool = False,
        enable_autodiff: bool = False,
        custom_options: Optional[List[str]] = None
    ) -> None:
        print("Configuring build...")
        
        options = [
            f"-Denable-pywrapper={'true' if enable_pywrapper else 'false'}",
            f"-Denable-mpi={'true' if enable_mpi else 'false'}",
            f"-Denable-autodiff={'true' if enable_autodiff else 'false'}",
            f"--prefix={self.prefix}"
        ]
        
        if custom_options:
            options.extend(custom_options)
        
        cmd = [sys.executable, "meson.py", "build"] + options
        
        if self.build_dir.exists():
            import shutil
            shutil.rmtree(self.build_dir)
        
        self.run_command(cmd)
    
    def build(self, jobs: Optional[int] = None) -> None:
        print("Building SU2...")
        
        if jobs is None:
            jobs = get_cpu_count()
        
        cmd = ["ninja", "-C", "build", f"-j{jobs}"]
        self.run_command(cmd)
    
    def install(self) -> None:
        print("Installing SU2...")
        
        cmd = ["ninja", "-C", "build", "install"]
        self.run_command(cmd)
    
    def clean(self) -> None:
        if self.build_dir.exists():
            import shutil
            shutil.rmtree(self.build_dir)
            print("Build directory cleaned")
    
    def get_build_info(self) -> Dict[str, str]:
        info = {
            "source_dir": str(self.source_dir),
            "build_dir": str(self.build_dir),
            "prefix": str(self.prefix),
            "version": SU2_RELEASE
        }
        
        try:
            if self.source_dir.exists():
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.source_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info["git_commit"] = result.stdout.strip()
        except:
            pass
        
        return info


def build_from_source(
    prefix: Path,
    enable_pywrapper: bool = False,
    enable_mpi: bool = False,
    enable_autodiff: bool = False,
    jobs: Optional[int] = None,
    source_dir: Optional[Path] = None,
    custom_options: Optional[List[str]] = None,
    clean_build: bool = False
) -> None:
    builder = SU2Builder(prefix, source_dir)
    
    try:
        # Check dependencies
        builder.check_dependencies()
        
        # Clean if requested
        if clean_build:
            builder.clean()
        
        # Get or update source
        builder.clone_or_update_source()
        
        # Configure build
        builder.configure_build(
            enable_pywrapper=enable_pywrapper,
            enable_mpi=enable_mpi,
            enable_autodiff=enable_autodiff,
            custom_options=custom_options
        )
        
        # Build and install
        builder.build(jobs)
        builder.install()
        
        print("Source build completed successfully")
        
    except Exception as e:
        raise BuildError(f"Build failed: {str(e)}")


def get_build_requirements() -> Dict[str, str]:
    return BUILD_DEPENDENCIES.copy()


def validate_build_environment() -> Dict[str, bool]:
    results = check_build_dependencies()
    
    try:
        results["python_version_ok"] = sys.version_info >= (3, 8)
        
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        results["git_version_ok"] = result.returncode == 0
        
    except:
        results["python_version_ok"] = False
        results["git_version_ok"] = False
    
    return results
