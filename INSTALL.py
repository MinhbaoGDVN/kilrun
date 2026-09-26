#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   KILRUN — Installer                         ║
║   Chạy file này một lần là xong.             ║
║   python INSTALL.py                          ║
╚══════════════════════════════════════════════╝
Tự tạo toàn bộ cấu trúc thư mục, cài deps, sẵn sàng dùng.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

# ══════════════════════════════════════════════════════════════════════════════
# CẤU TRÚC THƯ MỤC
# ══════════════════════════════════════════════════════════════════════════════
#
#  Kilrun/
#  ├── INSTALL.py            ← file này (xoá sau khi install xong)
#  ├── run.bat / run.sh      ← khởi động
#  │
#  ├── core/                 ← ENGINE — KHÔNG ĐƯỢC SỬA / XOÁ
#  │   ├── kilgoreai.py      ← API client
#  │   └── config.py         ← đọc .env
#  │
#  ├── agent/                ← AGENT RUNTIME
#  │   ├── kilrun.py         ← main TUI (chạy cái này)
#  │   └── tools.py          ← công cụ agent (file, shell, code)
#  │
#  ├── workspace/            ← NƠI AGENT LÀM VIỆC (tạo/sửa file tại đây)
#  │   └── .gitkeep
#  │
#  ├── scripts/              ← Script người dùng tự viết
#  │   └── example.py
#  │
#  ├── logs/                 ← Lịch sử chat, log lỗi
#  │   └── .gitkeep
#  │
#  └── .env                  ← API key & cấu hình
#
# ══════════════════════════════════════════════════════════════════════════════

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"

def p(msg): print(msg)
def ok(msg):   print(f"  {GREEN}✓{RESET}  {msg}")
def info(msg): print(f"  {CYAN}·{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}!{RESET}  {msg}")
def err(msg):  print(f"  {RED}✗{RESET}  {msg}")

# ── File contents ──────────────────────────────────────────────────────────────

FILES: dict[str, str] = {}

# ─────────────────────────────────────────────────────────────────────────────
FILES["core/kilgoreai.py"] = r'''"""
KilgoreAI Python Client — core engine. Đừng sửa file này.
API docs: https://apidocs.kilgoreai.xyz/
"""
import json
import httpx
from pathlib import Path
from typing import Iterator

BASE_URL = "https://apidocs.kilgoreai.xyz"

class KilgoreAI:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(headers=headers, cookies={}, timeout=60)

    def _url(self, path): return f"{self.base_url}{path}"
    def _post(self, path, **kw):
        r = self._client.post(self._url(path), **kw); r.raise_for_status(); return r
    def _get(self, path, **kw):
        r = self._client.get(self._url(path), **kw); r.raise_for_status(); return r

    # AUTH
    def create_api_key(self, name, ttl_days=None):
        b = {"name": name}
        if ttl_days: b["ttl_days"] = ttl_days
        return self._post("/v1/auth/api-keys", json=b).json()
    def list_api_keys(self): return self._get("/v1/auth/api-keys").json()
    def delete_api_key(self, key_id):
        r = self._client.delete(self._url(f"/v1/auth/api-keys/{key_id}")); r.raise_for_status(); return r.json()

    # MODELS
    def list_models(self): return self._get("/v1/models").json().get("data", [])
    def list_image_models(self): return self._get("/v1/images/models").json().get("data", [])

    # CHAT
    def chat(self, messages, model="claude-sonnet-5", system=None,
             conversation_id=None, web_search=False, stream=False, incognito=False):
        body = {"model": model, "messages": messages, "stream": stream}
        if system: body["system"] = system
        if conversation_id: body["conversation_id"] = conversation_id
        if web_search: body["web_search"] = True
        if incognito: body["incognito"] = True
        if stream: return self._stream_chat(body)
        return self._post("/v1/chat/completions", json=body).json()["choices"][0]["message"]["content"]

    def _stream_chat(self, body) -> Iterator[str]:
        with self._client.stream("POST", self._url("/v1/chat/completions"), json=body) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload == "[DONE]": break
                    try:
                        delta = json.loads(payload)["choices"][0]["delta"].get("content","")
                        if delta: yield delta
                    except: continue

    def messages(self, messages, model="claude-sonnet-5", system=None, max_tokens=1024):
        body = {"model": model, "messages": messages, "max_tokens": max_tokens}
        if system: body["system"] = system
        return self._post("/v1/messages", json=body).json()["content"][0]["text"]

    # IMAGE
    def generate_image(self, prompt, model="flux-1.1-pro", n=1, size="1024x1024"):
        r = self._post("/v1/images/generations", json={"model":model,"prompt":prompt,"n":n,"size":size}).json()
        return [i.get("url") or f"data:image/png;base64,{i['b64_json']}" for i in r.get("data",[])]

    # TTS
    def list_voices(self): return self._get("/v1/tts/voices").json()
    def tts(self, text, voice=None, rate=1.0, pitch=1.0, save_path=None):
        body = {"text": text, "rate": rate, "pitch": pitch}
        if voice: body["voice"] = voice
        audio = self._post("/v1/tts", json=body).content
        if save_path: Path(save_path).write_bytes(audio)
        return audio

    # FILES
    def upload_file(self, file_path, incognito=False):
        path = Path(file_path)
        hdrs = {"X-Incognito":"1"} if incognito else {}
        with open(path,"rb") as f:
            r = self._client.post(self._url("/v1/files"), files={"file":(path.name,f)}, headers=hdrs)
        r.raise_for_status(); return r.json()
    def list_files(self): return self._get("/v1/files").json()
    def delete_file(self, fid):
        r = self._client.delete(self._url(f"/v1/files/{fid}")); r.raise_for_status(); return r.json()

    # CONVERSATIONS
    def list_conversations(self): return self._get("/v1/conversations").json()
    def get_conversation(self, key): return self._get(f"/v1/conversations/{key}").json()
    def delete_conversation(self, key):
        r = self._client.delete(self._url(f"/v1/conversations/{key}")); r.raise_for_status(); return r.json()
    def rename_conversation(self, key, title):
        r = self._client.patch(self._url(f"/v1/conversations/{key}"), json={"title":title}); r.raise_for_status(); return r.json()

    # VIDEO
    def generate_video(self, prompt, model="video-ltx-2.5", duration=5, aspect_ratio="16:9"):
        return self._post("/v1/videos/generations",
            json={"model":model,"prompt":prompt,"duration":duration,"aspect_ratio":aspect_ratio}).json()["ticket"]
    def video_status(self, ticket): return self._get(f"/v1/videos/status/{ticket}").json()

    # HEALTH
    def health(self): return self._get("/v1/health").json()
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["core/config.py"] = r'''"""
Cấu hình Kilrun — đọc từ .env trong thư mục gốc.
"""
import os
from pathlib import Path

def _load_dotenv():
    env = Path(__file__).parent.parent / ".env"
    if not env.exists(): return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()

API_KEY           = os.getenv("KILGORE_API_KEY") or None
DEFAULT_MODEL     = os.getenv("KILGORE_MODEL", "claude-sonnet-5")
DEFAULT_IMG_MODEL = os.getenv("KILGORE_IMAGE_MODEL", "flux-1.1-pro")
DEFAULT_VID_MODEL = os.getenv("KILGORE_VIDEO_MODEL", "video-ltx-2.5")
SYSTEM_PROMPT     = os.getenv("KILGORE_SYSTEM") or None
BASE_URL          = os.getenv("KILGORE_BASE_URL", "https://apidocs.kilgoreai.xyz")
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["agent/tools.py"] = r'''"""
Kilrun Agent Tools — công cụ cho agent dùng để tương tác với hệ thống.
KHÔNG xoá file này. Agent cần nó để hoạt động.
"""
import re
import uuid
import subprocess
from pathlib import Path


WORKSPACE = Path(__file__).parent.parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)


def workspace_path(rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    return (WORKSPACE / p).resolve()


def write_file(path: str, content: str) -> Path:
    target = workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


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
    tmp.write_text(code, encoding="utf-8")
    rc, out, err = run_shell(f'python "{tmp}"', timeout)
    tmp.unlink(missing_ok=True)
    return rc, out, err


def parse_actions(text: str) -> list[dict]:
    """Trích xuất action block từ response AI."""
    actions = []
    for m in re.finditer(r"```create:([^\n]+)\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "create", "path": m.group(1).strip(), "content": m.group(2)})
    for m in re.finditer(r"```shell\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "shell", "cmd": m.group(1).strip()})
    for m in re.finditer(r"```python:run\n(.*?)```", text, re.DOTALL):
        actions.append({"type": "python", "code": m.group(1)})
    return actions
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["agent/kilrun.py"] = r'''#!/usr/bin/env python3
"""
██╗  ██╗██╗██╗     ██████╗ ██╗   ██╗███╗   ██╗
██║ ██╔╝██║██║     ██╔══██╗██║   ██║████╗  ██║
█████╔╝ ██║██║     ██████╔╝██║   ██║██╔██╗ ██║
██╔═██╗ ██║██║     ██╔══██╗██║   ██║██║╚██╗██║
██║  ██╗██║███████╗██║  ██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
Kilrun · AI Agent Terminal · kilgoreai.xyz
"""
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime

# Thêm core/ vào path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Confirm
    from rich import box
except ImportError:
    print("Thiếu rich. Chạy: pip install rich")
    sys.exit(1)

try:
    import config
    from kilgoreai import KilgoreAI
    import tools
except ImportError as e:
    print(f"Lỗi import: {e}")
    sys.exit(1)

# ── Console ────────────────────────────────────────────────────────────────────
console = Console()

BANNER = """\
[bold #6c63ff]██╗  ██╗██╗██╗     ██████╗ ██╗   ██╗███╗   ██╗
██║ ██╔╝██║██║     ██╔══██╗██║   ██║████╗  ██║
█████╔╝ ██║██║     ██████╔╝██║   ██║██╔██╗ ██║
██╔═██╗ ██║██║     ██╔══██╗██║   ██║██║╚██╗██║
██║  ██╗██║███████╗██║  ██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/]
[dim #a78bfa]AI Agent Terminal · kilgoreai.xyz[/]"""

AGENT_SYSTEM = """Bạn là Kilrun — AI agent chạy trực tiếp trên terminal.

Bạn CÓ THỂ tạo file và chạy lệnh bằng cú pháp sau:

Tạo file:
```create:tên_file.py
# nội dung
```

Chạy shell:
```shell
lệnh
```

Chạy Python trực tiếp:
```python:run
print("hello")
```

Mọi file tạo ra nằm trong workspace/.
Giải thích ngắn trước khi làm. Trả lời tiếng Việt.
"""

HELP_TEXT = """
## ⚡ Kilrun — Commands

| Lệnh | Mô tả |
|------|-------|
| `/mode chat` | Chat thường |
| `/mode agent` | Agent tự code, tạo file, chạy lệnh |
| `/model <id>` | Đổi model |
| `/search on\|off` | Bật/tắt web search |
| `/files` | Xem workspace |
| `/exec <cmd>` | Chạy shell trực tiếp |
| `/image <prompt>` | Sinh ảnh |
| `/tts <text>` | Text → MP3 |
| `/models` | Danh sách models |
| `/clear` | Xoá lịch sử |
| `/save` | Lưu chat vào logs/ |
| `/status` | Thông tin session |
| `/help` | Bảng này |
| `/exit` | Thoát |

## 🤖 Agent mode
AI tự tạo file vào `workspace/`, tự chạy code.
Mỗi hành động sẽ hỏi xác nhận trước khi thực thi.

## ⌨️  Shortcuts
`Enter` gửi · `Ctrl+C` huỷ · `/exit` thoát
"""


# ── UI helpers ─────────────────────────────────────────────────────────────────

def print_user(msg: str):
    console.print(Panel(
        Text(msg, style="white"),
        title="[bold #38bdf8]You[/]",
        border_style="#38bdf8",
        padding=(0, 1),
    ))

def to_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return chr(10).join(to_text(item) for item in value)
    if isinstance(value, dict):
        if "text" in value:
            return to_text(value["text"])
        if "content" in value:
            return to_text(value["content"])
    return str(value)


def print_ai(msg, mode: str = "chat"):
    color = "#a78bfa" if mode == "chat" else "#34d399"
    label = "Kilrun" if mode == "chat" else "Kilrun [bold]⚡ Agent[/bold]"
    msg = to_text(msg)

    try:
        content = Markdown(msg)
    except (TypeError, ValueError):
        content = Text(msg)

    console.print(Panel(
        content,
        title="[bold " + color + "]" + label + "[/]",
        border_style=color,
        padding=(0, 1)
    ))


def print_exec(kind: str, detail: str, rc: int, out: str, err: str):
    icon = "✓" if rc == 0 else "✗"
    clr = "green" if rc == 0 else "red"
    out = to_text(out).strip()
    err = to_text(err).strip()

    console.print(
        chr(10) + " [" + clr + "]" + icon + "[/] "
        + "[dim]" + to_text(kind) + "[/] "
        + "[italic]" + to_text(detail) + "[/]"
    )

    if out:
        console.print(Syntax(
            out,
            "text",
            background_color="default",
            line_numbers=False
        ))

    if err:
        console.print(Text(" stderr: " + err, style="red dim"))



def show_status(model, mode, search):
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim"); t.add_column()
    t.add_row("model",   f"[#6c63ff]{model}[/]")
    t.add_row("mode",    f"[#34d399]{mode}[/]" if mode=="agent" else f"[#38bdf8]{mode}[/]")
    t.add_row("search",  "[green]on[/]" if search else "[dim]off[/]")
    t.add_row("workspace", str(tools.WORKSPACE))
    t.add_row("time",    datetime.now().strftime("%H:%M · %d/%m/%Y"))
    console.print(Panel(t, title="[dim]session[/]", border_style="dim", padding=(0,1)))


# ── Session ────────────────────────────────────────────────────────────────────

class Session:
    def __init__(self):
        self.ai      = KilgoreAI(api_key=config.API_KEY)
        self.history : list[dict] = []
        self.conv_id = str(uuid.uuid4())
        self.model   = config.DEFAULT_MODEL
        self.mode    = "chat"
        self.search  = False
        self.logs_dir = ROOT / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def send(self, user_input: str):
        system = AGENT_SYSTEM if self.mode == "agent" else (config.SYSTEM_PROMPT or None)
        self.history.append({"role": "user", "content": user_input})
        print_user(user_input)

        with console.status(f"[dim #6c63ff]⠋ {self.model}[/]", spinner="dots",
                            spinner_style="#6c63ff"):
            try:
                reply = self.ai.chat(
                    self.history, model=self.model, system=system,
                    web_search=self.search, conversation_id=self.conv_id,
                )
            except Exception as e:
                console.print(f"[red]✗ API error:[/] {e}")
                self.history.pop(); return

        self.history.append({"role": "assistant", "content": reply})
        print_ai(reply, mode=self.mode)

        if self.mode == "agent":
            reply = to_text(reply)
            for action in tools.parse_actions(reply):
                if action["type"] == "create":
                    p = tools.write_file(action["path"], action["content"])
                    console.print(f"\n  [green]✓ created[/] [dim]{p}[/]")

                elif action["type"] == "shell":
                    cmd = action["cmd"]
                    if Confirm.ask(f"\n  [yellow]run shell:[/] [dim]{cmd}[/]", default=True):
                        with console.status("[dim]running...[/]"):
                            rc, out, err = tools.run_shell(cmd)
                        print_exec("shell", cmd, rc, out, err)
                        self.history.append({"role":"user","content":f"Output:\n```\n{out}{err}\n```"})

                elif action["type"] == "python":
                    if Confirm.ask("\n  [yellow]run python?[/]", default=True):
                        with console.status("[dim]python...[/]"):
                            rc, out, err = tools.run_python(action["code"])
                        print_exec("python", "(inline)", rc, out, err)
                        self.history.append({"role":"user","content":f"Output:\n```\n{out}{err}\n```"})

    def command(self, line: str):
        parts = line.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/exit":
            console.print("[dim]Bye 👋[/]"); raise SystemExit(0)

        elif cmd == "/help":
            console.print(Panel(Markdown(HELP_TEXT), title="[bold #6c63ff]Help[/]",
                                border_style="#6c63ff"))

        elif cmd == "/status":
            show_status(self.model, self.mode, self.search)

        elif cmd == "/mode":
            if arg in ("chat","agent"):
                self.mode = arg
                icon = "⚡" if arg == "agent" else "💬"
                console.print(f"  [dim]→ {icon} mode: [bold]{self.mode}[/][/]")
            else:
                console.print("[yellow]Dùng: /mode chat | /mode agent[/]")

        elif cmd == "/model":
            if arg: self.model = arg; console.print(f"  [dim]→ model: [bold #6c63ff]{self.model}[/][/]")
            else: console.print("[yellow]/model <tên>[/]")

        elif cmd == "/search":
            self.search = arg.lower() not in ("off","0","false")
            console.print(f"  [dim]→ search: [bold]{'on' if self.search else 'off'}[/][/]")

        elif cmd == "/clear":
            self.history.clear()
            self.conv_id = str(uuid.uuid4())
            console.clear()
            console.print(BANNER); console.print()
            console.print("[dim]Lịch sử đã xoá.[/]")

        elif cmd == "/save":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = self.logs_dir / f"chat_{ts}.json"
            out.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")
            console.print(f"  [green]✓[/] Đã lưu: [dim]{out}[/]")

        elif cmd == "/files":
            files = tools.list_workspace()
            if not files: console.print("[dim]workspace/ trống.[/]"); return
            t = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
            t.add_column(style="#6c63ff"); t.add_column(style="dim")
            for f in files:
                t.add_row(str(f.relative_to(tools.WORKSPACE)), f"{f.stat().st_size:,}B")
            console.print(Panel(t, title="[dim]workspace/[/]", border_style="dim"))

        elif cmd == "/exec":
            if not arg: console.print("[yellow]/exec <lệnh>[/]"); return
            with console.status(f"[dim]$ {arg}[/]"):
                rc, out, err = tools.run_shell(arg)
            print_exec("shell", arg, rc, out, err)

        elif cmd == "/image":
            if not arg: console.print("[yellow]/image <prompt>[/]"); return
            with console.status("[dim]Đang sinh ảnh...[/]"):
                try:
                    urls = self.ai.generate_image(arg)
                    for u in urls: console.print(f"  [green]✓[/] {u}")
                except Exception as e: console.print(f"  [red]✗[/] {e}")

        elif cmd == "/tts":
            if not arg: console.print("[yellow]/tts <văn bản>[/]"); return
            out = tools.WORKSPACE / "tts_output.mp3"
            with console.status("[dim]Đang tạo audio...[/]"):
                try:
                    self.ai.tts(arg, save_path=out)
                    console.print(f"  [green]✓[/] Đã lưu: [dim]{out}[/]")
                except Exception as e: console.print(f"  [red]✗[/] {e}")

        elif cmd == "/models":
            with console.status("[dim]Đang tải...[/]"):
                try:
                    ms = self.ai.list_models()
                    t = Table(box=box.SIMPLE, show_header=False)
                    t.add_column(style="#6c63ff")
                    for m in ms: t.add_row(m if isinstance(m,str) else m.get("id","?"))
                    console.print(t)
                except Exception as e: console.print(f"[red]Lỗi:[/] {e}")

        else:
            console.print(f"[yellow]Lệnh không biết: {cmd}  (gõ /help)[/]")

    def run(self):
        console.print(BANNER); console.print()
        show_status(self.model, self.mode, self.search)
        console.print("[dim]  /help · /mode agent · Ctrl+C thoát[/]\n")

        while True:
            try:
                icon = "⚡" if self.mode == "agent" else "💬"
                srch = " [dim]🔍[/]" if self.search else ""
                line = console.input(f"{icon} [bold #6c63ff]kilrun[/][dim]›[/]{srch} ").strip()
                if not line: continue
                if line.startswith("/"): self.command(line)
                else: self.send(line)
            except KeyboardInterrupt:
                console.print("\n[dim]Ctrl+C · gõ /exit để thoát[/]")
            except SystemExit: break
            except EOFError: break


def main():
    import argparse
    p = argparse.ArgumentParser(prog="kilrun", description="Kilrun AI Agent Terminal",
                                epilog="Gõ /help để xem tất cả lệnh")
    p.add_argument("--agent",  "-a", action="store_true", help="Bắt đầu ở agent mode")
    p.add_argument("--model",  "-m", default=None)
    p.add_argument("--search", "-s", action="store_true")
    p.add_argument("prompt", nargs="*", help="Gửi prompt ngay rồi vào loop")
    args = p.parse_args()

    s = Session()
    if args.model:  s.model  = args.model
    if args.agent:  s.mode   = "agent"
    if args.search: s.search = True
    if args.prompt:
        console.print(BANNER); console.print()
        s.send(" ".join(args.prompt))
        console.print()
    s.run()


if __name__ == "__main__":
    main()
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["scripts/example.py"] = r'''"""
Ví dụ script dùng KilgoreAI trực tiếp.
Chạy: python scripts/example.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

import config
from kilgoreai import KilgoreAI

ai = KilgoreAI(api_key=config.API_KEY)

reply = ai.chat([{"role": "user", "content": "Hello! Giới thiệu ngắn về bạn."}])
print(reply)
'''

FILES["workspace/.gitkeep"] = ""
FILES["logs/.gitkeep"] = ""

FILES[".env"] = """\
# Kilrun Configuration
# Để trống KILGORE_API_KEY cũng được — API vẫn hoạt động qua cookie

KILGORE_API_KEY=
KILGORE_MODEL=claude-sonnet-5
KILGORE_IMAGE_MODEL=flux-1.1-pro
KILGORE_VIDEO_MODEL=video-ltx-2.5
KILGORE_SYSTEM=
"""

FILES["run.bat"] = """\
@echo off
chcp 65001 > nul
if not exist .venv\\Scripts\\python.exe (
    echo [!] Chua setup. Dang chay setup tu dong...
    python -m venv .venv
    .venv\\Scripts\\pip install httpx rich --quiet
)
.venv\\Scripts\\python agent\\kilrun.py %*
"""

FILES["run.sh"] = """\
#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f .venv/bin/python ]; then
    echo "[*] Tạo venv..."
    python3 -m venv .venv
    .venv/bin/pip install httpx rich --quiet
fi
.venv/bin/python agent/kilrun.py "$@"
"""

FILES["requirements.txt"] = "httpx>=0.27\nrich>=13.0\n"


# ══════════════════════════════════════════════════════════════════════════════
# INSTALLER
# ══════════════════════════════════════════════════════════════════════════════

def install():
    p(f"\n{BOLD}{CYAN}╔══════════════════════════════════════╗")
    p(f"║   KILRUN Installer                   ║")
    p(f"╚══════════════════════════════════════╝{RESET}\n")
    p(f"{DIM}Thư mục gốc: {ROOT}{RESET}\n")

    # 1. Tạo thư mục
    dirs = ["core", "agent", "workspace", "scripts", "logs"]
    p(f"{BOLD}[1/3] Tạo cấu trúc thư mục{RESET}")
    for d in dirs:
        path = ROOT / d
        path.mkdir(exist_ok=True)
        ok(d + "/")

    # 2. Ghi files
    p(f"\n{BOLD}[2/3] Ghi files{RESET}")
    for rel, content in FILES.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and rel in (".env",):
            info(f"Giữ nguyên: {rel}")
            continue
        target.write_text(content, encoding="utf-8")
        ok(rel)

    # chmod run.sh trên Linux/Mac
    sh = ROOT / "run.sh"
    if sh.exists():
        try: sh.chmod(0o755)
        except: pass

    # 3. Cài dependencies
    p(f"\n{BOLD}[3/3] Cài môi trường Python (.venv){RESET}")
    venv = ROOT / ".venv"

    if not venv.exists():
        info("Tạo .venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        ok(".venv/ tạo xong")
    else:
        info(".venv/ đã tồn tại, bỏ qua")

    pip = venv / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    info("Cài httpx + rich ...")
    subprocess.run([str(pip), "install", "httpx", "rich", "--quiet"], check=True)
    ok("httpx + rich đã cài")

    # Done
    p(f"\n{BOLD}{GREEN}╔══════════════════════════════════════╗")
    p(f"║   ✓  Cài đặt hoàn tất!              ║")
    p(f"╚══════════════════════════════════════╝{RESET}")
    p(f"""
{BOLD}Cấu trúc:{RESET}
  {CYAN}core/{RESET}         ← Engine (không sửa/xoá)
  {CYAN}agent/{RESET}        ← Kilrun AI agent
  {CYAN}workspace/{RESET}    ← Nơi agent tạo file
  {CYAN}scripts/{RESET}      ← Scripts của bạn
  {CYAN}logs/{RESET}         ← Lịch sử chat
  {CYAN}.env{RESET}          ← Cấu hình & API key

{BOLD}Chạy ngay:{RESET}
  Windows:  {GREEN}run.bat{RESET}
  Linux:    {GREEN}./run.sh{RESET}

  Bắt đầu agent mode:
  Windows:  {GREEN}run.bat --agent{RESET}
  Linux:    {GREEN}./run.sh --agent{RESET}

{DIM}Sửa .env để thêm API key (không bắt buộc){RESET}
""")


if __name__ == "__main__":
    install()
