#!/usr/bin/env bash
# Build RockKingdomAuto.exe with PyInstaller
# Prerequisites:
#   - .venv with all dependencies installed
#   - PyInstaller in .venv
#   - interception.dll in project root
#
# Usage: bash build.sh

set -e

cd "$(dirname "$0")"
PYTHON=".venv/Scripts/python.exe"

echo "=== Building RockKingdomAuto.exe ==="
echo "Cleaning previous build..."
rm -rf build dist *.spec

echo "Running PyInstaller..."
"$PYTHON" -m PyInstaller \
    --onefile \
    --windowed \
    --name="RockKingdomAuto" \
    --add-data="interception.dll;." \
    --add-data="config.py;." \
    --add-data="src;src" \
    --add-data=".venv/Lib/site-packages/numpy/_core;numpy/_core" \
    --add-data=".venv/Lib/site-packages/numpy/lib;numpy/lib" \
    --add-data=".venv/Lib/site-packages/numpy/linalg;numpy/linalg" \
    --hidden-import=PySide6 \
    --hidden-import=qfluentwidgets \
    --hidden-import=ok \
    --hidden-import=numpy._core._multiarray_umath \
    --collect-all=qfluentwidgets \
    --collect-all=PySide6 \
    --collect-all=ok \
    --collect-all=numpy \
    main.py

echo ""
echo "=== Build complete ==="
ls -lh "dist/RockKingdomAuto.exe"
echo ""
echo "To release: upload dist/RockKingdomAuto.exe to GitHub Releases"
