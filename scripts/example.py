"""
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
