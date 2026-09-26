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
