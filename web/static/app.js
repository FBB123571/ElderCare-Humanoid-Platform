const $ = (id) => document.getElementById(id);

const PRESETS = {
  normal: { hr: 72, spo2: 98, activity: 40, aspect: 110, dy: 0, emotion: "neutral", text: "" },
  chat: { hr: 78, spo2: 97, activity: 20, aspect: 100, dy: 0, emotion: "sad", text: "最近有点孤独，睡不太好" },
  fall: { hr: 95, spo2: 94, activity: 5, aspect: 35, dy: -80, emotion: "anxious", text: "" },
};

const STATE_LABELS = {
  monitor: "监测中",
  converse: "对话中",
  alert: "告警",
  emergency: "紧急",
  idle: "空闲",
};

const RISK_LABELS = {
  normal: "正常",
  alert: "注意",
  emergency: "紧急",
};

const CMD_LABELS = {
  speak: "语音",
  gesture: "手势",
  alert_sound: "告警音",
  call_emergency: "紧急呼叫",
  approach: "靠近",
  log: "日志",
};

const fields = ["hr", "spo2", "activity", "aspect", "dy"];

function readPayload() {
  return {
    heart_rate: +$("hr").value,
    spo2: +$("spo2").value,
    activity_level: +$("activity").value / 100,
    skeleton_aspect_ratio: +$("aspect").value / 100,
    skeleton_dy: +$("dy").value / 100,
    emotion: $("emotion").value,
    user_text: $("userText").value.trim(),
    use_vision: $("useVision").checked,
  };
}

function setEmotion(value) {
  $("emotion").value = value;
  document.querySelectorAll(".emotion-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.emotion === value);
  });
}

function applyPreset(name) {
  const p = PRESETS[name];
  $("hr").value = p.hr;
  $("spo2").value = p.spo2;
  $("activity").value = p.activity;
  $("aspect").value = p.aspect;
  $("dy").value = p.dy;
  setEmotion(p.emotion);
  $("userText").value = p.text;
  updateLabels();
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.preset === name);
  });
}

function updateLabels() {
  $("hrVal").textContent = $("hr").value;
  $("spo2Val").textContent = $("spo2").value;
  $("actVal").textContent = $("activity").value;
  $("aspVal").textContent = (+$("aspect").value / 100).toFixed(2);
  $("dyVal").textContent = (+$("dy").value / 100).toFixed(2);
}

function setGauge(score, level) {
  const arc = $("gaugeArc");
  const offset = 327 - Math.min(score, 1) * 327;
  arc.style.strokeDashoffset = offset;
  const colors = {
    emergency: "#f87171",
    alert: "#fbbf24",
    normal: "url(#gaugeGrad)",
  };
  arc.style.stroke = colors[level] || colors.normal;
  arc.style.filter = level === "emergency"
    ? "drop-shadow(0 0 8px rgba(248,113,113,.6))"
    : "drop-shadow(0 0 6px rgba(52,211,153,.5))";

  const levelEl = $("riskLevel");
  levelEl.textContent = RISK_LABELS[level] || level;
  levelEl.style.background =
    level === "emergency" ? "rgba(248,113,113,.2)" :
    level === "alert" ? "rgba(251,191,36,.2)" : "rgba(52,211,153,.15)";
  levelEl.style.color =
    level === "emergency" ? "#fca5a5" :
    level === "alert" ? "#fcd34d" : "#34d399";

  const hero = $("riskHero");
  hero.classList.remove("level-alert", "level-emergency");
  if (level === "alert") hero.classList.add("level-alert");
  if (level === "emergency") hero.classList.add("level-emergency");
}

function setStateBadge(state) {
  const badge = $("stateBadge");
  badge.className = `state-badge state-${state}`;
  $("stateText").textContent = STATE_LABELS[state] || state;
}

function setPipeline(state) {
  document.querySelectorAll(".pipeline-step").forEach((el) => {
    el.classList.toggle("active", el.dataset.state === state);
  });
}

function renderActionTags(actions) {
  const box = $("actionTags");
  box.innerHTML = "";
  if (!actions?.length) return;
  actions.forEach((cmd) => {
    const tag = document.createElement("span");
    tag.className = `action-tag${cmd === "call_emergency" ? " danger" : ""}`;
    tag.textContent = CMD_LABELS[cmd] || cmd;
    box.appendChild(tag);
  });
}

function renderTick(data) {
  setStateBadge(data.state);
  setPipeline(data.state);
  $("riskScore").textContent = data.risk.score.toFixed(2);
  setGauge(data.risk.score, data.risk.level);

  const reasons = $("riskReasons");
  reasons.innerHTML = "";
  const list = data.risk.reasons || [];
  if (list.length) {
    list.forEach((r) => {
      const li = document.createElement("li");
      li.textContent = r;
      reasons.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "暂无异常，状态良好";
    reasons.appendChild(li);
  }

  const replyBox = $("replyBox");
  if (data.reply) {
    replyBox.classList.remove("hidden");
    $("replyText").textContent = data.reply;
  } else {
    replyBox.classList.add("hidden");
  }

  const fallEl = $("metricFall");
  $("fallDetected").textContent = data.fall.detected ? "已检测 ⚠" : "未检测";
  fallEl.classList.toggle("alert", data.fall.detected);
  $("fallScore").textContent = data.fall.score.toFixed(2);
  $("healthFlags").textContent = (data.health_flags || []).join("、") || "无";
  renderActionTags(data.actions);
}

function buildMsg(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "👴" : role === "system" ? "✓" : "🤖";
  const body = document.createElement("div");
  body.className = "msg-body";
  body.textContent = text;
  wrap.appendChild(avatar);
  wrap.appendChild(body);
  return wrap;
}

function buildCmdItem(record) {
  const cmd = record.command || "unknown";
  const div = document.createElement("div");
  div.className = "cmd-item";
  const badge = document.createElement("span");
  badge.className = `cmd-badge ${cmd}`;
  badge.textContent = CMD_LABELS[cmd] || cmd;
  const payload = { ...record };
  delete payload.command;
  const text = document.createElement("span");
  text.className = "cmd-payload";
  text.textContent = Object.keys(payload).length ? JSON.stringify(payload) : "—";
  div.appendChild(badge);
  div.appendChild(text);
  return div;
}

async function refreshLogs() {
  const res = await fetch("/api/status");
  const data = await res.json();
  $("cmdCount").textContent = data.robot_history.length;

  const chat = $("chatLog");
  chat.innerHTML = "";
  if (!data.chat_log.length) {
    chat.innerHTML = '<div class="chat-empty">暂无对话，输入老人话语或运行演示剧本</div>';
  } else {
    data.chat_log.forEach((m) => {
      const text = m.role === "user" ? m.text : m.text;
      chat.appendChild(buildMsg(m.role, text));
    });
  }
  chat.scrollTop = chat.scrollHeight;

  const robot = $("robotLog");
  robot.innerHTML = "";
  const history = data.robot_history.slice(-12);
  if (!history.length) {
    robot.innerHTML = '<div class="robot-empty">等待指令…</div>';
  } else {
    history.forEach((h) => robot.appendChild(buildCmdItem(h)));
  }
  robot.scrollTop = robot.scrollHeight;
}

let camStream = null;

async function startCamera() {
  try {
    camStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
    const video = $("camVideo");
    video.srcObject = camStream;
    video.classList.remove("hidden");
    $("visionPreview").classList.add("hidden");
    $("visionStatus").textContent = "摄像头已开启，点击「分析当前帧」提取姿态";
  } catch (e) {
    $("visionStatus").textContent = `无法打开摄像头：${e.message}`;
  }
}

async function analyzeCameraFrame() {
  const video = $("camVideo");
  const canvas = $("camCanvas");
  if (!video.videoWidth) {
    $("visionStatus").textContent = "请先打开摄像头";
    return;
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.85));
  const fd = new FormData();
  fd.append("file", blob, "frame.jpg");
  $("visionStatus").textContent = "分析中…";
  const res = await fetch("/api/vision/analyze", { method: "POST", body: fd });
  const data = await res.json();
  if (!data.ok) {
    $("visionStatus").textContent = data.error || "分析失败";
    return;
  }
  const m = data.metrics;
  $("aspect").value = Math.round(m.aspect_ratio * 100);
  $("dy").value = Math.round(Math.max(-100, Math.min(50, m.dy * 100)));
  updateLabels();
  if (data.preview_jpeg_b64) {
    $("visionPreview").src = `data:image/jpeg;base64,${data.preview_jpeg_b64}`;
    $("visionPreview").classList.remove("hidden");
    video.classList.add("hidden");
  }
  const detected = m.fall?.detected ? "是" : "否";
  $("visionStatus").textContent = `姿态宽高比 ${m.aspect_ratio.toFixed(2)} · 跌倒 ${detected}`;
}

async function doTick() {
  $("btnTick").disabled = true;
  try {
    const res = await fetch("/api/tick", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readPayload()),
    });
    const data = await res.json();
    renderTick(data);
    await refreshLogs();
  } finally {
    $("btnTick").disabled = false;
  }
}

async function doReset() {
  await fetch("/api/reset", { method: "POST" });
  $("scenarioBar").classList.add("hidden");
  document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
  renderTick({
    state: "monitor",
    risk: { score: 0, level: "normal", reasons: [] },
    fall: { detected: false, score: 0 },
    health_flags: [],
    actions: [],
    reply: "",
  });
  await refreshLogs();
}

let demoRunning = false;

async function runDemo() {
  if (demoRunning) return;
  demoRunning = true;
  $("btnDemo").disabled = true;
  $("scenarioBar").classList.remove("hidden");

  const es = new EventSource("/api/demo/stream");
  es.onmessage = async (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "scenario") {
      $("scenarioName").textContent = msg.name;
    } else if (msg.type === "tick") {
      renderTick(msg);
      await refreshLogs();
    } else if (msg.type === "done") {
      es.close();
      demoRunning = false;
      $("btnDemo").disabled = false;
      $("scenarioBar").classList.add("hidden");
      if (msg.emergency) {
        const chat = $("chatLog");
        const empty = chat.querySelector(".chat-empty");
        if (empty) empty.remove();
        chat.appendChild(buildMsg("system", "演示完成：跌倒紧急流程已成功触发"));
        chat.scrollTop = chat.scrollHeight;
      }
    }
  };
  es.onerror = () => {
    es.close();
    demoRunning = false;
    $("btnDemo").disabled = false;
    $("scenarioBar").classList.add("hidden");
  };
}

fields.forEach((id) => $(id).addEventListener("input", updateLabels));

document.querySelectorAll("[data-preset]").forEach((btn) => {
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset));
});

document.querySelectorAll(".emotion-btn").forEach((btn) => {
  btn.addEventListener("click", () => setEmotion(btn.dataset.emotion));
});

$("btnTick").addEventListener("click", doTick);
$("btnDemo").addEventListener("click", runDemo);
$("btnReset").addEventListener("click", doReset);
$("btnCamStart").addEventListener("click", startCamera);
$("btnCamAnalyze").addEventListener("click", analyzeCameraFrame);

$("userText").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    doTick();
  }
});

updateLabels();
doReset();

fetch("/api/health")
  .then((r) => r.json())
  .then(() => {
    $("connBadge").textContent = "系统在线";
    $("connDot").classList.add("live");
  })
  .catch(() => {
    $("connBadge").textContent = "连接断开";
    $("connDot").style.background = "var(--danger)";
  });
