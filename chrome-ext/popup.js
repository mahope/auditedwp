// EUComply Chrome Extension — Popup Script
(function() {
  'use strict';

  const API = 'https://eucomply-scan.mahope-eeb.workers.dev';
  const form = document.getElementById('scan-form');
  const input = document.getElementById('url-input');
  const btn = document.getElementById('scan-btn');
  const errEl = document.getElementById('scan-err');
  const initial = document.getElementById('initial-state');
  const result = document.getElementById('result');
  const checksEl = document.getElementById('checks-list');

  // --- Pre-fill with current tab's domain ---
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs[0] && tabs[0].url) {
      try {
        var u = new URL(tabs[0].url);
        input.value = u.hostname;
        input.placeholder = u.hostname;
      } catch(_) {
        // keep default placeholder
      }
    }
  });

  // --- Form submit ---
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    var url = input.value.trim();
    errEl.textContent = '';
    if (!url) { errEl.textContent = 'Please enter a domain.'; return; }

    // Show scanning state
    initial.style.display = 'none';
    result.style.display = 'none';
    btn.disabled = true;
    document.getElementById('status-info').textContent = 'Scanning…';

    try {
      var r = await fetch(API + '/scan?url=' + encodeURIComponent(url));
      var d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Scan failed.');
      render(d);

      // Store in Chrome storage for badge
      chrome.storage.local.set({ lastScan: { url: url, score: d.score.pct } });

    } catch (ex) {
      errEl.textContent = ex.message || 'Network error. Try again.';
      btn.disabled = false;
      document.getElementById('status-info').textContent = 'Free · No account needed';
    }
  });

  function render(d) {
    result.style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Scan again';
    document.getElementById('status-info').textContent = d.platform !== 'Unknown'
      ? d.platform + ' · Score: ' + d.score.pct + '%'
      : 'Score: ' + d.score.pct + '%';

    var pct = d.score.pct;
    var cls = pct >= 80 ? 'good' : (pct >= 50 ? 'mid' : 'bad');
    var num = document.getElementById('score-num');
    num.textContent = pct + '%';
    num.className = 'scorenum ' + cls;

    document.getElementById('score-meta').textContent =
      d.score.passed + ' of ' + d.score.total + ' checks passed';

    checksEl.innerHTML = '';
    Object.entries(d.checks).forEach(function(pair) {
      var c = pair[1];
      var v = c.warn && !c.pass ? 'warn' : (!c.pass && !c.warn ? 'fail' : c.warn ? 'warn' : 'pass');
      var pill = c.warn && !c.pass ? 'Check manually' : (c.warn ? 'Warning' : c.pass ? 'Pass' : 'Fix needed');

      var div = document.createElement('div');
      div.className = 'check ' + v;
      var html = '<strong>' + icon(pair[0]) + ' ' + esc(c.label || pair[0]) +
                 ' <span class="pill">' + pill + '</span></strong>';
      if (c.detail) html += '<div class="detail">' + esc(c.detail) + '</div>';
      if ((!c.pass || c.warn) && c.fix) {
        html += '<div class="fix"><strong>Fix:</strong> ' + esc(c.fix) + '</div>';
      }
      div.innerHTML = html;
      checksEl.appendChild(div);
    });
  }

  function icon(k) {
    return ({ssl:'🔒',cookies:'🍪',forms:'📋',legal:'📄',headers:'🛡️',consent_mode_v2:'📊',tcf:'🏛️',trackers:'🎯',dora:'🏦'})[k] || '•';
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function(m) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m];
    });
  }
})();