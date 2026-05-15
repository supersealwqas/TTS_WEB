"""Simple HTTP server for TTS web app."""

import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = "tp-c5fbolasp2e1oudhm6fz4niwuqzcakcg55w0xi5gi16ukyr5"
MODEL = "mimo-v2.5-tts"
VOICES = ["mimo_default", "冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe", "Milo", "Dean"]

STATIC_DIR = Path(__file__).parent / "static"


class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_file("index.html", "text/html")
        else:
            self.send_error(404)

    def serve_file(self, filename, content_type):
        filepath = STATIC_DIR / filename
        if not filepath.exists():
            self.send_error(404)
            return
        content = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path == "/api/tts":
            self.handle_tts()
        else:
            self.send_error(404)

    def handle_tts(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text = body.get("text", "").strip()
            voice = body.get("voice", "mimo_default")

            if not text:
                self.send_json(400, {"error": "text is required"})
                return

            url = f"{API_BASE}/chat/completions"
            payload = {
                "model": MODEL,
                "modalities": ["text", "audio"],
                "audio": {"voice": voice, "format": "wav"},
                "messages": [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": text},
                ],
            }

            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
                method="POST",
            )

            with urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())

            audio_b64 = result["choices"][0]["message"]["audio"]["data"]
            self.send_json(200, {"audio": audio_b64})

        except HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            self.send_json(502, {"error": f"API error ({e.code}): {error_body}"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json(500, {"error": str(e)})

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = 5000
    server = HTTPServer(("0.0.0.0", port), TTSHandler)
    print(f"TTS Server running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
