#!/bin/bash

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install it from https://www.python.org/downloads/macos/"
    read -r -p "Press Return to close..."
    exit 1
fi

if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV" || exit 1
fi

if ! "$PYTHON" -c 'import cv2, numpy, PyQt5; from PyQt5.QtCore import QLibraryInfo; raise SystemExit(QLibraryInfo.version().toString() != "5.15.18")' >/dev/null 2>&1; then
    "$PYTHON" -m pip install opencv-python-headless numpy PyQt5 'PyQt5-Qt5==5.15.18' || exit 1
fi

export QT_QPA_PLATFORM_PLUGIN_PATH="$("$PYTHON" -c 'from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath) + "/platforms")')"
exec "$PYTHON" "$ROOT/board_warp.py"
