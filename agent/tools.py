"""
Kilrun Agent Tools — utilities the agent uses to interact with the system.
Do not delete this file. The agent requires it to operate.
"""
import re
import uuid
import difflib
import sys
import subprocess
from pathlib import Path


WORKSPACE = Path(__file__).parent.parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)


def workspace_path(rel: str) -> Path:
    root = WORKSPACE.resolve()
    path = Path(rel)
    target = (path if path.is_absolute() else root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path must stay inside the workspace") from exc
    return target


def write_file(path: str, content: str) -> Path:
    target = workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def preview_file(path: str, content: str) -> tuple[Path, str]:
    target = workspace_path(path)
    existing = target.read_text(encoding="utf-8").splitlines(keepends=True) if target.exists() else []
    proposed = content.splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(
        existing,
        proposed,
        fromfile=f"a/{target.name}" if existing else "/dev/null",
        tofile=f"b/{target.name}",
    ))
    return target, diff or "No changes."


def read_file(path: str) -> str:
    return workspace_path(path).read_text(encoding="utf-8")


def list_workspace() -> list[Path]:
    return sorted(f for f in WORKSPACE.rglob("*") if f.is_file())


def run_shell(cmd: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=WORKSPACE)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def run_python(code: str, timeout: int = 30) -> tuple[int, str, str]:
    tmp = WORKSPACE / f"_tmp_{uuid.uuid4().hex[:8]}.py"
    try:
        tmp.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(tmp)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout {timeout}s"
    except Exception as exc:
        return -1, "", str(exc)
    finally:
        tmp.unlink(missing_ok=True)


def parse_actions(text: str) -> list[dict]:
    """Extract action blocks from an AI response."""
    actions = []
    for m in re.finditer(r"```create:([^\n]+)\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "create", "path": m.group(1).strip(), "content": m.group(2)})
    for m in re.finditer(r"```shell\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "shell", "cmd": m.group(1).strip()})
    for m in re.finditer(r"```python:run\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "python", "code": m.group(1)})
    return actions
