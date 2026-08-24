const { invoke } = window.__TAURI__.core;
const { shell } = window.__TAURI__;

// ── State ────────────────────────────────────────────────────────

let currentPanel = "settings";
let savedToken = null;

// ── DOM references ────────────────────────────────────────────────

const els = {
  settingsPanel: document.getElementById("settings-panel"),
  notifPanel: document.getElementById("notifications-panel"),
  providerSelect: document.getElementById("provider-select"),
  tokenHint: document.getElementById("token-hint"),
  tokenInput: document.getElementById("token-input"),
  saveTokenBtn: document.getElementById("save-token-btn"),
  testTokenBtn: document.getElementById("test-token-btn"),
  settingsStatus: document.getElementById("settings-status"),
  notifList: document.getElementById("notification-list"),
  unreadBadge: document.getElementById("unread-badge"),
  refreshBtn: document.getElementById("refresh-notifs-btn"),
  settingsBtn: document.getElementById("settings-btn"),
  showNotifBtn: document.getElementById("show-notifications-btn"),
};

// ── Provider info (mirrors Rust providers.rs) ────────────────────

const PROVIDER_INFO = {
  github: {
    label: "GitHub",
    tokenUrl: "https://github.com/settings/tokens",
    hint:
      'Create a <a href="#" id="token-link" class="token-link">token on GitHub</a> with notifications and repo scopes.',
  },
  gitlab: {
    label: "GitLab",
    tokenUrl: "https://gitlab.com/-/user_settings/personal_access_tokens",
    hint:
      'Create a <a href="#" id="token-link" class="token-link">token on GitLab</a> with the read_api scope.',
  },
};

function currentProvider() {
  return els.providerSelect.value;
}

function updateProviderUI() {
  const info = PROVIDER_INFO[currentProvider()];
  if (!info) return;
  els.tokenHint.innerHTML = info.hint;
  const link = document.getElementById("token-link");
  if (link) {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      invoke("open_url", { url: info.tokenUrl });
    });
  }
}

async function saveProviderSelection() {
  try {
    await invoke("save_provider", { provider: currentProvider() });
  } catch (err) {
    console.error("save_provider:", err);
  }
}

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
    await saveProviderSelection();
    await invoke("save_token", { token });
    savedToken = token;
    els.settingsStatus.textContent = `Token saved ✓ Connected to ${PROVIDER_INFO[currentProvider()].label}`;
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

// ── Trial / license ──────────────────────────────────────────────

async function refreshTrialStatus() {
  try {
    const t = await invoke("get_trial_status");
    const box = document.getElementById("trial-box");
    const badge = document.getElementById("unread-badge");
    if (t.licensed) {
      box.style.display = "none";
      return;
    }
    box.style.display = "block";
    if (t.expired) {
      badge.textContent = "Trial ended — buy a $19 license to continue";
      const st = document.getElementById("license-status");
      if (st && !st.textContent) {
        st.textContent =
          "Your free 7-day trial has ended. Buy a license and paste the key above.";
        st.className = "status-msg error";
      }
      showPanel("settings");
    } else if (t.trial_days_left <= 2) {
      badge.textContent = `Trial: ${t.trial_days_left} day${t.trial_days_left !== 1 ? "s" : ""} left`;
    }
  } catch (err) {
    console.error("trial status:", err);
  }
}

async function activateLicense() {
  const input = document.getElementById("license-input");
  const status = document.getElementById("license-status");
  const key = input.value.trim();
  if (!key) {
    status.textContent = "Please paste your license key";
    status.className = "status-msg error";
    return;
  }
  try {
    await invoke("activate_license", { key });
    status.textContent = "License activated ✓ Thank you!";
    status.className = "status-msg success";
    setTimeout(() => refreshNotifications(), 500);
  } catch (err) {
    status.textContent = `Error: ${err}`;
    status.className = "status-msg error";
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

document
  .getElementById("activate-license-btn")
  .addEventListener("click", activateLicense);

const BUY_URL = "https://auditedwp.pages.dev/devnotify/#buy";
document.getElementById("buy-license-btn").addEventListener("click", () => {
  invoke("open_url", { url: BUY_URL });
});

// ── Init ─────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", async () => {
  try {
    const p = await invoke("get_provider");
    if (p && PROVIDER_INFO[p]) els.providerSelect.value = p;
  } catch (_) {}
  updateProviderUI();
  await loadSavedToken();
  await refreshTrialStatus();
  // If token exists, show notifications by default
  if (savedToken) {
    showPanel("notifications");
  }
});

els.providerSelect.addEventListener("change", updateProviderUI);