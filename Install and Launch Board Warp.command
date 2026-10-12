#!/bin/bash

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
PYTHON_BIN=""

for candidate in \
    "/Library/Frameworks/Python.framework/Versions/3.15/bin/python3.15" \
    "$(command -v python3.15 2>/dev/null || true)" \
    "$(command -v python3 2>/dev/null || true)"
do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3 is required. Install it from https://www.python.org/downloads/macos/"
    read -r -p "Press Return to close..."
    exit 1
fi

if [ ! -x "$PYTHON" ]; then
    "$PYTHON_BIN" -m venv "$VENV" || exit 1
fi

if ! "$PYTHON" -c 'import cv2, numpy, PyQt5; from PyQt5.QtCore import QLibraryInfo; raise SystemExit(QLibraryInfo.version().toString() != "5.15.18")' >/dev/null 2>&1; then
    "$PYTHON" -m pip install opencv-python-headless numpy PyQt5 'PyQt5-Qt5==5.15.18' || exit 1
fi

exec "$PYTHON" "$ROOT/board_warp.py"
