from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as v3, html
from trame.decorators import TrameApp, change, trigger
import asyncio
import threading
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Literal
import urllib.request
import tarfile
import zipfile
import platform

class SU2InstallerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self.server.client_type = "vue3"
        
        # Initialize state variables
        self.state.setdefault("install_mode", "binaries")
        self.state.setdefault("install_prefix", str(Path.home() / "SU2_RUN"))
        self.state.setdefault("enable_pywrapper", False)
        self.state.setdefault("enable_mpi", False)
        self.state.setdefault("enable_autodiff", False)
        self.state.setdefault("parallel_jobs", os.cpu_count() or 4)
        self.state.setdefault("dialog_visible", False)
        self.state.setdefault("installation_progress", 0)
        self.state.setdefault("installation_status", "Ready")
        self.state.setdefault("installation_log", "")
        self.state.setdefault("installation_running", False)
        self.state.setdefault("show_progress", False)
        
        # Installation constants
        self.SU2_RELEASE = "v8.2.0"
        self.BIN_BASE_URL = "https://github.com/su2code/SU2/releases/download"
        
        self._build_ui()

    def _build_ui(self):
        """Build the Trame user interface"""
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text("SU2GUI - Install/Update SU2")
            
            with layout.toolbar:
                v3.VSpacer()
                v3.VBtn(
                    "Install / Update SU2",
                    icon="mdi-download",
                    color="primary",
                    click=self.open_installer_dialog
                )

            with layout.content:
                # Main installer dialog
                with v3.VDialog(
                    v_model=("dialog_visible", False),
                    max_width="800",
                    persistent=True
                ):
                    with v3.VCard():
                        with v3.VCardTitle():
                            html.Span("SU2 Installation Wizard")
                            v3.VSpacer()
                            v3.VBtn(
                                icon="mdi-close",
                                variant="text",
                                click=self.close_dialog,
                                disabled=("installation_running", False)
                            )
                        
                        with v3.VCardText():
                            self._build_installation_form()
                            self._build_progress_section()
                        
                        with v3.VCardActions():
                            v3.VSpacer()
                            v3.VBtn(
                                "Cancel",
                                color="grey",
                                click=self.close_dialog,
                                disabled=("installation_running", False)
                            )
                            v3.VBtn(
                                "Install",
                                color="primary",
                                click=self.start_installation,
                                disabled=("installation_running", False),
                                loading=("installation_running", False)
                            )

    def _build_installation_form(self):
        """Build the installation configuration form"""
        with v3.VContainer():
            # Installation mode selection
            with v3.VRow():
                with v3.VCol(cols=12):
                    v3.VSelect(
                        label="Installation Mode",
                        v_model=("install_mode", "binaries"),
                        items=[
                            {"title": "Pre-compiled Binaries (Recommended)", "value": "binaries"},
                            {"title": "Build from Source", "value": "source"},
                            {"title": "Conda Package", "value": "conda"}
                        ],
                        outlined=True
                    )
            
            # Installation directory
            with v3.VRow():
                with v3.VCol(cols=10):
                    v3.VTextField(
                        label="Installation Directory",
                        v_model=("install_prefix",),
                        outlined=True,
                        hint="Directory where SU2 will be installed"
                    )
                with v3.VCol(cols=2):
                    v3.VBtn(
                        icon="mdi-folder",
                        variant="outlined",
                        click=self.browse_directory
                    )
            
            # Advanced options (show only for source build)
            with v3.VExpandTransition():
                with v3.VCard(
                    v_show="install_mode === 'source'",
                    variant="outlined",
                    class_="mt-4"
                ):
                    with v3.VCardTitle():
                        html.Span("Build Options")
                    with v3.VCardText():
                        with v3.VRow():
                            with v3.VCol(cols=12):
                                v3.VCheckbox(
                                    label="Enable Python Wrapper (pysu2)",
                                    v_model=("enable_pywrapper", False),
                                    hint="Build Python bindings for SU2"
                                )
                            with v3.VCol(cols=6):
                                v3.VCheckbox(
                                    label="Enable MPI Support",
                                    v_model=("enable_mpi", False)
                                )
                            with v3.VCol(cols=6):
                                v3.VCheckbox(
                                    label="Enable Automatic Differentiation",
                                    v_model=("enable_autodiff", False)
                                )
                            with v3.VCol(cols=12):
                                v3.VSlider(
                                    label="Parallel Build Jobs",
                                    v_model=("parallel_jobs", 4),
                                    min=1,
                                    max=16,
                                    step=1,
                                    thumb_label=True
                                )

    def _build_progress_section(self):
        """Build the installation progress section"""
        with v3.VExpandTransition():
            with v3.VCard(
                v_show=("show_progress", False),
                variant="outlined",
                class_="mt-4"
            ):
                with v3.VCardTitle():
                    html.Span("Installation Progress")
                with v3.VCardText():
                    # Progress bar
                    v3.VProgressLinear(
                        v_model=("installation_progress", 0),
                        height="20",
                        color="primary",
                        striped=True
                    )
                    
                    # Status text
                    with v3.VRow(class_="mt-2"):
                        with v3.VCol():
                            html.P(
                                "{{ installation_status }}",
                                class_="text-body-1 mb-2"
                            )
                    
                    # Log output
                    with v3.VTextarea(
                        v_model=("installation_log", ""),
                        label="Installation Log",
                        readonly=True,
                        rows=8,
                        variant="outlined",
                        class_="mt-2"
                    ):
                        pass

    # Event handlers
    @trigger("open_installer_dialog")
    def open_installer_dialog(self):
        """Open the installer dialog"""
        self.state.dialog_visible = True
        self.state.show_progress = False
        self.state.installation_progress = 0
        self.state.installation_status = "Ready"
        self.state.installation_log = ""

    @trigger("close_dialog")
    def close_dialog(self):
        """Close the installer dialog"""
        if not self.state.installation_running:
            self.state.dialog_visible = False

    @trigger("browse_directory")
    def browse_directory(self):
        """Browse for installation directory"""
        # In a real implementation, this would open a directory browser
        # For now, we'll use a simple fallback
        self.state.installation_log += "Directory browser not implemented in web version\n"

    @trigger("start_installation")
    def start_installation(self):
        """Start the SU2 installation process"""
        self.state.installation_running = True
        self.state.show_progress = True
        self.state.installation_progress = 0
        self.state.installation_status = "Starting installation..."
        
        # Start installation in background thread
        thread = threading.Thread(
            target=self._run_installation_async,
            daemon=True
        )
        thread.start()

    def _run_installation_async(self):
        """Run installation in background thread with progress updates"""
        try:
            self._update_progress(10, "Validating configuration...")
            
            # Validate inputs
            install_dir = Path(self.state.install_prefix).expanduser().resolve()
            install_dir.mkdir(parents=True, exist_ok=True)
            
            self._update_progress(20, "Preparing installation...")
            
            if self.state.install_mode == "binaries":
                self._install_binaries(install_dir)
            elif self.state.install_mode == "source":
                self._install_from_source(install_dir)
            elif self.state.install_mode == "conda":
                self._install_conda(install_dir)
            
            self._update_progress(90, "Setting up environment...")
            self._setup_environment(install_dir)
            
            self._update_progress(100, "Installation completed successfully!")
            
        except Exception as e:
            self._update_progress(
                self.state.installation_progress,
                f"Installation failed: {str(e)}"
            )
            self._log_message(f"Error: {str(e)}")
        finally:
            self.state.installation_running = False

    def _install_binaries(self, install_dir: Path):
        """Install pre-compiled binaries"""
        self._update_progress(30, "Detecting platform...")
        
        # Platform detection mapping to public asset tags
        short_map = {
            ("Linux", "x86_64"): "linux64",
            ("Linux", "aarch64"): "linux64",
            ("Darwin", "x86_64"): "macos64",
            ("Darwin", "arm64"): "macos64",
            ("Windows", "AMD64"): "win64",
        }
        platform_key = (platform.system(), platform.machine())
        base_tag = short_map.get(platform_key)
        if not base_tag:
            raise RuntimeError(f"No precompiled binaries available for {platform_key}")
        arch_tag = base_tag + ("-mpi" if self.state.enable_mpi else "")
        self._update_progress(40, f"Downloading SU2 {self.SU2_RELEASE} for {arch_tag}...")
        # Always download zip assets
        ext = "zip"
        filename = f"SU2-{self.SU2_RELEASE}-{arch_tag}.{ext}"
        url = f"{self.BIN_BASE_URL}/{self.SU2_RELEASE}/{filename}"
        dst = install_dir / filename
        
        self._download_with_progress(url, dst, 40, 70)
        
        self._update_progress(75, "Extracting archive...")
        
        # Extract
        if ext == "zip":
            with zipfile.ZipFile(dst) as zf:
                zf.extractall(install_dir)
        else:
            with tarfile.open(dst, "r:gz") as tf:
                tf.extractall(install_dir)
        
        dst.unlink()  # cleanup
        self._update_progress(85, "Binary installation complete")

    def _install_from_source(self, install_dir: Path):
        """Install from source code"""
        self._update_progress(30, "Cloning SU2 repository...")
        
        src_dir = install_dir.parent / "SU2_src"
        
        # Clone or update repository
        if src_dir.exists():
            self._run_command(["git", "-C", str(src_dir), "fetch", "--all", "--tags"])
            self._run_command(["git", "-C", str(src_dir), "checkout", self.SU2_RELEASE])
        else:
            self._run_command([
                "git", "clone", "--branch", self.SU2_RELEASE, "--depth", "1",
                "https://github.com/su2code/SU2.git", str(src_dir)
            ])
        
        self._update_progress(50, "Configuring build...")
        
        # Configure build
        os.chdir(src_dir)
        build_opts = [
            f"-Denable-pywrapper={'true' if self.state.enable_pywrapper else 'false'}",
            f"-Denable-mpi={'true' if self.state.enable_mpi else 'false'}",
            f"-Denable-autodiff={'true' if self.state.enable_autodiff else 'false'}",
            f"--prefix={install_dir}"
        ]
        
        self._run_command([sys.executable, "meson.py", "build"] + build_opts)
        
        self._update_progress(60, "Building SU2...")
        self._run_command(["ninja", "-C", "build", f"-j{self.state.parallel_jobs}"])
        
        self._update_progress(80, "Installing...")
        self._run_command(["ninja", "-C", "build", "install"])

    def _install_conda(self, install_dir: Path):
        """Install using conda"""
        self._update_progress(30, "Installing SU2 via conda...")
        
        version = self.SU2_RELEASE.lstrip('v')
        self._run_command([
            "conda", "install", "-y", "-c", "conda-forge",
            "--prefix", str(install_dir), f"su2={version}"
        ])

    def _setup_environment(self, install_dir: Path):
        """Set up environment variables"""
        env_script = f"""
# >>> SU2 automatically added by SU2_GUI <<<
export SU2_RUN="{install_dir / 'bin'}"
export SU2_HOME="{install_dir}"
export PATH="$SU2_RUN:$PATH"
export PYTHONPATH="$SU2_RUN:$PYTHONPATH"
# <<< End SU2 block <<<
"""
        
        rcfile = Path.home() / (".bashrc" if platform.system() != "Windows" else ".su2_env.bat")
        with open(rcfile, "a") as f:
            f.write("\n" + env_script + "\n")
        
        self._log_message(f"Environment variables added to {rcfile}")

    def _download_with_progress(self, url: str, dst: Path, start_pct: int, end_pct: int):
        """Download file with progress updates"""
        try:
            with urllib.request.urlopen(url) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(dst, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = start_pct + (end_pct - start_pct) * downloaded / total_size
                            self._update_progress(int(progress), f"Downloaded {downloaded}/{total_size} bytes")
                        
        except Exception as e:
            raise RuntimeError(f"Download failed: {str(e)}")

    def _run_command(self, cmd: list[str]):
        """Run shell command and capture output"""
        self._log_message(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            self._log_message(line.rstrip())
        
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"Command failed with code {process.returncode}")

    def _update_progress(self, progress: int, status: str):
        """Update installation progress and status"""
        # Update state in thread-safe manner
        async def update_state():
            self.state.installation_progress = progress
            self.state.installation_status = status
            self.state.flush()
        
        # Schedule state update in main event loop
        if hasattr(self.server, '_loop') and self.server._loop:
            asyncio.run_coroutine_threadsafe(update_state(), self.server._loop)

    def _log_message(self, message: str):
        """Add message to installation log"""
        async def update_log():
            self.state.installation_log += message + "\n"
            self.state.flush()
        
        # Schedule log update in main event loop  
        if hasattr(self.server, '_loop') and self.server._loop:
            asyncio.run_coroutine_threadsafe(update_log(), self.server._loop)

# Integration with existing SU2GUI
def create_installer_app(server=None):
    """Factory function to create installer app"""
    return SU2InstallerApp(server)

# CLI integration
if __name__ == "__main__":
    app = SU2InstallerApp()
    app.server.start()
