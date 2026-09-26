@echo off
chcp 65001 > nul
if not exist .venv\Scripts\python.exe (
    echo [!] Chua setup. Dang chay setup tu dong...
    python -m venv .venv
    .venv\Scripts\pip install httpx rich --quiet
)
.venv\Scripts\python agent\kilrun.py %*
