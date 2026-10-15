#!/usr/bin/env bash
# Build a standalone executable with PyInstaller.
#
#   bash scripts/build.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

echo '==> Running PyInstaller'
"$PYTHON" -m PyInstaller --noconfirm --clean mupen64plus_gui.spec

echo
echo "Build complete: $PROJECT_ROOT/dist/mupen64plus_gui"
