const { invoke } = window.__TAURI__.core;
const { shell } = window.__TAURI__;

// ── State ────────────────────────────────────────────────────────

let currentPanel = "settings";
let savedToken = null;

// ── DOM references ────────────────────────────────────────────────

const els = {
  settingsPanel: document.getElementById("settings-panel"),
  notifPanel: document.getElementById("notifications-panel"),
  tokenInput: document.getElementById("token-input"),
  saveTokenBtn: document.getElementById("save-token-btn"),
  testTokenBtn: document.getElementById("test-token-btn"),
  settingsStatus: document.getElementById("settings-status"),
  notifList: document.getElementById("notification-list"),
  unreadBadge: document.getElementById("unread-badge"),
  refreshBtn: document.getElementById("refresh-notifs-btn"),
  settingsBtn: document.getElementById("settings-btn"),
  showNotifBtn: document.getElementById("show-notifications-btn"),
  tokenLink: document.getElementById("token-link"),
};

// ── Panel switching ──────────────────────────────────────────────

function showPanel(name) {
  currentPanel = name;
  els.settingsPanel.style.display = name === "settings" ? "block" : "none";
  els.notifPanel.style.display = name === "notifications" ? "block" : "none";
  if (name === "notifications") {
    refreshNotifications();
  }
}

// ── Token management ────────────────────────────────────────────

async function loadSavedToken() {
  const token = await invoke("get_token");
  if (token) {
    savedToken = token;
    els.tokenInput.value = token;
    els.settingsStatus.textContent = "Token loaded";
    els.settingsStatus.className = "status-msg success";
  }
}

async function saveToken() {
  const token = els.tokenInput.value.trim();
  if (!token) {
    els.settingsStatus.textContent = "Please enter a token";
    els.settingsStatus.className = "status-msg error";
    return;
  }
  try {
    await invoke("save_token", { token });
    savedToken = token;
    els.settingsStatus.textContent = "Token saved ✓";
    els.settingsStatus.className = "status-msg success";
  } catch (err) {
    els.settingsStatus.textContent = `Error: ${err}`;
    els.settingsStatus.className = "status-msg error";
  }
}

async function testToken() {
  const token = els.tokenInput.value.trim();
  if (!token) {
    els.settingsStatus.textContent = "Please enter a token first";
    els.settingsStatus.className = "status-msg error";
    return;
  }
  try {
    const count = await invoke("check_now");
    if (count === 0) {
      els.settingsStatus.textContent =
        "Connection OK! No unread notifications.";
    } else {
      els.settingsStatus.textContent = `Connection OK! ${count} unread notification(s).`;
    }
    els.settingsStatus.className = "status-msg success";
  } catch (err) {
    els.settingsStatus.textContent = `Error: ${err}`;
    els.settingsStatus.className = "status-msg error";
  }
}

// ── Notifications rendering ─────────────────────────────────────

async function refreshNotifications() {
  els.notifList.innerHTML = '<p class="loading">Refreshing…</p>';
  try {
    const count = await invoke("check_now");
    const notifs = await invoke("get_notifications");
    const lastCheck = await invoke("get_last_check");
    renderNotifications(notifs, count, lastCheck);
  } catch (err) {
    els.notifList.innerHTML = `
      <div class="notif-empty">
        <div class="emoji">⚠️</div>
        <p>${err}</p>
      </div>`;
  }
}

function renderNotifications(notifs, count, lastCheck) {
  els.unreadBadge.textContent =
    count > 0
      ? `${count} unread notification${count !== 1 ? "s" : ""}`
      : "All caught up!";

  if (notifs.length === 0) {
    els.notifList.innerHTML = `
      <div class="notif-empty">
        <div class="emoji">✅</div>
        <p>No unread notifications</p>
      </div>`;
    return;
  }

  let html = "";
  for (const n of notifs) {
    const typeLabel = n.notification_type.replace(/_/g, " ").toLowerCase();
    const timeAgo = getTimeAgo(n.updated_at);
    html += `
      <div class="notification-item" data-url="${n.repo_url}">
        <div class="notif-title">${escapeHtml(n.title)}</div>
        <div class="notif-meta">${escapeHtml(n.repo)}</div>
        <div class="notif-meta">${timeAgo}</div>
        <span class="notif-type">${escapeHtml(typeLabel)}</span>
      </div>`;
  }
  els.notifList.innerHTML = html;

  // Click handlers — open in browser
  for (const el of els.notifList.querySelectorAll(".notification-item")) {
    el.addEventListener("click", () => {
      const url = el.dataset.url;
      if (url) {
        invoke("open_url", { url });
      }
    });
  }
}

// ── Utilities ─────────────────────────────────────────────────────

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function getTimeAgo(isoString) {
  const now = new Date();
  const date = new Date(isoString);
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD}d ago`;
  return date.toLocaleDateString();
}

// ── Expose for Rust backend ──────────────────────────────────────

window.refreshNotifications = refreshNotifications;

// ── Event handlers ───────────────────────────────────────────────

els.saveTokenBtn.addEventListener("click", saveToken);
els.testTokenBtn.addEventListener("click", testToken);
els.refreshBtn.addEventListener("click", refreshNotifications);
els.settingsBtn.addEventListener("click", () => showPanel("settings"));
els.showNotifBtn.addEventListener("click", () => showPanel("notifications"));

els.tokenLink.addEventListener("click", (e) => {
  e.preventDefault();
  invoke("open_url", { url: "https://github.com/settings/tokens" });
});

// ── Init ─────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", async () => {
  await loadSavedToken();
  // If token exists, show notifications by default
  if (savedToken) {
    showPanel("notifications");
  }
});