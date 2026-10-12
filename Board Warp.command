#!/bin/bash

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [ ! -x "$PYTHON" ] || ! "$PYTHON" -c 'from PyQt5.QtCore import QLibraryInfo; raise SystemExit(QLibraryInfo.version().toString() != "5.15.18")' >/dev/null 2>&1; then
    exec "$ROOT/Install and Launch Board Warp.command"
fi

export QT_QPA_PLATFORM_PLUGIN_PATH="$("$PYTHON" -c 'from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath) + "/platforms")')"
exec "$PYTHON" "$ROOT/board_warp.py"
