"""Tests for Flask TTS app."""
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"MiMo TTS" in resp.data


def test_preset_missing_text(client):
    resp = client.post("/api/tts/preset", json={"voice": "冰糖"})
    assert resp.status_code == 400
    assert "text" in resp.get_json()["error"]


def test_preset_missing_voice(client):
    resp = client.post("/api/tts/preset", json={"text": "你好"})
    assert resp.status_code == 400
    assert "voice" in resp.get_json()["error"]


def test_preset_invalid_voice(client):
    resp = client.post("/api/tts/preset", json={"text": "你好", "voice": "不存在"})
    assert resp.status_code == 400
    assert "voice" in resp.get_json()["error"]


def test_design_missing_voice_desc(client):
    resp = client.post("/api/tts/design", json={"text": "你好"})
    assert resp.status_code == 400
    assert "voice_desc" in resp.get_json()["error"]


import io


def test_clone_missing_file(client):
    resp = client.post("/api/tts/clone", data={"text": "你好"})
    assert resp.status_code == 400
    assert "audio_file" in resp.get_json()["error"]


def test_clone_missing_text(client):
    data = {"audio_file": (io.BytesIO(b"fake audio"), "test.wav")}
    resp = client.post("/api/tts/clone", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "text" in resp.get_json()["error"]


def test_clone_invalid_format(client):
    data = {
        "audio_file": (io.BytesIO(b"fake"), "test.txt"),
        "text": "你好",
    }
    resp = client.post("/api/tts/clone", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "format" in resp.get_json()["error"].lower() or "mp3" in resp.get_json()["error"].lower() or "wav" in resp.get_json()["error"].lower()
