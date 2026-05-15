# MiMo TTS 全功能网站设计

## 概述

将现有 TTS Web 应用升级为覆盖 MiMo-V2.5-TTS 系列全部功能的完整平台，支持三种模型：预置音色合成、音色设计、音色复刻。

## 文件结构

```
tts_web/
├── app.py                  # Flask 主应用（替换 server.py）
├── tts.py                  # 核心 TTS 客户端（保留，扩展）
├── cli.py                  # CLI（保留不动）
├── requirements.txt        # Flask 依赖
├── api文档.txt             # 保留
├── static/
│   ├── index.html          # 主页面结构
│   ├── style.css           # 样式
│   └── app.js              # 前端逻辑
└── voices/                 # 预置音色样本（保留）
```

变更说明：
- `server.py` → `app.py`（Flask 重写）
- `static/index.html` 拆分为 `index.html` + `style.css` + `app.js`
- 根目录 `index.html` 删除（过时版本）
- 新增 `requirements.txt`（flask）

## 后端设计

### 技术栈
- Flask
- 代理请求到 MiMo API（`https://token-plan-cn.xiaomimimo.com/v1`）

### API 端点

#### 1. `POST /api/tts/preset` — 预置音色合成

模型：`mimo-v2.5-tts`

请求体（JSON）：
```json
{
  "text": "要合成的文本（必填）",
  "voice": "冰糖（必填，9种预置音色之一）",
  "style_prompt": "自然语言风格控制（可选）",
  "audio_tag": "音频标签，如 (温柔)（可选）",
  "api_key": "用户自定义 key（可选）"
}
```

处理逻辑：
- 若提供 `style_prompt`：放入 `role: user` 的 content
- 若未提供 `style_prompt`：user 消息为空字符串
- `audio_tag` + `text` 拼接后放入 `role: assistant` 的 content
  - 若有 `audio_tag`：`"{audio_tag}{text}"`
  - 若无：直接用 `text`
- `audio.voice` = 请求中的 `voice`
- `audio.format` = `"wav"`

预置音色列表：
| 音色名 | Voice ID | 语言 | 性别 |
|--------|----------|------|------|
| MiMo-默认 | mimo_default | 中文 | 女性 |
| 冰糖 | 冰糖 | 中文 | 女性 |
| 茉莉 | 茉莉 | 中文 | 女性 |
| 苏打 | 苏打 | 中文 | 男性 |
| 白桦 | 白桦 | 中文 | 男性 |
| Mia | Mia | 英文 | 女性 |
| Chloe | Chloe | 英文 | 女性 |
| Milo | Milo | 英文 | 男性 |
| Dean | Dean | 英文 | 男性 |

#### 2. `POST /api/tts/design` — 音色设计

模型：`mimo-v2.5-tts-voicedesign`

请求体（JSON）：
```json
{
  "voice_desc": "音色描述（必填）",
  "text": "合成文本（可选，配合 optimize_preview）",
  "optimize_preview": true,
  "api_key": ""
}
```

处理逻辑：
- `voice_desc` → `role: user` 的 content
- 若提供 `text`：放入 `role: assistant` 的 content
- `audio.optimize_text_preview` = 请求中的 `optimize_preview`
- `audio.format` = `"wav"`
- 不传 `voice` 字段

#### 3. `POST /api/tts/clone` — 音色复刻

模型：`mimo-v2.5-tts-voiceclone`

请求格式：`multipart/form-data`

字段：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio_file | File | 是 | mp3/wav 音频文件，base64 后不超过 10MB |
| text | string | 是 | 要合成的文本 |
| style_prompt | string | 否 | 自然语言风格控制 |
| api_key | string | 否 | 用户自定义 key |

处理逻辑：
- 读取上传文件 → base64 编码
- 拼接前缀：`data:{mime};base64,{base64_data}`
  - wav 文件：`audio/wav`
  - mp3 文件：`audio/mpeg`
- `audio.voice` = 拼接后的 base64 字符串
- 若提供 `style_prompt`：放入 `role: user` 的 content
- `text` → `role: assistant` 的 content
- `audio.format` = `"wav"`

### API Key 逻辑

- 内置默认 Key（硬编码在 `app.py`）
- 用户可在前端输入自定义 Key，通过请求体 `api_key` 字段传递
- 若请求中 `api_key` 非空，使用用户 Key；否则使用内置 Key

### 错误处理

所有端点统一返回格式：
- 成功：`{ "audio": "base64编码的音频数据" }`，HTTP 200
- 失败：`{ "error": "错误描述" }`，HTTP 4xx/5xx

错误码：
- 400：参数缺失或无效
- 502：MiMo API 调用失败
- 500：服务器内部错误

### 静态文件服务

Flask 直接提供 `static/` 目录的静态文件，根路径 `/` 返回 `index.html`。

## 前端设计

### 整体布局

```
┌─────────────────────────────────────────┐
│  MiMo TTS          [API Key 设置 (折叠)] │
├─────────┬───────────┬───────────────────┤
│ 预置音色 │ 音色设计  │    音色复刻       │  ← Tab 栏
├─────────┴───────────┴───────────────────┤
│                                         │
│         （Tab 对应的内容区域）            │
│                                         │
│         [生成语音]                       │
│                                         │
│         ▶ 音频播放器  [下载]             │
│         状态信息                         │
└─────────────────────────────────────────┘
```

### Tab 1：预置音色合成

组件：
1. **文本输入** — textarea，必填
2. **风格控制** — 可选输入框，自然语言描述风格（放入 user message）
3. **音频标签** — 可选
   - 快捷按钮：温柔 / 悲伤 / 开心 / 愤怒 / 慵懒 / 磁性 / 紧张 / 叹气 / 笑 / 哭泣
   - 自定义输入框，用户可输入任意标签如 `(紧张，深呼吸)`
4. **音色选择** — 3x3 网格按钮，默认选中 `mimo_default`
5. **生成按钮**
6. **音频播放器 + 下载按钮**
7. **状态信息区**

请求示例：
```json
{
  "text": "你好世界",
  "voice": "冰糖",
  "style_prompt": "用温柔的语气",
  "audio_tag": "(温柔)"
}
```

### Tab 2：音色设计

组件：
1. **音色描述** — textarea，必填，描述想要的音色特征
2. **智能润色开关** — checkbox，默认开启（optimize_text_preview）
3. **合成文本** — textarea，可选（开启智能润色时可不填）
4. **生成按钮**
5. **音频播放器 + 下载按钮**

请求示例：
```json
{
  "voice_desc": "年轻女性，温柔甜美",
  "text": "你好世界",
  "optimize_preview": true
}
```

### Tab 3：音色复刻

组件：
1. **音频上传** — 拖拽区域 + 点击选择，支持 mp3/wav，最大 10MB
   - 显示已选文件名和删除按钮
2. **风格控制** — 可选输入框
3. **合成文本** — textarea，必填
4. **生成按钮**
5. **音频播放器 + 下载按钮**

请求：使用 `FormData` 发送 multipart/form-data。

### API Key 设置

- 页面顶部可折叠区域
- 默认显示内置 Key 的末四位：`****akcg`
- 输入框供用户输入自定义 Key
- 保存到 localStorage，下次打开自动加载
- 提供"恢复默认"按钮

### 样式风格

沿用当前暗色主题：
- 背景 `#0f0f13`，卡片 `#1a1a24`，边框 `#2a2a3a`
- 主色 `#6c5ce7`，强调色 `#00cec9`
- 字体 `Segoe UI, system-ui`
- 圆角卡片，渐变标题

### 交互细节

- 生成中：按钮禁用，显示"生成中..."，状态区显示进度
- 生成成功：自动播放音频，显示下载按钮
- 生成失败：红色错误提示
- Tab 切换：内容区域平滑切换，不丢失已填内容

## 实现顺序

1. 安装 Flask，创建 `requirements.txt`
2. 重写 `app.py`（三个 API 端点）
3. 创建 `static/style.css`（从现有 index.html 提取样式，扩展）
4. 创建 `static/index.html`（页面结构）
5. 创建 `static/app.js`（前端逻辑）
6. 删除旧文件：`server.py`、根目录 `index.html`
7. 测试全部功能

## 不做的事情

- 不加用户登录/注册
- 不加历史记录功能
- 不加流式输出（API 尚未真正支持）
- 不引入前端框架（React/Vue）
- 不引入构建工具
