# TTS Web

基于 MiMo-V2.5-TTS 的文本转语音 Web 应用，支持预置音色、音色设计、音色克隆三种模式。

## 功能

- **预置音色** - 内置 9 种精品音色，支持风格标签和自然语言控制
- **音色设计** - 通过文字描述自定义音色
- **音色克隆** - 上传音频样本复刻音色

## 快速开始

### 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### 安装

```bash
git clone https://github.com/supersealwqas/TTS_WEB.git
cd TTS_WEB
uv sync
```

### 配置

复制并编辑环境变量：

```bash
echo "MIMO_API_KEY=your_api_key" > .env
```

### 运行

```bash
uv run python app.py
```

访问 http://localhost:5000

## 项目结构

```
├── app.py           # Flask 服务端
├── tts.py           # TTS 客户端
├── cli.py           # 命令行工具
├── static/
│   ├── index.html   # 前端页面
│   ├── app.js       # 前端逻辑
│   └── style.css    # 样式
├── pyproject.toml   # 项目配置
└── .env             # 环境变量（不提交）
```

## API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tts/preset` | POST | 预置音色合成 |
| `/api/tts/design` | POST | 音色设计合成 |
| `/api/tts/clone` | POST | 音色克隆合成 |

## 部署

推送到 GitHub 后，在 [Render](https://render.com) 创建 Web Service：

- **Build Command**: `pip install uv && uv pip install ".[deploy]"`
- **Start Command**: `gunicorn app:app`

在 Environment 中设置 `MIMO_API_KEY`。
