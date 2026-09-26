@echo off
chcp 65001 > nul
if not exist .venv\Scripts\python.exe (
    echo [!] Setup not found. Starting automatic setup...
    python -m venv .venv
    .venv\Scripts\pip install httpx rich --quiet
)
.venv\Scripts\python agent\kilrun.py %*
