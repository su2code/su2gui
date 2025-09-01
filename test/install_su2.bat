@echo off
REM SU2 Installation Script for Windows
REM This script provides an easy way to install SU2 on Windows systems

echo.
echo ============================================================
echo                   SU2 Installation Tool
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    echo.
    pause
    exit /b 1
)

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Check if the installer script exists
if not exist "%SCRIPT_DIR%install_su2.py" (
    echo ERROR: install_su2.py not found in %SCRIPT_DIR%
    echo Please ensure this script is in the same directory as install_su2.py
    echo.
    pause
    exit /b 1
)

echo Choose installation mode:
echo   1. Install using pre-compiled binaries (recommended)
echo   2. Install using conda
echo   3. Install from source code
echo   4. Validate existing installation
echo   5. Show system information
echo   6. Uninstall SU2
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo Installing SU2 using pre-compiled binaries...
    python "%SCRIPT_DIR%install_su2.py" --mode binaries
) else if "%choice%"=="2" (
    echo.
    echo Installing SU2 using conda...
    python "%SCRIPT_DIR%install_su2.py" --mode conda
) else if "%choice%"=="3" (
    echo.
    echo Installing SU2 from source code...
    echo This may take a while and requires build tools...
    set /p confirm="Continue? (y/N): "
    if /i "!confirm!"=="y" (
        python "%SCRIPT_DIR%install_su2.py" --mode source
    ) else (
        echo Installation cancelled.
    )
) else if "%choice%"=="4" (
    echo.
    echo Validating existing SU2 installation...
    python "%SCRIPT_DIR%install_su2.py" --validate
) else if "%choice%"=="5" (
    echo.
    echo Showing system information...
    python "%SCRIPT_DIR%install_su2.py" --info
) else if "%choice%"=="6" (
    echo.
    echo Uninstalling SU2...
    python "%SCRIPT_DIR%install_su2.py" --uninstall --remove-env
) else (
    echo Invalid choice. Please run the script again.
)

echo.
if %errorlevel% equ 0 (
    echo Operation completed successfully!
) else (
    echo Operation failed with errors.
)

echo.
pause
