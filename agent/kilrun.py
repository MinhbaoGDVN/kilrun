#!/usr/bin/env python3
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
        return "\n".join(to_text(item) for item in value)
    if isinstance(value, dict):
        if "text" in value:
            return to_text(value["text"])
        if "content" in value:
            return to_text(value["content"])
    return str(value)

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
