#!/bin/bash

ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/.venv/bin/python" "$ROOT/board_warp.py"
