"""Flask TTS server -- proxies requests to MiMo TTS API."""

import base64
import json
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from urllib.request import Request, urlopen
from urllib.error import HTTPError

app = Flask(__name__, static_folder="static", static_url_path="")

API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_API_KEY = "tp-c5fbolasp2e1oudhm6fz4niwuqzcakcg55w0xi5gi16ukyr5"


def get_api_key():
    """Return user-provided key if present, otherwise the built-in key."""
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip()
    return key if key else DEFAULT_API_KEY


def mimo_request(payload, api_key):
    """Send a request to the MiMo API and return the parsed response."""
    url = f"{API_BASE}/chat/completions"
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
