/**
 * IT Helpdesk Monitor — Live metrics dashboard JavaScript
 * Polls /health, /metrics/summary, and /security/events every 30 seconds.
 */

const API_BASE = "http://localhost:8000";
const REFRESH_MS = 30_000;

// Bucket labels for confidence histogram (matches backend buckets)
const HIST_BUCKETS = ["0.0","0.1","0.2","0.3","0.4","0.5","0.6","0.7","0.8","0.85","0.9","0.95"];

let confidenceData = new Array(HIST_BUCKETS.length).fill(0);

// ── Boot ─────────────────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", () => {
  refreshAll();
  setInterval(refreshAll, REFRESH_MS);
});

async function refreshAll() {
  await Promise.allSettled([
    refreshHealth(),
    refreshMetrics(),
    refreshSecurityEvents(),
    refreshAppLogs(),
  ]);
  document.getElementById("last-refresh").textContent = new Date().toLocaleTimeString();
}

// ── Health ────────────────────────────────────────────────────────────────────

async function refreshHealth() {
  try {
    const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(6000) });
    const data = await resp.json();

    setDot("dot-overall",  data.overall);
    setDot("dot-search",   data.azure_search);
    setDot("dot-openai",   data.azure_openai);
    setDot("dot-store",    data.escalation_store);

    const label = document.getElementById("label-overall");
    label.textContent = `System: ${data.overall.toUpperCase()}`;
    label.style.color = data.overall === "healthy" ? "var(--accent-green)"
                      : data.overall === "degraded" ? "var(--accent-amber)"
                      : "var(--accent-red)";

    const lats = data.latency_ms || {};
    document.getElementById("latency-info").textContent =
      `Search: ${lats.azure_search ?? "—"}ms | OpenAI: ${lats.azure_openai ?? "—"}ms`;

    document.getElementById("status-dot").style.background =
      data.overall === "healthy" ? "var(--accent-green)" : "var(--accent-amber)";

  } catch {
    setDot("dot-overall", "unhealthy");
  }
}

function setDot(id, status) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = "health-dot " + status;
}

// ── Metrics Summary ───────────────────────────────────────────────────────────

async function refreshMetrics() {
  try {
    const resp = await fetch(`${API_BASE}/metrics/summary`, { signal: AbortSignal.timeout(6000) });
    const data = await resp.json();

    setText("kpi-deflection", `${Math.round((data.deflection_rate || 0) * 100)}%`);
    setText("kpi-total",      data.total_requests ?? 0);
    setText("kpi-deflected",  data.total_deflections ?? 0);
    setText("kpi-escalated",  data.total_escalations ?? 0);
    setText("kpi-blocks",     data.security_blocks_today ?? 0);

    // Update histogram summary
    if (data.total_requests > 0) {
      const dr = Math.round((data.deflection_rate || 0) * 100);
      document.getElementById("hist-summary").textContent =
        `${dr}% of queries answered confidently`;
    }

  } catch { /* keep showing last values */ }
}

// ── Security Events ────────────────────────────────────────────────────────────

async function refreshSecurityEvents() {
  try {
    const resp = await fetch(`${API_BASE}/security/events?limit=20`, { signal: AbortSignal.timeout(6000) });
    const events = await resp.json();

    const tbody = document.getElementById("security-tbody");
    if (!events || events.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--text-muted);">No security events recorded yet</td></tr>`;
      return;
    }

    tbody.innerHTML = events.slice().reverse().map(evt => {
      const time = new Date(evt.timestamp).toLocaleTimeString();
      const threatBadge = threatBadgeHtml(evt.threat_type);
      const severityBadge = severityBadgeHtml(evt.severity);
      const actionBadge = evt.action_taken === "blocked"
        ? '<span class="badge badge-red">Blocked</span>'
        : '<span class="badge badge-gray">Logged</span>';

      return `
        <tr>
          <td style="white-space:nowrap;">${escHtml(time)}</td>
          <td>${threatBadge}</td>
          <td>${severityBadge}</td>
          <td>${actionBadge}</td>
          <td><code style="font-size:0.7rem; color:var(--text-muted);">${escHtml(evt.rule_triggered || "—")}</code></td>
          <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:0.75rem; color:var(--text-muted);" title="${escHtml(evt.input_snippet || "")}">${escHtml(evt.input_snippet || "—")}</td>
        </tr>
      `;
    }).join("");

  } catch { /* keep last state */ }
}

function threatBadgeHtml(type) {
  const labels = {
    prompt_injection: ["badge-red", "Injection"],
    prompt_flooding: ["badge-amber", "Flooding"],
    jailbreak: ["badge-red", "Jailbreak"],
    rate_limit_exceeded: ["badge-amber", "Rate Limit"],
    pii_in_output: ["badge-purple", "PII Output"],
    oversized_input: ["badge-gray", "Oversized"],
    xss_attempt: ["badge-red", "XSS"],
  };
  const [cls, label] = labels[type] || ["badge-gray", type || "Unknown"];
  return `<span class="badge ${cls}">${escHtml(label)}</span>`;
}

function severityBadgeHtml(severity) {
  const map = { critical: "badge-red", high: "badge-red", medium: "badge-amber", low: "badge-gray" };
  return `<span class="badge ${map[severity] || "badge-gray"}">${escHtml(severity || "—")}</span>`;
}

// ── App Logs ──────────────────────────────────────────────────────────────────

async function refreshAppLogs() {
  try {
    // Read recent structured logs from the security events endpoint as a proxy
    // In production, this would stream from Log Analytics / App Insights
    const resp = await fetch(`${API_BASE}/security/events?limit=20`, { signal: AbortSignal.timeout(5000) });
    const events = await resp.json();

    const logStream = document.getElementById("log-stream");

    const lines = events.slice().reverse().map(evt => {
      const time = new Date(evt.timestamp).toLocaleTimeString();
      const level = evt.severity === "critical" || evt.severity === "high" ? "ERROR"
                  : evt.severity === "medium" ? "WARNING" : "INFO";
      const msg = `[SECURITY] ${evt.threat_type} — ${evt.action_taken} (${evt.rule_triggered || "n/a"})`;
      return `<div class="log-line log-${level}">
        <span class="log-time">${escHtml(time)}</span>
        <span class="log-${level}">${level}</span>
        ${escHtml(msg)}
      </div>`;
    });

    if (lines.length === 0) {
      logStream.innerHTML = `<div class="log-line log-INFO"><span class="log-time">${new Date().toLocaleTimeString()}</span><span class="log-INFO">INFO</span> System running normally — no security events</div>`;
    } else {
      logStream.innerHTML = lines.join("");
    }

    logStream.scrollTop = logStream.scrollHeight;

  } catch { /* keep last state */ }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escHtml(text) {
  const d = document.createElement("div");
  d.textContent = String(text);
  return d.innerHTML;
}
