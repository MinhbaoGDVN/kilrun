#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f .venv/bin/python ]; then
    echo "[*] Tạo venv..."
    python3 -m venv .venv
    .venv/bin/pip install httpx rich --quiet
fi
.venv/bin/python agent/kilrun.py "$@"
