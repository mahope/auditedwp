/**
 * DevNotify Chrome Extension — Background Service Worker
 *
 * Polls GitHub API for notifications, updates badge count,
 * and caches results for the popup UI.
 */

// ─── Configuration ────────────────────────────────────────────────────────────

const POLL_INTERVAL_FREE = 10;    // minutes
const POLL_INTERVAL_PRO  = 2;     // minutes
const MAX_NOTIFICATIONS_FREE = 5;
const MAX_NOTIFICATIONS_PRO  = 100;
const GH_API = 'https://api.github.com';

// ─── Premium check ────────────────────────────────────────────────────────────

async function isPro() {
  const { licenseKey } = await chrome.storage.sync.get('licenseKey');
  if (!licenseKey) return false;
  // Simple offline validation: key format devnotify-XXXX-XXXX-XXXX
  const valid = /^devnotify-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/i.test(licenseKey);
  return valid;
}

// ─── GitHub API ───────────────────────────────────────────────────────────────

async function getAuthHeaders() {
  const { token } = await chrome.storage.sync.get('token');
  if (!token) return null;
  return {
    'Authorization': `Bearer ${token}`,
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'DevNotify/1.0',
  };
}

async function fetchNotifications() {
  const headers = await getAuthHeaders();
  if (!headers) return { error: 'no-token', notifications: [] };

  const pro = await isPro();
  const max = pro ? 100 : 5;
  const polling = pro ? '2' : '10';
  const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(); // 7 days

  try {
    const url = `${GH_API}/notifications?per_page=${max}&participating=true&since=${since}`;
    const res = await fetch(url, { headers });

    if (res.status === 401) return { error: 'bad-token', notifications: [] };
    if (res.status === 403) return { error: 'rate-limited', notifications: [] };
    if (!res.ok) return { error: `http-${res.status}`, notifications: [] };

    const data = await res.json();
    const items = (data || []).map(n => ({
      id: n.id,
      repo: n.repository?.full_name || 'unknown',
      title: n.subject?.title || 'No title',
      type: n.subject?.type || 'Unknown',
      url: n.subject?.url || '',
      htmlUrl: n.repository?.html_url || '',
      reason: n.reason || 'subscribed',
      unread: n.unread !== false,
      updatedAt: n.updated_at || new Date().toISOString(),
    }));

    return { error: null, notifications: items };
  } catch (e) {
    return { error: 'network-error', notifications: [] };
  }
}

// ─── Badge ────────────────────────────────────────────────────────────────────

async function updateBadge(count) {
  const text = count > 0 ? String(Math.min(count, 99)) : '';
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color: '#ef4444' }); // Red-500
}

// ─── Polling ──────────────────────────────────────────────────────────────────

let cachedNotifications = [];

async function poll() {
  const { token } = await chrome.storage.sync.get('token');
  if (!token) {
    await updateBadge(0);
    return;
  }

  const result = await fetchNotifications();
  if (result.error === 'no-token' || result.error === 'bad-token') {
    await updateBadge(0);
    return;
  }

  cachedNotifications = result.notifications;
  const unread = result.notifications.filter(n => n.unread).length;
  await updateBadge(unread);
}

// ─── Alarms ───────────────────────────────────────────────────────────────────

async function rescheduleAlarm() {
  await chrome.alarms.clear('poll');
  const pro = await isPro();
  const interval = pro ? POLL_INTERVAL_PRO : POLL_INTERVAL_FREE;
  await chrome.alarms.create('poll', { periodInMinutes: interval });
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'poll') poll();
});

// ─── Message handlers (popup → background) ────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  switch (msg.action) {
    case 'get-notifications':
      sendResponse({ notifications: cachedNotifications });
      break;
    case 'get-status':
      chrome.storage.sync.get(['token', 'licenseKey'], (data) => {
        sendResponse({
          hasToken: !!data.token,
          isPro: /^devnotify-/i.test(data.licenseKey || ''),
        });
      });
      return true; // Keep channel open for async
    case 'refresh':
      poll().then(() => {
        sendResponse({ ok: true, count: cachedNotifications.filter(n => n.unread).length });
      });
      return true;
  }
});

// ─── Init ─────────────────────────────────────────────────────────────────────

// On install/update: set up initial alarm
chrome.runtime.onInstalled.addListener(async () => {
  await rescheduleAlarm();
  await poll();
});

// Also start immediately
rescheduleAlarm();
poll();