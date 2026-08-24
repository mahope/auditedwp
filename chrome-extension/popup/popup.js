/**
 * DevNotify Chrome Extension — Popup Script
 * Handles UI state, settings, and communication with background worker.
 */

(function () {

// ─── DOM refs ────────────────────────────────────────────────────────────────

const $ = (id) => document.getElementById(id);

const countBadge = $('count-badge');
const statusBanner = $('status-banner');
const mainContent = $('main-content');
const loading = $('loading');
const emptyState = $('empty-state');
const notifList = $('notif-list');
const settingsPanel = $('settings-panel');
const tokenInput = $('token');
const licenseInput = $('license-key');
const btnRefresh = $('btn-refresh');
const btnSettings = $('btn-settings');
const btnSave = $('btn-save');
const btnBack = $('btn-back');
const footerStatus = $('footer-status');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function typeShort(type) {
  switch (type) {
    case 'PullRequest': return 'PR';
    case 'Issue': return 'IS';
    case 'Commit': return 'CM';
    case 'Discussion': return 'DS';
    case 'Release': return 'RL';
    case 'CheckSuite': return 'CI';
    default: return type.charAt(0).toUpperCase();
  }
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ─── Render notifications ────────────────────────────────────────────────────

function renderNotifs(notifications) {
  loading.classList.add('hidden');
  notifList.classList.remove('hidden');

  if (!notifications || notifications.length === 0) {
    notifList.classList.add('hidden');
    emptyState.classList.remove('hidden');
    countBadge.textContent = '0';
    return;
  }

  emptyState.classList.add('hidden');
  const unread = notifications.filter(n => n.unread).length;
  countBadge.textContent = String(unread);

  notifList.innerHTML = notifications
    .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    .map(n => {
      const typeClass = n.type || 'default';
      return `
        <div class="notif-item ${n.unread ? 'unread' : 'read'}"
             data-url="${escapeAttr(n.htmlUrl)}">
          <div class="notif-type ${typeClass}">${typeShort(n.type)}</div>
          <div class="notif-content">
            <div class="notif-repo">${escapeHtml(n.repo)}</div>
            <div class="notif-title">${escapeHtml(n.title)}</div>
            <div class="notif-meta">${n.reason} · ${timeAgo(n.updatedAt)}</div>
          </div>
        </div>
      `;
    })
    .join('');

  // Click to open
  document.querySelectorAll('.notif-item').forEach(el => {
    el.addEventListener('click', () => {
      const url = el.dataset.url;
      if (url) chrome.tabs.create({ url });
    });
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s || '';
  return div.innerHTML;
}

function escapeAttr(s) {
  return (s || '').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─── Status banner ────────────────────────────────────────────────────────────

function showBanner(text, type, action) {
  statusBanner.classList.remove('hidden', 'error', 'success');
  if (type) statusBanner.classList.add(type);
  statusBanner.innerHTML = `<span class="icon">${type === 'error' ? '⚠' : 'ℹ'}</span> ${text}`;
  if (action) {
    const link = document.createElement('a');
    link.href = '#';
    link.textContent = action.label || 'Open settings';
    link.addEventListener('click', (e) => {
      e.preventDefault();
      showSettings();
      if (action.callback) action.callback();
    });
    statusBanner.appendChild(link);
  }
}

function hideBanner() {
  statusBanner.classList.add('hidden');
}

// ─── Settings ─────────────────────────────────────────────────────────────────

function showSettings() {
  mainContent.classList.add('hidden');
  settingsPanel.classList.add('visible');
  chrome.storage.sync.get(['token', 'licenseKey'], (data) => {
    tokenInput.value = data.token || '';
    licenseInput.value = data.licenseKey || '';
  });
}

function hideSettings() {
  mainContent.classList.remove('hidden');
  settingsPanel.classList.remove('visible');
  loadAndRender();
}

btnSettings.addEventListener('click', showSettings);
btnBack.addEventListener('click', hideSettings);

btnSave.addEventListener('click', () => {
  const token = tokenInput.value.trim();
  const licenseKey = licenseInput.value.trim();

  chrome.storage.sync.set({ token, licenseKey }, () => {
    showBanner('Settings saved!', 'success');
    setTimeout(hideBanner, 2000);
    // Notify background to re-schedule alarm (token/license changed)
    chrome.runtime.sendMessage({ action: 'refresh' });
    hideSettings();
  });
});

// ─── Refresh ──────────────────────────────────────────────────────────────────

btnRefresh.addEventListener('click', () => {
  btnRefresh.textContent = '…';
  btnRefresh.disabled = true;
  chrome.runtime.sendMessage({ action: 'refresh' }, () => {
    loadAndRender();
    btnRefresh.textContent = '↻';
    btnRefresh.disabled = false;
  });
});

// ─── Load and render ─────────────────────────────────────────────────────────

function loadAndRender() {
  chrome.runtime.sendMessage({ action: 'get-notifications' }, (response) => {
    const notifs = (response && response.notifications) || [];
    renderNotifs(notifs);
  });
}

// ─── Init ────────────────────────────────────────────────────────────────────

// Check status
chrome.runtime.sendMessage({ action: 'get-status' }, (status) => {
  if (!status || !status.hasToken) {
    showBanner('Connect your GitHub account to see notifications.', null, { label: 'Connect' });
  }
  footerStatus.textContent = status && status.isPro ? '🔓 Pro' : '🔒 Free';
});

loadAndRender();

})();