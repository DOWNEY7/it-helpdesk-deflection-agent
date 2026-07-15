/**
 * IT Helpdesk Admin — Escalation Queue JavaScript
 */

const API_BASE = "http://localhost:8000";
let allTickets = [];
let activeTicketId = null;

window.addEventListener("DOMContentLoaded", () => {
  loadTickets();
  document.getElementById("filter-status").addEventListener("change", renderTable);
  document.getElementById("filter-category").addEventListener("change", renderTable);
  checkHealth();
});

// ── Load tickets ────────────────────────────────────────────────────────────

async function loadTickets() {
  try {
    const resp = await fetch(`${API_BASE}/escalations?limit=200`);
    allTickets = await resp.json();
    renderTable();
    updateKPIs();
  } catch {
    document.getElementById("tickets-tbody").innerHTML =
      `<tr><td colspan="7" style="text-align:center;padding:3rem;color:var(--accent-red);">Failed to load tickets — is the backend running?</td></tr>`;
  }
}

// ── Render table ────────────────────────────────────────────────────────────

function renderTable() {
  const statusFilter   = document.getElementById("filter-status").value;
  const categoryFilter = document.getElementById("filter-category").value;

  let filtered = allTickets.filter(t => {
    if (statusFilter && t.status !== statusFilter) return false;
    if (categoryFilter && t.category !== categoryFilter) return false;
    return true;
  });

  const tbody = document.getElementById("tickets-tbody");

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:3rem;color:var(--text-muted);">No tickets match your filters</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(t => {
    const urgencyBadge = urgencyBadgeHtml(t.urgency);
    const statusBadge  = statusBadgeHtml(t.status);
    const catBadge     = `<span class="badge badge-blue">${escHtml(t.category)}</span>`;
    const confPct      = Math.round((t.confidence_score || 0) * 100);
    const confColor    = confPct >= 70 ? "var(--accent-green)" : "var(--accent-red)";
    const created      = new Date(t.created_at).toLocaleDateString("en-GB", { day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit" });

    return `
      <tr class="ticket-row animate-fade-in" onclick="openTicket('${escHtml(t.ticket_id)}')">
        <td class="ticket-id-cell" style="font-family:'Courier New',monospace; font-size:0.72rem; color:var(--text-muted);">${escHtml(t.ticket_id)}</td>
        <td style="max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escHtml(t.summary)}</td>
        <td>${catBadge}</td>
        <td>${urgencyBadge}</td>
        <td>${statusBadge}</td>
        <td>
          <div style="display:flex; align-items:center; gap:0.4rem;">
            <div style="flex:1; height:4px; background:rgba(255,255,255,0.08); border-radius:99px; overflow:hidden; min-width:40px;">
              <div style="width:${confPct}%; height:100%; background:${confColor}; border-radius:99px;"></div>
            </div>
            <span style="font-size:0.7rem; color:var(--text-muted);">${confPct}%</span>
          </div>
        </td>
        <td style="white-space:nowrap; font-size:0.8rem; color:var(--text-muted);">${escHtml(created)}</td>
      </tr>
    `;
  }).join("");
}

function updateKPIs() {
  const today = new Date().toDateString();
  document.getElementById("kpi-open").textContent = allTickets.filter(t => t.status === "open").length;
  document.getElementById("kpi-inprogress").textContent = allTickets.filter(t => t.status === "in_progress").length;
  document.getElementById("kpi-resolved").textContent = allTickets.filter(t =>
    t.status === "resolved" && new Date(t.resolved_at || t.created_at).toDateString() === today
  ).length;
  document.getElementById("kpi-total").textContent = allTickets.length;
}

// ── Slide-over ──────────────────────────────────────────────────────────────

function openTicket(ticketId) {
  const ticket = allTickets.find(t => t.ticket_id === ticketId);
  if (!ticket) return;
  activeTicketId = ticketId;

  document.getElementById("so-ticket-id").textContent = ticket.ticket_id;
  document.getElementById("so-summary").textContent = ticket.summary;
  document.getElementById("so-badges").innerHTML = [
    urgencyBadgeHtml(ticket.urgency),
    `<span class="badge badge-blue">${escHtml(ticket.category)}</span>`,
    statusBadgeHtml(ticket.status),
    ticket.retrieval_miss ? `<span class="badge badge-gray">No KB Match</span>` : "",
  ].join("");

  document.getElementById("so-status-select").value = ticket.status;

  // Render conversation
  const conv = document.getElementById("so-conversation");
  if (!ticket.conversation_history || ticket.conversation_history.length === 0) {
    conv.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;">No conversation history recorded.</p>`;
  } else {
    conv.innerHTML = ticket.conversation_history.map(msg => `
      <div class="conv-message">
        <div class="conv-role">${escHtml(msg.role)}</div>
        <div class="conv-content conv-${escHtml(msg.role)}">${escHtml(msg.content)}</div>
      </div>
    `).join("");
  }

  document.getElementById("backdrop").classList.add("open");
  document.getElementById("slide-over").classList.add("open");
}

function closeSlideOver() {
  document.getElementById("backdrop").classList.remove("open");
  document.getElementById("slide-over").classList.remove("open");
  activeTicketId = null;
}

async function saveTicketUpdate() {
  if (!activeTicketId) return;
  const newStatus = document.getElementById("so-status-select").value;

  try {
    const resp = await fetch(`${API_BASE}/escalations/${activeTicketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (resp.ok) {
      closeSlideOver();
      loadTickets();
    }
  } catch { /* silently fail */ }
}

// ── Badge helpers ────────────────────────────────────────────────────────────

function urgencyBadgeHtml(urgency) {
  const map = { critical:"badge-red", high:"badge-red", medium:"badge-amber", low:"badge-gray" };
  return `<span class="badge ${map[urgency] || "badge-gray"}">${escHtml(urgency || "—")}</span>`;
}

function statusBadgeHtml(status) {
  const map = { open:"badge-red", in_progress:"badge-amber", resolved:"badge-green", closed:"badge-gray" };
  return `<span class="badge ${map[status] || "badge-gray"}">${escHtml(status?.replace("_"," ") || "—")}</span>`;
}

function escHtml(text) {
  const d = document.createElement("div");
  d.textContent = String(text ?? "");
  return d.innerHTML;
}

async function checkHealth() {
  try {
    const resp = await fetch(`${API_BASE}/health`);
    const data = await resp.json();
    const dot = document.getElementById("status-dot");
    dot.style.background = data.overall === "healthy" ? "var(--accent-green)" : "var(--accent-amber)";
  } catch {
    document.getElementById("status-dot").style.background = "var(--accent-red)";
  }
}
