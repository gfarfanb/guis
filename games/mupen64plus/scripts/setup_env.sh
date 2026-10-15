#!/usr/bin/env bash
# Create the local virtual environment and install every dependency.
#
#   bash scripts/setup_env.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo '==> Creating virtual environment (.venv)'
    python -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

echo '==> Upgrading pip'
"$PYTHON" -m pip install --upgrade pip

echo '==> Installing dependencies (PySide6, PyInstaller)'
"$PYTHON" -m pip install -r requirements.txt

echo
echo 'Environment ready.'
echo "  Activate : source .venv/bin/activate"
echo "  Run      : python mupen64plus_gui.py"
echo "  Build    : pyinstaller mupen64plus_gui.spec"
