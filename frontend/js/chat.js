/**
 * IT Helpdesk Chat UI — JavaScript
 * Handles: sending messages, rendering responses, source citations, escalation cards.
 */

const API_BASE = "http://localhost:8000";
const MAX_CHARS = 2000;

// Session management
let sessionId = sessionStorage.getItem("helpdesk_session_id") || crypto.randomUUID();
sessionStorage.setItem("helpdesk_session_id", sessionId);

let conversationHistory = JSON.parse(sessionStorage.getItem("helpdesk_history") || "[]");
let isWaiting = false;

// DOM refs
const messagesContainer = document.getElementById("messages-container");
const welcomeHero = document.getElementById("welcome-hero");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const charCount = document.getElementById("char-count");
const statusDot = document.getElementById("status-dot");

// ── Initialisation ─────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", () => {
  // Restore conversation if exists
  if (conversationHistory.length > 0) {
    welcomeHero.style.display = "none";
    messagesContainer.style.display = "flex";
    conversationHistory.forEach(msg => {
      if (msg.role === "user") renderUserBubble(msg.content);
      // Agent messages are not re-rendered from history (no source data stored)
    });
  }

  messageInput.addEventListener("input", onInputChange);
  messageInput.addEventListener("keydown", onKeyDown);
  sendBtn.addEventListener("click", sendMessage);

  checkSystemHealth();
  setInterval(checkSystemHealth, 60_000);
});

// ── Input handling ─────────────────────────────────────────────────────────

function onInputChange() {
  const len = messageInput.value.length;
  charCount.textContent = `${len} / ${MAX_CHARS}`;
  charCount.className = "char-count" + (len > 1800 ? " warn" : "");

  // Auto-resize textarea
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";

  sendBtn.disabled = len === 0 || isWaiting;
}

function onKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled) sendMessage();
  }
}

function fillSuggestion(btn) {
  messageInput.value = btn.textContent;
  onInputChange();
  messageInput.focus();
}

// ── Send message ───────────────────────────────────────────────────────────

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || isWaiting) return;

  // Show messages area, hide welcome
  if (welcomeHero.style.display !== "none") {
    welcomeHero.style.display = "none";
    messagesContainer.style.display = "flex";
  }

  // Render user bubble
  renderUserBubble(text);

  // Clear input
  messageInput.value = "";
  messageInput.style.height = "auto";
  charCount.textContent = "0 / 2000";
  charCount.className = "char-count";
  sendBtn.disabled = true;
  isWaiting = true;

  // Show typing indicator
  const typingEl = renderTypingIndicator();
  scrollToBottom();

  // Add to history
  conversationHistory.push({ role: "user", content: text });
  if (conversationHistory.length > 20) conversationHistory = conversationHistory.slice(-20);

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session_id: sessionId,
        conversation_history: conversationHistory.slice(-10),
      }),
    });

    typingEl.remove();

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      renderErrorBubble(err.detail || `Error ${response.status} — please try again.`);
    } else {
      const data = await response.json();
      if (data.escalate) {
        renderEscalationCard(data);
      } else {
        renderAgentBubble(data);
        conversationHistory.push({ role: "assistant", content: data.answer });
      }
    }

    sessionStorage.setItem("helpdesk_history", JSON.stringify(conversationHistory));

  } catch (err) {
    typingEl.remove();
    renderErrorBubble("Could not reach the support service. Please check your connection.");
  } finally {
    isWaiting = false;
    sendBtn.disabled = false;
    scrollToBottom();
  }
}

// ── Render functions ───────────────────────────────────────────────────────

function renderUserBubble(text) {
  const row = document.createElement("div");
  row.className = "message-row user animate-fade-in";
  row.innerHTML = `
    <div class="avatar avatar-user">👤</div>
    <div class="bubble-content">
      <div class="chat-bubble bubble-user">${escapeHtml(text)}</div>
    </div>
  `;
  messagesContainer.appendChild(row);
}

function renderAgentBubble(data) {
  const confidence = data.confidence || 0;
  const confPct = Math.round(confidence * 100);
  const confColor = confidence >= 0.85 ? "var(--accent-green)"
                  : confidence >= 0.70 ? "var(--accent-amber)"
                  : "var(--accent-red)";

  // Format answer — convert markdown-style **bold** and [Source: x] citations
  let answerHtml = escapeHtml(data.answer)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[Source:\s*([^\]]+)\]/g, '<span class="source-pill">📄 $1</span>')
    .replace(/\n/g, "<br>");

  // Source pills
  let sourcesHtml = "";
  if (data.sources && data.sources.length > 0) {
    const pills = data.sources.map(s =>
      `<span class="source-pill" title="${escapeHtml(s.section)} — ${Math.round(s.relevance_score * 100)}% relevance">
        📄 ${escapeHtml(s.title || s.article)}
      </span>`
    ).join("");
    sourcesHtml = `<div class="sources-row">${pills}</div>`;
  }

  // Disclaimer
  let disclaimerHtml = "";
  if (data.low_confidence_disclaimer) {
    disclaimerHtml = `
      <div class="disclaimer-banner">
        ⚠️ This answer may not be complete. An IT engineer can provide more detailed help.
      </div>
    `;
  }

  const row = document.createElement("div");
  row.className = "message-row animate-fade-in";
  row.innerHTML = `
    <div class="avatar avatar-agent">🤖</div>
    <div class="bubble-content">
      <div class="chat-bubble bubble-agent">${answerHtml}</div>
      ${sourcesHtml}
      <div class="confidence-bar-wrap">
        <span>Confidence</span>
        <div class="confidence-bar">
          <div class="confidence-bar-fill" style="width:${confPct}%; background:${confColor};"></div>
        </div>
        <span>${confPct}%</span>
      </div>
      ${disclaimerHtml}
    </div>
  `;
  messagesContainer.appendChild(row);
}

function renderEscalationCard(data) {
  const row = document.createElement("div");
  row.className = "message-row animate-fade-in";
  row.innerHTML = `
    <div class="avatar avatar-agent">🤖</div>
    <div class="bubble-content" style="width:100%;">
      <div class="escalation-card">
        <div class="esc-title">
          🎫 Ticket Raised — IT Team Notified
        </div>
        <p style="font-size:0.875rem; color:var(--text-secondary);">
          I couldn't find a confident answer for your query. I've created a support ticket — an IT engineer will follow up with you shortly.
        </p>
        <div class="esc-meta">
          <span class="badge badge-amber">Escalated</span>
          <span class="badge badge-gray">Session: ${escapeHtml(data.session_id.slice(0, 8))}…</span>
        </div>
        <p style="font-size:0.75rem; color:var(--text-muted); margin-top:0.75rem;">
          In the meantime, you can also call the IT Helpdesk: <strong style="color:var(--text-secondary);">ext. 4321</strong>
        </p>
      </div>
    </div>
  `;
  messagesContainer.appendChild(row);
}

function renderErrorBubble(message) {
  const row = document.createElement("div");
  row.className = "message-row animate-fade-in";
  row.innerHTML = `
    <div class="avatar avatar-agent">⚠️</div>
    <div class="bubble-content">
      <div class="chat-bubble bubble-escalation" style="border-color:rgba(239,68,68,0.25); background:rgba(239,68,68,0.08);">
        <strong style="color:var(--accent-red);">Error</strong><br>
        ${escapeHtml(message)}
      </div>
    </div>
  `;
  messagesContainer.appendChild(row);
}

function renderTypingIndicator() {
  const row = document.createElement("div");
  row.className = "message-row";
  row.id = "typing-row";
  row.innerHTML = `
    <div class="avatar avatar-agent">🤖</div>
    <div class="chat-bubble bubble-agent" style="padding: 0.75rem 1rem;">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  messagesContainer.appendChild(row);
  return row;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;  // Safe: renders as text node, no innerHTML
  return div.innerHTML;
}

async function checkSystemHealth() {
  try {
    const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
    const data = await resp.json();
    const healthy = data.overall === "healthy";
    statusDot.style.background = healthy ? "var(--accent-green)" : "var(--accent-amber)";
    statusDot.style.boxShadow = `0 0 6px ${healthy ? "var(--accent-green)" : "var(--accent-amber)"}`;
    statusDot.title = `System: ${data.overall}`;
  } catch {
    statusDot.style.background = "var(--accent-red)";
    statusDot.title = "System: unreachable";
  }
}
