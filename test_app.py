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
