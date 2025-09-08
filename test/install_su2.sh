#!/bin/bash
# SU2 Installation Script for Linux/macOS
# This script provides an easy way to install SU2 on Unix-like systems

echo ""
echo "============================================================"
echo "                   SU2 Installation Tool"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and try again"
        echo ""
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if the installer script exists
if [ ! -f "$SCRIPT_DIR/install_su2.py" ]; then
    echo "ERROR: install_su2.py not found in $SCRIPT_DIR"
    echo "Please ensure this script is in the same directory as install_su2.py"
    echo ""
    exit 1
fi

echo "Choose installation mode:"
echo "  1. Install using pre-compiled binaries (recommended)"
echo "  2. Install using conda"
echo "  3. Install from source code"
echo "  4. Validate existing installation"
echo "  5. Show system information"
echo "  6. Uninstall SU2"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "Installing SU2 using pre-compiled binaries..."
        $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --mode binaries
        ;;
    2)
        echo ""
        echo "Installing SU2 using conda..."
        $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --mode conda
        ;;
    3)
        echo ""
        echo "Installing SU2 from source code..."
        echo "This may take a while and requires build tools..."
        read -p "Continue? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --mode source
        else
            echo "Installation cancelled."
        fi
        ;;
    4)
        echo ""
        echo "Validating existing SU2 installation..."
        $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --validate
        ;;
    5)
        echo ""
        echo "Showing system information..."
        $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --info
        ;;
    6)
        echo ""
        echo "Uninstalling SU2..."
        $PYTHON_CMD "$SCRIPT_DIR/install_su2.py" --uninstall --remove-env
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    echo "Operation completed successfully!"
else
    echo "Operation failed with errors."
fi

echo ""
read -p "Press Enter to continue..."
