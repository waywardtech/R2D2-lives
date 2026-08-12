const transcript = document.querySelector("#transcript");
const chatForm = document.querySelector("#chat-form");
const messageInput = document.querySelector("#message");
const refreshButton = document.querySelector("#refresh");
let latestStatus = null;

const escapeText = (value) => String(value ?? "UNAVAILABLE");
const compact = (value) => {
  if (value === null || value === undefined || value === "") return "UNAVAILABLE";
  if (typeof value === "boolean") return value ? "YES" : "NO";
  if (typeof value === "object") return Object.entries(value).map(([key, item]) => `${key}:${compact(item)}`).join(" · ");
  return String(value);
};

function addMessage(kind, primary, translation = "") {
  const article = document.createElement("article");
  article.className = `message ${kind}`;
  const speaker = document.createElement("span");
  speaker.className = "speaker";
  speaker.textContent = kind === "user" ? "PILOT" : "R2-D2";
  const main = document.createElement("p");
  main.className = kind === "user" ? "translation" : "binary";
  main.textContent = primary;
  article.append(speaker, main);
  if (translation) {
    const translated = document.createElement("p");
    translated.className = "translation";
    translated.textContent = `Translation: “${translation}”`;
    article.append(translated);
  }
  transcript.append(article);
  transcript.scrollTop = transcript.scrollHeight;
}

function droidReply(text) {
  const normalized = text.toLowerCase();
  const droid = latestStatus?.droid || {};
  const battery = droid.battery || {};
  const pi = latestStatus?.pi || {};
  if (/battery|charge/.test(normalized)) {
    return ["deet-deet · bwoo", `Battery state is ${compact(battery.state)} at ${compact(battery.voltage_v)} volts.`];
  }
  if (/status|systems|health|how are you/.test(normalized)) {
    return ["bweep · doo-wah · deet", `System state is ${compact(latestStatus?.overall)}. Pi CPU is ${compact(pi.cpu_temperature_c)} °C and R2 link is ${compact(droid.connection)}.`];
  }
  if (/hello|hi|hey|luke/.test(normalized)) {
    return ["bweep-bweep! · woo", "Hello! I am listening, and the console remains locked against motor commands."];
  }
  if (/proof|life|emote/.test(normalized)) {
    return ["doo-deet · brreep", `The latest proof-of-life expression is ${compact(droid.expression?.status)}. Hardware tests must be armed at the Pi console.`];
  }
  if (/issue|warning|problem/.test(normalized)) {
    const issues = latestStatus?.issues || [];
    return ["bwooo · deet", issues.length ? issues.map((issue) => issue.message).join("; ") : "No reported system issues."];
  }
  return ["beep-brrt · woo-deet", "I received that. Conversational reasoning is in local fallback mode, so no physical action was inferred."];
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  addMessage("user", text);
  messageInput.value = "";
  const [binary, translation] = droidReply(text);
  window.setTimeout(() => addMessage("droid", binary, translation), 260);
});

function row(label, value) {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const detail = document.createElement("dd");
  term.textContent = label;
  detail.textContent = compact(value);
  wrapper.append(term, detail);
  return wrapper;
}

function renderStatus(status) {
  latestStatus = status;
  const droid = status.droid || {};
  const pi = status.pi || {};
  const droidList = document.querySelector("#droid-state");
  const piList = document.querySelector("#pi-state");
  droidList.replaceChildren(
    row("Connection", droid.connection),
    row("Safe hold", droid.safe_hold),
    row("Battery", droid.battery?.state),
    row("Voltage", droid.battery?.voltage_v == null ? null : `${droid.battery.voltage_v} V`),
    row("Firmware", droid.identity?.firmware),
    row("Head", droid.head?.head_position),
    row("Expression", droid.expression?.status),
    row("Locomotion", droid.movement_performed ? "MOVEMENT REPORTED" : "NONE REPORTED"),
  );
  piList.replaceChildren(
    row("Host", pi.hostname),
    row("CPU temp", pi.cpu_temperature_c == null ? null : `${pi.cpu_temperature_c} °C`),
    row("Ambient", pi.ambient_temperature_status),
    row("Load 1m", pi.load?.one_min),
    row("Memory used", pi.memory?.used_percent == null ? null : `${pi.memory.used_percent}%`),
    row("Disk used", pi.disk?.used_percent == null ? null : `${pi.disk.used_percent}%`),
    row("Throttle", pi.throttling),
    row("Apache", pi.services?.apache2),
    row("Bluetooth", pi.services?.bluetooth),
    row("Clock sync", status.clock?.synchronized),
    row("Network", pi.network_interfaces),
  );
  const issues = document.querySelector("#issues");
  issues.replaceChildren(...(status.issues || []).map((item) => {
    const node = document.createElement("div");
    node.className = `issue ${escapeText(item.severity)}`;
    node.textContent = item.message;
    return node;
  }));
  const overall = status.overall || "unknown";
  document.querySelector("#overall").textContent = overall.toUpperCase();
  document.querySelector("#measured").textContent = status.measured_at ? `UTC ${status.measured_at}` : "NO TIMESTAMP";
  document.querySelector("#alert-strip").dataset.level = overall;
}

async function loadStatus() {
  refreshButton.disabled = true;
  try {
    const response = await fetch(`status.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`status ${response.status}`);
    renderStatus(await response.json());
  } catch (_error) {
    renderStatus({
      overall: "attention",
      issues: [{ severity: "warning", message: "Live status snapshot is unavailable." }],
      droid: { connection: "unknown" },
      pi: {},
    });
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadStatus);
loadStatus();
window.setInterval(loadStatus, 10000);

document.querySelectorAll("canvas.scope").forEach((canvas, index) => {
  const context = canvas.getContext("2d");
  let phase = index * 1.7;
  function draw() {
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (canvas.width !== width * ratio || canvas.height !== height * ratio) {
      canvas.width = width * ratio;
      canvas.height = height * ratio;
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);
    context.strokeStyle = "#183136";
    context.lineWidth = 1;
    for (let x = 0; x < width; x += 14) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke(); }
    context.strokeStyle = index === 1 ? "#ffb43b" : "#ff5a1f";
    context.shadowColor = context.strokeStyle;
    context.shadowBlur = 5;
    context.beginPath();
    for (let x = 0; x <= width; x += 2) {
      const burst = Math.sin(x * .19 + phase) * Math.sin(x * .043 - phase * .7);
      const y = height / 2 + burst * height * .28 + Math.sin(x * .05 + phase) * 3;
      if (x === 0) context.moveTo(x, y); else context.lineTo(x, y);
    }
    context.stroke();
    context.shadowBlur = 0;
    phase += .045;
    requestAnimationFrame(draw);
  }
  draw();
});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("service-worker.js");
