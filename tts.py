"""MiMo TTS client - Text-to-Speech via OpenAI-compatible chat completions API."""

import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5-tts"

VOICES = ["mimo_default", "冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe", "Milo", "Dean"]


class TTSError(Exception):
    pass


def text_to_speech(
    text: str,
    output_path: str | Path = "output.wav",
    *,
    voice: str = "mimo_default",
    api_key: str = "",
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
) -> Path:
    """Convert text to speech and save as WAV file.

    Args:
        text: The text to convert to speech.
        output_path: Where to save the audio file.
        voice: Voice name. See VOICES for available options.
        api_key: API key for authentication.
        base_url: API base URL.
        model: TTS model name.

    Returns:
        Path to the saved audio file.
    """
    if not api_key:
        raise TTSError("api_key is required")

    if voice not in VOICES:
        raise TTSError(f"Unknown voice '{voice}'. Available: {VOICES}")

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
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
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise TTSError(f"API request failed ({e.code}): {error_body}") from e

    try:
        audio_b64 = result["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError) as e:
        raise TTSError(f"Unexpected API response: {json.dumps(result, ensure_ascii=False)[:500]}") from e

    audio_bytes = base64.b64decode(audio_b64)
    output = Path(output_path)
    output.write_bytes(audio_bytes)
    return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Usage: python tts.py <text> [output.wav] [voice]")
        print(f"Voices: {', '.join(VOICES)}")
        sys.exit(1)

    text = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "output.wav"
    voice = sys.argv[3] if len(sys.argv) > 3 else "mimo_default"

    api_key = "tp-c5fbolasp2e1oudhm6fz4niwuqzcakcg55w0xi5gi16ukyr5"
    result = text_to_speech(text, out, voice=voice, api_key=api_key)
    print(f"Saved: {result}")
