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
