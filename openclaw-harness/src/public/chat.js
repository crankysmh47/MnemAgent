/* MnemOS Chat UI */

const STORAGE_USER = "mnemos_user_id";
const STORAGE_SESSION = "mnemos_session_id";
const STORAGE_HISTORY = "mnemos_session_history";
const STORAGE_MESSAGES = "mnemos_messages_";

function uuid() {
  return crypto.randomUUID ? crypto.randomUUID() : "u-" + Date.now();
}

function getUserId() {
  let id = localStorage.getItem(STORAGE_USER);
  if (!id) {
    id = uuid();
    localStorage.setItem(STORAGE_USER, id);
  }
  return id;
}

function getSessionId() {
  let id = localStorage.getItem(STORAGE_SESSION);
  if (!id) {
    id = uuid();
    localStorage.setItem(STORAGE_SESSION, id);
  }
  return id;
}

function setSessionId(id) {
  localStorage.setItem(STORAGE_SESSION, id);
  document.getElementById("sessionLabel").textContent = id.slice(0, 8) + "…";
}

function pushSessionHistory(id) {
  const hist = JSON.parse(localStorage.getItem(STORAGE_HISTORY) || "[]");
  if (!hist.includes(id)) hist.unshift(id);
  localStorage.setItem(STORAGE_HISTORY, JSON.stringify(hist.slice(0, 5)));
  renderSessionHistory();
}

function renderSessionHistory() {
  const ul = document.getElementById("sessionHistory");
  const hist = JSON.parse(localStorage.getItem(STORAGE_HISTORY) || "[]");
  const current = getSessionId();
  ul.innerHTML = hist
    .map(
      (s) =>
        `<li class="${s === current ? "active" : ""}" data-session="${s}">${s.slice(0, 12)}…</li>`
    )
    .join("");
  ul.querySelectorAll("li").forEach((li) => {
    li.onclick = () => loadSession(li.dataset.session);
  });
}

function saveMessages() {
  const key = STORAGE_MESSAGES + getSessionId();
  const msgs = [...document.querySelectorAll("#messages .msg")].map((el) => ({
    role: el.classList.contains("user") ? "user" : "agent",
    html: el.querySelector(".body")?.innerHTML || "",
    time: el.querySelector(".time")?.textContent || "",
  }));
  localStorage.setItem(key, JSON.stringify(msgs));
}

function loadSession(sessionId) {
  setSessionId(sessionId);
  const key = STORAGE_MESSAGES + sessionId;
  const msgs = JSON.parse(localStorage.getItem(key) || "[]");
  const box = document.getElementById("messages");
  box.innerHTML = "";
  msgs.forEach((m) => appendMessage(m.role, m.html, m.time, false));
  scrollBottom();
}

function appendMessage(role, content, timeStr, persist = true) {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const time = timeStr || new Date().toLocaleTimeString();
  const body = role === "agent" ? renderAgentContent(content) : escapeHtml(content);
  div.innerHTML = `<div class="body">${body}</div><div class="time">${time}</div>`;
  box.appendChild(div);
  scrollBottom();
  if (persist) saveMessages();
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderAgentContent(text) {
  if (text.includes("| --- |") && text.includes("|")) {
    return markdownTableToHtml(text);
  }
  if (typeof marked !== "undefined") {
    const html = marked.parse(text);
    if (typeof hljs !== "undefined") {
      setTimeout(() => {
        document.querySelectorAll("#messages pre code").forEach((block) => hljs.highlightElement(block));
      }, 0);
    }
    return html;
  }
  return escapeHtml(text).replace(/\n/g, "<br>");
}

function markdownTableToHtml(md) {
  const lines = md.split("\n").filter((l) => l.trim().startsWith("|"));
  if (lines.length < 2) return escapeHtml(md);
  const rows = lines.filter((l) => !l.includes("---"));
  let html = '<table><thead><tr>';
  rows[0].split("|").filter(Boolean).forEach((c) => (html += `<th>${c.trim()}</th>`));
  html += "</tr></thead><tbody>";
  rows.slice(1).forEach((row) => {
    html += "<tr>";
    row.split("|").filter(Boolean).forEach((c) => (html += `<td>${c.trim()}</td>`));
    html += "</tr>";
  });
  return html + "</tbody></table>";
}

function scrollBottom() {
  const box = document.getElementById("messages");
  box.scrollTop = box.scrollHeight;
}

function confidenceClass(weight) {
  if (weight >= 0.85) return "high";
  if (weight >= 0.55) return "mid";
  return "low";
}

function confidenceLabel(weight) {
  if (weight >= 0.85) return "High Confidence";
  if (weight >= 0.55) return "Confident";
  return "Fading";
}

async function refreshMemoryCards() {
  const panel = document.getElementById("memoryPanel");
  panel.innerHTML = "<em>Loading…</em>";
  try {
    const resp = await fetch(`/api/graph/${encodeURIComponent(getUserId())}`);
    const data = await resp.json();
    if (!data.beliefs?.length) {
      panel.innerHTML = "<em>No memories yet.</em>";
      return;
    }
    panel.innerHTML = data.beliefs
      .map(
        (b) => `
      <div class="belief-card ${confidenceClass(b.node_weight)}">
        <strong>${escapeHtml(b.entity_source)}</strong> → ${escapeHtml(b.relation)} → ${escapeHtml(b.entity_target)}
        <div class="badge">${confidenceLabel(b.node_weight)} · Q ${b.base_utility_q.toFixed(2)}</div>
      </div>`
      )
      .join("");
  } catch (e) {
    panel.innerHTML = `<em>Error: ${e.message}</em>`;
  }
}

async function showStats() {
  const panel = document.getElementById("memoryPanel");
  panel.innerHTML = "<em>Loading stats…</em>";
  try {
    const resp = await fetch(`/stats/${encodeURIComponent(getUserId())}`);
    const data = await resp.json();
    appendMessage("agent", data.response, null, true);
    panel.innerHTML = "<em>Stats shown in chat →</em>";
  } catch (e) {
    panel.innerHTML = `<em>Error: ${e.message}</em>`;
  }
}

function setTyping(on) {
  let el = document.getElementById("typing");
  if (on && !el) {
    el = document.createElement("div");
    el.id = "typing";
    el.className = "typing";
    el.textContent = "MnemOS is thinking…";
    document.getElementById("messages").appendChild(el);
    scrollBottom();
  } else if (!on && el) {
    el.remove();
  }
}

async function sendMessage(text) {
  const message = (text ?? document.getElementById("messageInput").value).trim();
  if (!message) return;
  document.getElementById("messageInput").value = "";
  appendMessage("user", message);
  setTyping(true);
  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: getUserId(),
        session_id: getSessionId(),
        message,
      }),
    });
    const data = await resp.json();
    setTyping(false);
    if (data.error) throw new Error(data.detail || data.error);
    appendMessage("agent", data.response);
    if (!message.startsWith("/memory")) refreshMemoryCards();
  } catch (e) {
    setTyping(false);
    appendMessage("agent", `Error: ${e.message}`);
  }
}

function newSession() {
  const id = uuid();
  setSessionId(id);
  pushSessionHistory(id);
  document.getElementById("messages").innerHTML = "";
  localStorage.setItem(STORAGE_MESSAGES + id, "[]");
  document.getElementById("sessionBanner").classList.add("show");
  setTimeout(() => document.getElementById("sessionBanner").classList.remove("show"), 5000);
}

async function pollHealth() {
  const dot = document.getElementById("statusDot");
  try {
    const resp = await fetch("/health");
    const data = await resp.json();
    dot.classList.toggle("ok", data.status === "ok" && data.mnemos?.status === "ok");
  } catch {
    dot.classList.remove("ok");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("userLabel").textContent = getUserId().slice(0, 12) + "…";
  setSessionId(getSessionId());
  pushSessionHistory(getSessionId());
  loadSession(getSessionId());

  document.getElementById("sendBtn").onclick = () => sendMessage();
  document.getElementById("newSessionBtn").onclick = newSession;
  document.getElementById("refreshMemoryBtn").onclick = refreshMemoryCards;
  document.getElementById("statsBtn").onclick = showStats;
  document.getElementById("cmdMemory").onclick = () => sendMessage("/memory");
  document.getElementById("cmdStats").onclick = () => sendMessage("/memory --mode stats");

  const input = document.getElementById("messageInput");
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  refreshMemoryCards();
  pollHealth();
  setInterval(pollHealth, 10000);
});
