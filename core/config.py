"""
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
