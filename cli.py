"""CLI for MiMo TTS - convert text to speech."""

import argparse
import sys
from pathlib import Path

from tts import TTSError, VOICES, text_to_speech

DEFAULT_API_KEY = "tp-c5fbolasp2e1oudhm6fz4niwuqzcakcg55w0xi5gi16ukyr5"


def main():
    parser = argparse.ArgumentParser(description="MiMo TTS - Text to Speech")
    parser.add_argument("text", nargs="?", help="Text to convert to speech")
    parser.add_argument("-f", "--file", help="Read text from file")
    parser.add_argument("-o", "--output", default="output.wav", help="Output file path (default: output.wav)")
    parser.add_argument("-v", "--voice", default="mimo_default", choices=VOICES, help="Voice name")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="API key")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    args = parser.parse_args()

    if args.list_voices:
        print("Available voices:")
        for v in VOICES:
            print(f"  - {v}")
        return

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text
    else:
        print("Enter text (Ctrl+Z then Enter on Windows to finish):")
        text = sys.stdin.read().strip()

    if not text:
        print("Error: no text provided", file=sys.stderr)
        sys.exit(1)

    try:
        result = text_to_speech(text, args.output, voice=args.voice, api_key=args.key)
        print(f"Saved: {result}")
    except TTSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
