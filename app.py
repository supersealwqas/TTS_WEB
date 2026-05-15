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


PRESET_VOICES = [
    "mimo_default", "冰糖", "茉莉", "苏打", "白桦",
    "Mia", "Chloe", "Milo", "Dean",
]


@app.route("/api/tts/preset", methods=["POST"])
def tts_preset():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    voice = data.get("voice", "").strip()
    style_prompt = data.get("style_prompt", "").strip()
    audio_tag = data.get("audio_tag", "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400
    if not voice:
        return jsonify({"error": "voice is required"}), 400
    if voice not in PRESET_VOICES:
        return jsonify({"error": f"Unknown voice: {voice}. Available: {PRESET_VOICES}"}), 400

    assistant_content = f"{audio_tag}{text}" if audio_tag else text

    payload = {
        "model": "mimo-v2.5-tts",
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": "wav"},
        "messages": [
            {"role": "user", "content": style_prompt},
            {"role": "assistant", "content": assistant_content},
        ],
    }

    try:
        result = mimo_request(payload, get_api_key())
        audio_b64 = result["choices"][0]["message"]["audio"]["data"]
        return jsonify({"audio": audio_b64})
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return jsonify({"error": f"API error ({e.code}): {error_body}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tts/design", methods=["POST"])
def tts_design():
    data = request.get_json(silent=True) or {}
    voice_desc = data.get("voice_desc", "").strip()
    text = data.get("text", "").strip()
    optimize_preview = data.get("optimize_preview", True)

    if not voice_desc:
        return jsonify({"error": "voice_desc is required"}), 400

    messages = [{"role": "user", "content": voice_desc}]
    if text:
        messages.append({"role": "assistant", "content": text})

    payload = {
        "model": "mimo-v2.5-tts-voicedesign",
        "modalities": ["text", "audio"],
        "audio": {"format": "wav", "optimize_text_preview": optimize_preview},
        "messages": messages,
    }

    try:
        result = mimo_request(payload, get_api_key())
        audio_b64 = result["choices"][0]["message"]["audio"]["data"]
        return jsonify({"audio": audio_b64})
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return jsonify({"error": f"API error ({e.code}): {error_body}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
