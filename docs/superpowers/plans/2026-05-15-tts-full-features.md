# MiMo TTS 全功能网站实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 TTS Web 应用升级为覆盖 MiMo-V2.5-TTS 系列全部功能的完整平台，支持预置音色合成、音色设计、音色复刻三种模型。

**Architecture:** Flask 后端做三层 API 代理（preset/design/clone），前端单页三 Tab 切换，纯 HTML/CSS/JS 无构建工具。

**Tech Stack:** Python 3.12, Flask, HTML, CSS, JavaScript (vanilla)

---

## 文件结构

```
tts_web/
├── app.py                  # Flask 主应用（新建，替换 server.py）
├── test_app.py             # Flask 端点测试（新建）
├── tts.py                  # 核心 TTS 客户端（保留不动）
├── cli.py                  # CLI（保留不动）
├── requirements.txt        # 依赖（新建）
├── static/
│   ├── index.html          # 页面结构（重写）
│   ├── style.css           # 样式（新建）
│   └── app.js              # 前端逻辑（新建）
└── voices/                 # 预置音色样本（保留）
```

---

### Task 1: 环境准备

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 创建 requirements.txt**

```
flask>=3.0
```

- [ ] **Step 2: 安装依赖**

Run: `pip install flask`
Expected: Successfully installed flask

- [ ] **Step 3: 验证 Flask 可用**

Run: `python -c "import flask; print(flask.__version__)"`
Expected: 输出版本号，如 `3.x.x`

---

### Task 2: 创建 Flask 应用骨架 + 静态文件服务

**Files:**
- Create: `app.py`
- Create: `test_app.py`

- [ ] **Step 1: 编写测试 — 根路径返回 index.html**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: 编写 app.py 骨架**

```python
"""Flask TTS server — proxies requests to MiMo TTS API."""

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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest test_app.py -v`
Expected: `test_index_returns_html PASSED`

- [ ] **Step 5: 提交**

```bash
git add requirements.txt app.py test_app.py
git commit -m "feat: Flask app skeleton with static file serving"
```

---

### Task 3: 实现 /api/tts/preset 端点

**Files:**
- Modify: `app.py`
- Modify: `test_app.py`

- [ ] **Step 1: 编写测试**

在 `test_app.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest test_app.py::test_preset_missing_text -v`
Expected: FAIL — 404 (路由不存在)

- [ ] **Step 3: 实现 preset 端点**

在 `app.py` 中 `mimo_request` 函数之后、`index` 路由之前添加：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest test_app.py -v`
Expected: 全部 PASSED

- [ ] **Step 5: 提交**

```bash
git add app.py test_app.py
git commit -m "feat: add /api/tts/preset endpoint"
```

---

### Task 4: 实现 /api/tts/design 端点

**Files:**
- Modify: `app.py`
- Modify: `test_app.py`

- [ ] **Step 1: 编写测试**

在 `test_app.py` 末尾追加：

```python
def test_design_missing_voice_desc(client):
    resp = client.post("/api/tts/design", json={"text": "你好"})
    assert resp.status_code == 400
    assert "voice_desc" in resp.get_json()["error"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest test_app.py::test_design_missing_voice_desc -v`
Expected: FAIL — 404 (路由不存在)

- [ ] **Step 3: 实现 design 端点**

在 `app.py` 中 `tts_preset` 函数之后添加：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest test_app.py -v`
Expected: 全部 PASSED

- [ ] **Step 5: 提交**

```bash
git add app.py test_app.py
git commit -m "feat: add /api/tts/design endpoint"
```

---

### Task 5: 实现 /api/tts/clone 端点

**Files:**
- Modify: `app.py`
- Modify: `test_app.py`

- [ ] **Step 1: 编写测试**

在 `test_app.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest test_app.py::test_clone_missing_file -v`
Expected: FAIL — 404

- [ ] **Step 3: 实现 clone 端点**

在 `app.py` 中 `tts_design` 函数之后添加：

```python
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav"}
MIME_MAP = {".mp3": "audio/mpeg", ".wav": "audio/wav"}


@app.route("/api/tts/clone", methods=["POST"])
def tts_clone():
    audio_file = request.files.get("audio_file")
    text = request.form.get("text", "").strip()
    style_prompt = request.form.get("style_prompt", "").strip()
    api_key = request.form.get("api_key", "").strip() or DEFAULT_API_KEY

    if not audio_file:
        return jsonify({"error": "audio_file is required"}), 400
    if not text:
        return jsonify({"error": "text is required"}), 400

    ext = Path(audio_file.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({"error": f"Unsupported format: {ext}. Use mp3 or wav."}), 400

    file_bytes = audio_file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({"error": "Audio file too large (max 10MB)"}), 400

    mime = MIME_MAP[ext]
    b64_audio = base64.b64encode(file_bytes).decode("utf-8")
    voice_value = f"data:{mime};base64,{b64_audio}"

    messages = [{"role": "user", "content": style_prompt}]
    messages.append({"role": "assistant", "content": text})

    payload = {
        "model": "mimo-v2.5-tts-voiceclone",
        "modalities": ["text", "audio"],
        "audio": {"format": "wav", "voice": voice_value},
        "messages": messages,
    }

    try:
        result = mimo_request(payload, api_key)
        audio_b64 = result["choices"][0]["message"]["audio"]["data"]
        return jsonify({"audio": audio_b64})
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return jsonify({"error": f"API error ({e.code}): {error_body}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest test_app.py -v`
Expected: 全部 PASSED

- [ ] **Step 5: 提交**

```bash
git add app.py test_app.py
git commit -m "feat: add /api/tts/clone endpoint"
```

---

### Task 6: 创建 CSS 样式文件

**Files:**
- Create: `static/style.css`

- [ ] **Step 1: 编写 style.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #0f0f13;
  --card: #1a1a24;
  --border: #2a2a3a;
  --primary: #6c5ce7;
  --primary-hover: #7c6cf7;
  --text: #e8e8f0;
  --text-dim: #8888a0;
  --accent: #00cec9;
  --error: #ff6b6b;
}

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 20px;
}

.container {
  width: 100%;
  max-width: 600px;
  padding-top: 20px;
}

/* Header */
h1 {
  text-align: center;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* API Key Section */
.api-key-section {
  margin-bottom: 24px;
}

.api-key-toggle {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 4px 0;
  font-family: inherit;
}

.api-key-toggle:hover { color: var(--text); }

.api-key-panel {
  display: none;
  margin-top: 8px;
  padding: 14px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.api-key-panel.show { display: block; }

.api-key-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.api-key-row input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.85rem;
  font-family: inherit;
  outline: none;
}

.api-key-row input:focus { border-color: var(--primary); }

.btn-sm {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text-dim);
  font-size: 0.8rem;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
}

.btn-sm:hover { border-color: var(--primary); color: var(--text); }

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 0;
}

.tab-btn {
  flex: 1;
  padding: 12px 8px;
  background: var(--card);
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  color: var(--text-dim);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.tab-btn:hover { color: var(--text); }

.tab-btn.active {
  background: var(--card);
  color: var(--primary);
  border-color: var(--primary);
  font-weight: 600;
}

/* Card */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0 0 16px 16px;
  padding: 28px;
  border-top: none;
}

/* Tab content */
.tab-content { display: none; }
.tab-content.active { display: block; }

/* Form elements */
label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-dim);
  margin-bottom: 8px;
  font-weight: 500;
}

textarea {
  width: 100%;
  height: 120px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  padding: 14px;
  font-size: 0.95rem;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  line-height: 1.6;
}

textarea:focus { border-color: var(--primary); }

textarea.small {
  height: 80px;
  font-size: 0.85rem;
}

.input-group { margin-bottom: 20px; }

.input-group label {
  margin-bottom: 8px;
}

.optional-hint {
  font-size: 0.75rem;
  color: var(--text-dim);
  font-weight: 400;
  margin-left: 4px;
}

/* Voice grid */
.voice-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.voice-btn {
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  padding: 10px 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  font-family: inherit;
}

.voice-btn:hover { border-color: var(--primary); }

.voice-btn.active {
  border-color: var(--primary);
  background: rgba(108, 92, 231, 0.12);
  color: var(--primary);
  font-weight: 600;
}

/* Audio tag quick buttons */
.tag-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tag-btn {
  padding: 6px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  color: var(--text-dim);
  font-size: 0.8rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.tag-btn:hover { border-color: var(--accent); color: var(--accent); }

.tag-btn.active {
  border-color: var(--accent);
  background: rgba(0, 206, 201, 0.12);
  color: var(--accent);
}

/* Checkbox */
.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.checkbox-group input[type="checkbox"] {
  accent-color: var(--primary);
  width: 16px;
  height: 16px;
}

.checkbox-group label {
  margin-bottom: 0;
  font-size: 0.85rem;
  cursor: pointer;
}

/* File upload */
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 28px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
}

.upload-zone:hover,
.upload-zone.dragover {
  border-color: var(--primary);
  background: rgba(108, 92, 231, 0.05);
}

.upload-zone .upload-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.upload-zone .upload-text {
  color: var(--text-dim);
  font-size: 0.85rem;
}

.upload-zone .upload-hint {
  color: var(--text-dim);
  font-size: 0.75rem;
  margin-top: 4px;
}

.file-info {
  display: none;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 0.85rem;
}

.file-info.show { display: flex; }

.file-info .file-name { flex: 1; color: var(--accent); }

.file-remove {
  background: none;
  border: none;
  color: var(--error);
  cursor: pointer;
  font-size: 1rem;
  padding: 0 4px;
}

/* Generate button */
.generate-btn {
  width: 100%;
  padding: 14px;
  background: var(--primary);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  margin-top: 4px;
}

.generate-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.generate-btn.loading {
  background: var(--border);
  pointer-events: none;
}

/* Player section */
.player-section {
  margin-top: 24px;
  display: none;
}

.player-section.show { display: block; }

.player-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

audio {
  flex: 1;
  height: 48px;
  border-radius: 8px;
  outline: none;
}

.download-btn {
  padding: 10px 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.85rem;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
  text-decoration: none;
}

.download-btn:hover { border-color: var(--accent); color: var(--accent); }

/* Status */
.status {
  text-align: center;
  margin-top: 16px;
  font-size: 0.85rem;
  min-height: 24px;
}

.status.error { color: var(--error); }
.status.success { color: var(--accent); }
```

- [ ] **Step 2: 提交**

```bash
git add static/style.css
git commit -m "feat: add CSS styles for TTS web app"
```

---

### Task 7: 创建 HTML 页面

**Files:**
- Create: `static/index.html`

- [ ] **Step 1: 编写 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MiMo TTS</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
  <h1>MiMo TTS</h1>

  <!-- API Key -->
  <div class="api-key-section">
    <button class="api-key-toggle" id="apiKeyToggle">API Key 设置</button>
    <div class="api-key-panel" id="apiKeyPanel">
      <div class="api-key-row">
        <input type="password" id="apiKeyInput" placeholder="输入你的 API Key（留空使用默认）">
        <button class="btn-sm" id="apiKeySave">保存</button>
        <button class="btn-sm" id="apiKeyReset">恢复默认</button>
      </div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab-btn active" data-tab="preset">预置音色</button>
    <button class="tab-btn" data-tab="design">音色设计</button>
    <button class="tab-btn" data-tab="clone">音色复刻</button>
  </div>

  <div class="card">
    <!-- Tab 1: Preset -->
    <div class="tab-content active" id="tab-preset">
      <div class="input-group">
        <label>输入文本</label>
        <textarea id="presetText" placeholder="在这里输入要合成的文字..."></textarea>
      </div>

      <div class="input-group">
        <label>风格控制 <span class="optional-hint">（可选，自然语言描述）</span></label>
        <textarea class="small" id="presetStyle" placeholder="例：用温柔的语气，语速稍慢，带着微笑"></textarea>
      </div>

      <div class="input-group">
        <label>音频标签 <span class="optional-hint">（可选）</span></label>
        <div class="tag-buttons" id="tagButtons">
          <button class="tag-btn" data-tag="(温柔)">温柔</button>
          <button class="tag-btn" data-tag="(悲伤)">悲伤</button>
          <button class="tag-btn" data-tag="(开心)">开心</button>
          <button class="tag-btn" data-tag="(愤怒)">愤怒</button>
          <button class="tag-btn" data-tag="(慵懒)">慵懒</button>
          <button class="tag-btn" data-tag="(磁性)">磁性</button>
          <button class="tag-btn" data-tag="(紧张)">紧张</button>
          <button class="tag-btn" data-tag="(叹气)">叹气</button>
          <button class="tag-btn" data-tag="(笑)">笑</button>
          <button class="tag-btn" data-tag="(哭泣)">哭泣</button>
        </div>
        <input type="text" id="presetTag" placeholder="自定义标签，如 (紧张，深呼吸)" style="
          width: 100%;
          padding: 8px 12px;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 8px;
          color: var(--text);
          font-size: 0.85rem;
          font-family: inherit;
          outline: none;
        ">
      </div>

      <div class="input-group">
        <label>选择音色</label>
        <div class="voice-grid" id="voiceGrid">
          <button class="voice-btn active" data-voice="mimo_default">默认</button>
          <button class="voice-btn" data-voice="冰糖">冰糖</button>
          <button class="voice-btn" data-voice="茉莉">茉莉</button>
          <button class="voice-btn" data-voice="苏打">苏打</button>
          <button class="voice-btn" data-voice="白桦">白桦</button>
          <button class="voice-btn" data-voice="Mia">Mia</button>
          <button class="voice-btn" data-voice="Chloe">Chloe</button>
          <button class="voice-btn" data-voice="Milo">Milo</button>
          <button class="voice-btn" data-voice="Dean">Dean</button>
        </div>
      </div>

      <button class="generate-btn" id="presetGenerate">生成语音</button>
      <div class="player-section" id="presetPlayer">
        <div class="player-row">
          <audio id="presetAudio" controls></audio>
          <a class="download-btn" id="presetDownload" download="preset.wav">下载</a>
        </div>
      </div>
      <div class="status" id="presetStatus"></div>
    </div>

    <!-- Tab 2: Design -->
    <div class="tab-content" id="tab-design">
      <div class="input-group">
        <label>音色描述</label>
        <textarea id="designDesc" placeholder="描述你想要的音色，例：年轻女性，温柔甜美，语速适中，像在耳边轻声说话"></textarea>
      </div>

      <div class="checkbox-group">
        <input type="checkbox" id="designOptimize" checked>
        <label for="designOptimize">智能润色文本（optimize_text_preview）</label>
      </div>

      <div class="input-group">
        <label>合成文本 <span class="optional-hint">（开启智能润色时可不填）</span></label>
        <textarea class="small" id="designText" placeholder="要合成的文本..."></textarea>
      </div>

      <button class="generate-btn" id="designGenerate">生成语音</button>
      <div class="player-section" id="designPlayer">
        <div class="player-row">
          <audio id="designAudio" controls></audio>
          <a class="download-btn" id="designDownload" download="design.wav">下载</a>
        </div>
      </div>
      <div class="status" id="designStatus"></div>
    </div>

    <!-- Tab 3: Clone -->
    <div class="tab-content" id="tab-clone">
      <div class="input-group">
        <label>上传音频样本</label>
        <div class="upload-zone" id="uploadZone">
          <div class="upload-icon">+</div>
          <div class="upload-text">拖拽文件到此处，或点击选择</div>
          <div class="upload-hint">支持 mp3、wav，最大 10MB</div>
        </div>
        <input type="file" id="cloneFile" accept=".mp3,.wav" style="display:none">
        <div class="file-info" id="fileInfo">
          <span class="file-name" id="fileName"></span>
          <button class="file-remove" id="fileRemove">✕</button>
        </div>
      </div>

      <div class="input-group">
        <label>风格控制 <span class="optional-hint">（可选，自然语言描述）</span></label>
        <textarea class="small" id="cloneStyle" placeholder="例：用欢快的语气，语速稍快"></textarea>
      </div>

      <div class="input-group">
        <label>合成文本</label>
        <textarea id="cloneText" placeholder="要合成的文字..."></textarea>
      </div>

      <button class="generate-btn" id="cloneGenerate">生成语音</button>
      <div class="player-section" id="clonePlayer">
        <div class="player-row">
          <audio id="cloneAudio" controls></audio>
          <a class="download-btn" id="cloneDownload" download="clone.wav">下载</a>
        </div>
      </div>
      <div class="status" id="cloneStatus"></div>
    </div>
  </div>
</div>

<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 启动 Flask 验证页面可加载**

Run: `python app.py`（在后台运行）
访问 `http://localhost:5000`，确认页面显示正常。

- [ ] **Step 3: 提交**

```bash
git add static/index.html
git commit -m "feat: add HTML page with three tabs"
```

---

### Task 8: 创建前端 JavaScript

**Files:**
- Create: `static/app.js`

- [ ] **Step 1: 编写 app.js**

```javascript
/* MiMo TTS Web App - Frontend Logic */

// ─── API Key ───
const apiKeyToggle = document.getElementById("apiKeyToggle");
const apiKeyPanel = document.getElementById("apiKeyPanel");
const apiKeyInput = document.getElementById("apiKeyInput");
const apiKeySave = document.getElementById("apiKeySave");
const apiKeyReset = document.getElementById("apiKeyReset");

let customApiKey = localStorage.getItem("tts_api_key") || "";

function getApiKey() {
  return customApiKey;
}

apiKeyToggle.addEventListener("click", () => {
  apiKeyPanel.classList.toggle("show");
});

apiKeySave.addEventListener("click", () => {
  customApiKey = apiKeyInput.value.trim();
  if (customApiKey) {
    localStorage.setItem("tts_api_key", customApiKey);
  } else {
    localStorage.removeItem("tts_api_key");
  }
  apiKeyPanel.classList.remove("show");
});

apiKeyReset.addEventListener("click", () => {
  customApiKey = "";
  apiKeyInput.value = "";
  localStorage.removeItem("tts_api_key");
});

// Load saved key on init
if (customApiKey) {
  apiKeyInput.value = customApiKey;
}

// ─── Tabs ───
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

// ─── Status helper ───
function setStatus(el, msg, isError, isSuccess) {
  el.textContent = msg;
  el.className = "status" + (isError ? " error" : isSuccess ? " success" : "");
}

// ─── Download helper ───
function setupDownload(downloadBtn, audioEl, base64Data, filename) {
  const bin = atob(base64Data);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  const blob = new Blob([arr], { type: "audio/wav" });
  const url = URL.createObjectURL(blob);
  audioEl.src = url;
  downloadBtn.href = url;
  downloadBtn.download = filename;
}

// ═══════════════════════════════════════
// Tab 1: Preset Voice
// ═══════════════════════════════════════
const presetText = document.getElementById("presetText");
const presetStyle = document.getElementById("presetStyle");
const presetTag = document.getElementById("presetTag");
const voiceGrid = document.getElementById("voiceGrid");
const tagButtons = document.getElementById("tagButtons");
const presetGenerate = document.getElementById("presetGenerate");
const presetPlayer = document.getElementById("presetPlayer");
const presetAudio = document.getElementById("presetAudio");
const presetDownload = document.getElementById("presetDownload");
const presetStatus = document.getElementById("presetStatus");

let selectedVoice = "mimo_default";

// Voice selection
voiceGrid.addEventListener("click", (e) => {
  const btn = e.target.closest(".voice-btn");
  if (!btn) return;
  voiceGrid.querySelectorAll(".voice-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  selectedVoice = btn.dataset.voice;
});

// Tag quick buttons
tagButtons.addEventListener("click", (e) => {
  const btn = e.target.closest(".tag-btn");
  if (!btn) return;
  const wasActive = btn.classList.contains("active");
  tagButtons.querySelectorAll(".tag-btn").forEach((b) => b.classList.remove("active"));
  if (!wasActive) {
    btn.classList.add("active");
    presetTag.value = btn.dataset.tag;
  } else {
    presetTag.value = "";
  }
});

// Clear quick button highlight when typing custom tag
presetTag.addEventListener("input", () => {
  tagButtons.querySelectorAll(".tag-btn").forEach((b) => b.classList.remove("active"));
});

presetGenerate.addEventListener("click", async () => {
  const text = presetText.value.trim();
  if (!text) {
    setStatus(presetStatus, "请输入文本", true);
    return;
  }

  const body = {
    text,
    voice: selectedVoice,
    style_prompt: presetStyle.value.trim(),
    audio_tag: presetTag.value.trim(),
    api_key: getApiKey(),
  };

  presetGenerate.classList.add("loading");
  presetGenerate.textContent = "生成中...";
  presetGenerate.disabled = true;
  presetPlayer.classList.remove("show");
  setStatus(presetStatus, "正在调用 TTS 接口...");

  try {
    const resp = await fetch("/api/tts/preset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "请求失败");

    setupDownload(presetDownload, presetAudio, data.audio, "preset.wav");
    presetPlayer.classList.add("show");
    presetAudio.play();
    setStatus(presetStatus, "生成成功", false, true);
  } catch (e) {
    setStatus(presetStatus, e.message, true);
  } finally {
    presetGenerate.classList.remove("loading");
    presetGenerate.textContent = "生成语音";
    presetGenerate.disabled = false;
  }
});

// ═══════════════════════════════════════
// Tab 2: Voice Design
// ═══════════════════════════════════════
const designDesc = document.getElementById("designDesc");
const designOptimize = document.getElementById("designOptimize");
const designText = document.getElementById("designText");
const designGenerate = document.getElementById("designGenerate");
const designPlayer = document.getElementById("designPlayer");
const designAudio = document.getElementById("designAudio");
const designDownload = document.getElementById("designDownload");
const designStatus = document.getElementById("designStatus");

designGenerate.addEventListener("click", async () => {
  const voice_desc = designDesc.value.trim();
  if (!voice_desc) {
    setStatus(designStatus, "请输入音色描述", true);
    return;
  }

  const body = {
    voice_desc,
    text: designText.value.trim(),
    optimize_preview: designOptimize.checked,
    api_key: getApiKey(),
  };

  designGenerate.classList.add("loading");
  designGenerate.textContent = "生成中...";
  designGenerate.disabled = true;
  designPlayer.classList.remove("show");
  setStatus(designStatus, "正在调用 TTS 接口...");

  try {
    const resp = await fetch("/api/tts/design", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "请求失败");

    setupDownload(designDownload, designAudio, data.audio, "design.wav");
    designPlayer.classList.add("show");
    designAudio.play();
    setStatus(designStatus, "生成成功", false, true);
  } catch (e) {
    setStatus(designStatus, e.message, true);
  } finally {
    designGenerate.classList.remove("loading");
    designGenerate.textContent = "生成语音";
    designGenerate.disabled = false;
  }
});

// ═══════════════════════════════════════
// Tab 3: Voice Clone
// ═══════════════════════════════════════
const uploadZone = document.getElementById("uploadZone");
const cloneFileInput = document.getElementById("cloneFile");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const fileRemove = document.getElementById("fileRemove");
const cloneStyle = document.getElementById("cloneStyle");
const cloneText = document.getElementById("cloneText");
const cloneGenerate = document.getElementById("cloneGenerate");
const clonePlayer = document.getElementById("clonePlayer");
const cloneAudio = document.getElementById("cloneAudio");
const cloneDownload = document.getElementById("cloneDownload");
const cloneStatus = document.getElementById("cloneStatus");

let selectedFile = null;

uploadZone.addEventListener("click", () => cloneFileInput.click());

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  if (e.dataTransfer.files.length) {
    handleFile(e.dataTransfer.files[0]);
  }
});

cloneFileInput.addEventListener("change", () => {
  if (cloneFileInput.files.length) {
    handleFile(cloneFileInput.files[0]);
  }
});

function handleFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  if (ext !== "mp3" && ext !== "wav") {
    setStatus(cloneStatus, "仅支持 mp3 和 wav 格式", true);
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    setStatus(cloneStatus, "文件大小不能超过 10MB", true);
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.classList.add("show");
  uploadZone.style.display = "none";
  setStatus(cloneStatus, "", false, false);
}

fileRemove.addEventListener("click", () => {
  selectedFile = null;
  cloneFileInput.value = "";
  fileInfo.classList.remove("show");
  uploadZone.style.display = "";
});

cloneGenerate.addEventListener("click", async () => {
  if (!selectedFile) {
    setStatus(cloneStatus, "请上传音频样本", true);
    return;
  }
  const text = cloneText.value.trim();
  if (!text) {
    setStatus(cloneStatus, "请输入合成文本", true);
    return;
  }

  const formData = new FormData();
  formData.append("audio_file", selectedFile);
  formData.append("text", text);
  formData.append("style_prompt", cloneStyle.value.trim());
  formData.append("api_key", getApiKey());

  cloneGenerate.classList.add("loading");
  cloneGenerate.textContent = "生成中...";
  cloneGenerate.disabled = true;
  clonePlayer.classList.remove("show");
  setStatus(cloneStatus, "正在调用 TTS 接口...");

  try {
    const resp = await fetch("/api/tts/clone", {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "请求失败");

    setupDownload(cloneDownload, cloneAudio, data.audio, "clone.wav");
    clonePlayer.classList.add("show");
    cloneAudio.play();
    setStatus(cloneStatus, "生成成功", false, true);
  } catch (e) {
    setStatus(cloneStatus, e.message, true);
  } finally {
    cloneGenerate.classList.remove("loading");
    cloneGenerate.textContent = "生成语音";
    cloneGenerate.disabled = false;
  }
});
```

- [ ] **Step 2: 启动 Flask 并手动测试**

Run: `python app.py`
访问 `http://localhost:5000`，验证：
1. 三个 Tab 可切换
2. 预置音色：选音色、输入文本、点击生成
3. 音色设计：输入描述、点击生成
4. 音色复刻：上传文件、输入文本、点击生成
5. API Key 设置可折叠、可保存

- [ ] **Step 3: 提交**

```bash
git add static/app.js
git commit -m "feat: add frontend JavaScript logic"
```

---

### Task 9: 清理旧文件

**Files:**
- Delete: `server.py`
- Delete: `index.html`（根目录）

- [ ] **Step 1: 删除旧的 server.py**

```bash
rm server.py
```

- [ ] **Step 2: 删除根目录的 index.html**

```bash
rm index.html
```

- [ ] **Step 3: 删除旧的 static/index.html（已被新的替换）**

确认 `static/index.html` 已是新版本后无需额外操作。

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: remove old server.py and root index.html"
```

---

### Task 10: 最终验证

- [ ] **Step 1: 运行全部测试**

Run: `python -m pytest test_app.py -v`
Expected: 全部 PASSED

- [ ] **Step 2: 启动服务并端到端测试**

Run: `python app.py`

测试清单：
1. 访问 `http://localhost:5000` — 页面正常加载
2. Tab 切换 — 三个 Tab 都能切换，内容不丢失
3. API Key — 折叠/展开、保存、恢复默认
4. 预置音色合成 — 输入文本、选音色、生成、播放、下载
5. 预置音色 + 风格控制 — 填写自然语言风格，生成
6. 预置音色 + 音频标签 — 使用快捷标签和自定义标签
7. 音色设计 — 输入描述、开启智能润色、生成
8. 音色设计 — 关闭智能润色、手动输入文本、生成
9. 音色复刻 — 上传 wav 文件、输入文本、生成
10. 音色复刻 — 上传 mp3 文件、生成
11. 错误处理 — 空文本、无效文件格式、API 错误

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: MiMo TTS full-featured web app complete"
```
