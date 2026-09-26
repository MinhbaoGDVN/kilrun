"""
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
