#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   KILRUN — Installer                         ║
║   Run this file once to set everything up.   ║
║   python INSTALL.py                          ║
╚══════════════════════════════════════════════╝
Automatically creates the project structure, installs dependencies, and gets Kilrun ready to use.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

# ══════════════════════════════════════════════════════════════════════════════
# PROJECT STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
#
#  Kilrun/
#  ├── INSTALL.py            ← this file (can be deleted after installation)
#  ├── run.bat / run.sh      ← launch scripts
#  │
#  ├── core/                 ← ENGINE — DO NOT MODIFY OR DELETE
#  │   ├── kilgoreai.py      ← API client
#  │   └── config.py         ← reads .env
#  │
#  ├── agent/                ← AGENT RUNTIME
#  │   ├── kilrun.py         ← main TUI (run this)
#  │   └── tools.py          ← agent tools (files, shell, code)
#  │
#  ├── workspace/            ← AGENT WORKSPACE (create and edit files here)
#  │   └── .gitkeep
#  │
#  ├── scripts/              ← user-created scripts
#  │   └── example.py
#  │
#  ├── logs/                 ← chat history and error logs
#  │   └── .gitkeep
#  │
#  └── .env                  ← API key and configuration
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
KilgoreAI Python Client — core engine. Do not modify this file.
API docs: https://apidocs.kilgoreai.xyz/
"""
import sys
import uuid
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

BASE_URL = "https://apidocs.kilgoreai.xyz"

class KilgoreAI:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(headers=headers, cookies={}, timeout=300)

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
Kilrun configuration — read from the .env file in the project root.
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
Kilrun Agent Tools — utilities the agent uses to interact with the system.
Do not delete this file. The agent requires it to operate.
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
    """Extract action blocks from an AI response."""
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
import re
import shlex
import subprocess
from pathlib import Path
from datetime import datetime

# Add core/ to the import path.
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
    print("The rich package is missing. Install it with: pip install rich")
    sys.exit(1)

try:
    import config
    from kilgoreai import KilgoreAI
    import tools
except ImportError as e:
    print(f"Import error: {e}")
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

AGENT_SYSTEM = """You are Kilrun, an AI agent running directly in the terminal.

You CAN create files and run commands using the following syntax:

Create a file:
```create:filename.py
# file contents
```

Run a shell command:
```shell
command
```

Run Python directly:
```python:run
print("hello")
```

All created files must be placed in workspace/.
Briefly explain what you are about to do. Respond in English.
"""

HELP_TEXT = """
## ⚡ Kilrun — Commands

| Command | Description |
|------|-------|
| `/mode chat` | Standard chat |
| `/mode agent` | Let the agent write code, create files, and run commands |
| `/model <id>` | Change the model |
| `/search on\|off` | Toggle web search |
| `/files` | List workspace files |
| `/exec <cmd>` | Run a shell command directly |
| `/image <prompt>` | Generate an image |
| `/tts <text>` | Convert text to MP3 |
| `/models` | List available models |
| `/clear` | Clear conversation history |
| `/save` | Save the chat to logs/ |
| `/status` | Show session information |
| `/help` | Show this help menu |
| `/copy [number]` | Copy a reply or a code block |
| `/multi` | Enter a multiline prompt; type `.` on a line by itself to send |
| `/attach <path> [path ...]` | Attach local images or documents to the next message |
| `/exit` | Exit |

## 🤖 Agent mode
The AI can create files in `workspace/` and run code.
You will be asked to confirm each action before it is executed.

## ⌨️  Shortcuts
`Enter` send · `Ctrl+C` cancel · `/exit` exit
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

def extract_code_blocks(message):
    message = to_text(message)

    matches = re.findall(
        r"```[^\r\n]*\r?\n(.*?)```",
        message,
        flags=re.DOTALL
    )

    return [code.rstrip("\r\n") for code in matches]


def copy_to_clipboard(text):
    text = to_text(text)

    try:
        if sys.platform == "win32":
            process = subprocess.run(
                ["clip"],
                input=text,
                text=True,
                check=True
            )
        elif sys.platform == "darwin":
            process = subprocess.run(
                ["pbcopy"],
                input=text,
                text=True,
                check=True
            )
        else:
            clipboard_commands = [
                ["wl-copy"],
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
            ]

            process = None

            for command in clipboard_commands:
                try:
                    process = subprocess.run(
                        command,
                        input=text,
                        text=True,
                        check=True
                    )
                    break
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue

            if process is None:
                raise RuntimeError(
                    "Could not find wl-copy, xclip, or xsel"
                )

        return True, ""

    except Exception as exc:
        return False, str(exc)

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

    blocks = extract_code_blocks(msg)

    if blocks:
        commands = "  ".join(
            "[bold #a78bfa]/copy " + str(index) + "[/]"
            for index in range(1, len(blocks) + 1)
        )
        console.print(
            "  [dim]Copy code:[/] "
            + commands
            + "  [dim]| full reply: /copy[/]"
        )
    else:
        console.print("  [dim]Copy reply: [bold]/copy[/][/]")



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
        self.pending_attachments: list[Path] = []
        self.logs_dir = ROOT / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def send(self, user_input: str):
        system = AGENT_SYSTEM if self.mode == "agent" else (config.SYSTEM_PROMPT or None)
        attachment_names = [path.name for path in self.pending_attachments]
        display_text = user_input
        if attachment_names:
            display_text += "\n\nAttachments: " + ", ".join(attachment_names)
        print_user(display_text)

        with console.status(f"[dim #6c63ff]⠋ {self.model}[/]", spinner="dots",
                            spinner_style="#6c63ff"):
            try:
                content = user_input
                if self.pending_attachments:
                    content = [{"type": "text", "text": user_input}]
                    for path in self.pending_attachments:
                        uploaded = self.ai.upload_file(path)
                        content.append({"type": "file_id", "file_id": uploaded["id"]})

                self.history.append({"role": "user", "content": content})
                reply = self.ai.chat(
                    self.history, model=self.model, system=system,
                    web_search=self.search, conversation_id=self.conv_id,
                )
            except Exception as e:
                console.print(f"[red]✗ API error:[/] {e}")
                if self.history and self.history[-1].get("role") == "user":
                    self.history.pop()
                return

        self.pending_attachments.clear()

        reply = to_text(reply)
        self.last_reply = reply
        self.history.append({"role": "assistant", "content": reply})
        print_ai(reply, mode=self.mode)

        if self.mode == "agent":
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
                console.print("[yellow]Usage: /mode chat | /mode agent[/]")

        elif cmd == "/model":
            if arg: self.model = arg; console.print(f"  [dim]→ model: [bold #6c63ff]{self.model}[/][/]")
            else: console.print("[yellow]Usage: /model <name>[/]")

        elif cmd == "/search":
            self.search = arg.lower() not in ("off","0","false")
            console.print(f"  [dim]→ search: [bold]{'on' if self.search else 'off'}[/][/]")

        elif cmd == "/copy":
            if not self.last_reply:
                console.print(
                    "[yellow]There is no AI response to copy yet.[/]"
                )
                return

            if not arg:
                text_to_copy = self.last_reply
                description = "the full reply"
            else:
                try:
                    block_number = int(arg)
                except ValueError:
                    console.print(
                        "[yellow]Usage: /copy or /copy <code block number>[/]"
                    )
                    return

                blocks = extract_code_blocks(self.last_reply)

                if block_number < 1 or block_number > len(blocks):
                    console.print(
                        "[yellow]There is no code block number "
                        + str(block_number)
                        + ". There are "
                        + str(len(blocks))
                        + " code block(s).[/]"
                    )
                    return

                text_to_copy = blocks[block_number - 1]
                description = "code block " + str(block_number)

            copied, error = copy_to_clipboard(text_to_copy)

            if copied:
                console.print(
                    "  [green]✓[/] Copied "
                    + description
                    + " to the clipboard."
                )
            else:
                console.print(
                    "[red]Could not copy:[/] " + error
                )

        elif cmd == "/attach":
            if not arg:
                console.print("[yellow]Usage: /attach <path> [path ...][/]")
                return

            try:
                raw_paths = shlex.split(arg, posix=False)
            except ValueError as exc:
                console.print(f"[red]Invalid attachment path:[/] {exc}")
                return

            queued = []
            for raw_path in raw_paths:
                cleaned_path = raw_path.strip('"\'')
                path = Path(cleaned_path).expanduser().resolve()
                if not path.is_file():
                    console.print(f"[yellow]File not found:[/] {path}")
                    continue
                if path.stat().st_size > 25 * 1024 * 1024:
                    console.print(f"[yellow]File exceeds the 25 MB limit:[/] {path.name}")
                    continue
                if path not in self.pending_attachments:
                    self.pending_attachments.append(path)
                    queued.append(path.name)

            if queued:
                console.print("  [green]✓[/] Queued: " + ", ".join(queued))
            if self.pending_attachments:
                console.print("  [dim]Attachments will be sent with your next message.[/]")

        elif cmd == "/multi":
            console.print("[dim]Enter your prompt. Type . on a line by itself to send.[/]")
            lines = []
            while True:
                next_line = console.input("[dim]...[/] ")
                if next_line == ".":
                    break
                lines.append(next_line)
            prompt = "\n".join(lines).strip()
            if prompt:
                self.send(prompt)


        elif cmd == "/clear":
            self.history.clear()
            self.conv_id = str(uuid.uuid4())
            console.clear()
            console.print(BANNER); console.print()
            console.print("[dim]Conversation history cleared.[/]")

        elif cmd == "/save":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = self.logs_dir / f"chat_{ts}.json"
            out.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")
            console.print(f"  [green]✓[/] Saved: [dim]{out}[/]")

        elif cmd == "/files":
            files = tools.list_workspace()
            if not files: console.print("[dim]workspace/ is empty.[/]"); return
            t = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
            t.add_column(style="#6c63ff"); t.add_column(style="dim")
            for f in files:
                t.add_row(str(f.relative_to(tools.WORKSPACE)), f"{f.stat().st_size:,}B")
            console.print(Panel(t, title="[dim]workspace/[/]", border_style="dim"))

        elif cmd == "/exec":
            if not arg: console.print("[yellow]Usage: /exec <command>[/]"); return
            with console.status(f"[dim]$ {arg}[/]"):
                rc, out, err = tools.run_shell(arg)
            print_exec("shell", arg, rc, out, err)

        elif cmd == "/image":
            if not arg: console.print("[yellow]/image <prompt>[/]"); return
            with console.status("[dim]Generating image...[/]"):
                try:
                    urls = self.ai.generate_image(arg)
                    for u in urls: console.print(f"  [green]✓[/] {u}")
                except Exception as e: console.print(f"  [red]✗[/] {e}")

        elif cmd == "/tts":
            if not arg: console.print("[yellow]Usage: /tts <text>[/]"); return
            out = tools.WORKSPACE / "tts_output.mp3"
            with console.status("[dim]Generating audio...[/]"):
                try:
                    self.ai.tts(arg, save_path=out)
                    console.print(f"  [green]✓[/] Saved: [dim]{out}[/]")
                except Exception as e: console.print(f"  [red]✗[/] {e}")

        elif cmd == "/models":
            with console.status("[dim]Loading...[/]"):
                try:
                    ms = self.ai.list_models()
                    t = Table(box=box.SIMPLE, show_header=False)
                    t.add_column(style="#6c63ff")
                    for m in ms: t.add_row(m if isinstance(m,str) else m.get("id","?"))
                    console.print(t)
                except Exception as e: console.print(f"[red]Error:[/] {e}")

        else:
            console.print(f"[yellow]Unknown command: {cmd}  (type /help)[/]")

    def run(self):
        console.print(BANNER); console.print()
        show_status(self.model, self.mode, self.search)
        console.print("[dim]  /help · /mode agent · Ctrl+C to exit[/]\n")

        while True:
            try:
                icon = "⚡" if self.mode == "agent" else "💬"
                srch = " [dim]🔍[/]" if self.search else ""
                line = console.input(f"{icon} [bold #6c63ff]kilrun[/][dim]›[/]{srch} ").strip()
                if not line: continue
                if line.startswith("/"): self.command(line)
                else: self.send(line)
            except KeyboardInterrupt:
                console.print("\n[dim]Ctrl+C · type /exit to quit[/]")
            except SystemExit: break
            except EOFError: break


def main():
    import argparse
    p = argparse.ArgumentParser(prog="kilrun", description="Kilrun AI Agent Terminal",
                                epilog="Type /help to see all commands")
    p.add_argument("--agent",  "-a", action="store_true", help="Start in agent mode")
    p.add_argument("--model",  "-m", default=None)
    p.add_argument("--search", "-s", action="store_true")
    p.add_argument("prompt", nargs="*", help="Send a prompt immediately, then enter the interactive loop")
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
Example script using KilgoreAI directly.
Run: python scripts/example.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

import config
from kilgoreai import KilgoreAI

ai = KilgoreAI(api_key=config.API_KEY)

reply = ai.chat([{"role": "user", "content": "Hello! Briefly introduce yourself."}])
print(reply)
'''

FILES["workspace/.gitkeep"] = ""
FILES["logs/.gitkeep"] = ""

FILES[".env"] = """\
# Kilrun Configuration
# KILGORE_API_KEY may be left empty — the API can also authenticate via cookies.

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
    echo "[*] Creating virtual environment..."
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
    p(f"{DIM}Project root: {ROOT}{RESET}\n")

    # 1. Create directories
    dirs = ["core", "agent", "workspace", "scripts", "logs"]
    p(f"{BOLD}[1/3] Create directory structure{RESET}")
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
            info(f"Keeping existing file: {rel}")
            continue
        target.write_text(content, encoding="utf-8")
        ok(rel)

    # chmod run.sh trên Linux/Mac
    sh = ROOT / "run.sh"
    if sh.exists():
        try: sh.chmod(0o755)
        except: pass

    # 3. Install dependencies
    p(f"\n{BOLD}[3/3] Set up Python environment (.venv){RESET}")
    venv = ROOT / ".venv"

    if not venv.exists():
        info("Creating .venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        ok(".venv/ created")
    else:
        info(".venv/ already exists, skipping")

    pip = venv / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    info("Installing httpx + rich ...")
    subprocess.run([str(pip), "install", "httpx", "rich", "--quiet"], check=True)
    ok("httpx + rich installed")

    # Done
    p(f"\n{BOLD}{GREEN}╔══════════════════════════════════════╗")
    p(f"║   ✓  Installation complete!         ║")
    p(f"╚══════════════════════════════════════╝{RESET}")
    p(f"""
{BOLD}Structure:{RESET}
    {CYAN}core/{RESET}         ← Engine (do not modify or delete)
  {CYAN}agent/{RESET}        ← Kilrun AI agent
    {CYAN}workspace/{RESET}    ← Where the agent creates files
    {CYAN}scripts/{RESET}      ← Your scripts
    {CYAN}logs/{RESET}         ← Chat history
    {CYAN}.env{RESET}          ← Configuration and API key

{BOLD}Quick start:{RESET}
  Windows:  {GREEN}run.bat{RESET}
  Linux:    {GREEN}./run.sh{RESET}

    Start in agent mode:
  Windows:  {GREEN}run.bat --agent{RESET}
  Linux:    {GREEN}./run.sh --agent{RESET}

{DIM}Add an API key to .env (optional){RESET}
""")


if __name__ == "__main__":
    install()
