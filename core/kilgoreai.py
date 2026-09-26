"""
KilgoreAI Python Client — core engine. Do not modify this file.
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
