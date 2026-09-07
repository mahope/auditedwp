/* EUComply shell: theme, menu, search palette, article furniture, small comforts.
   No dependencies, no tracking. Everything degrades to plain HTML without it. */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');
  var lang = (root.lang || 'en').slice(0, 2);
  var T = {
    en: { search: 'Search this site', noresults: 'No pages match', results: 'results', copy: 'Copy', copied: 'Copied', top: 'Back to top',
          recent: 'Recent scans', clear: 'clear', link: 'Copy link', linked: 'Link copied', open: 'Open', navigate: 'to navigate', close: 'to close',
          sections: { blog: 'Blog', guides: 'Guides', checklists: 'Checklists', tools: 'Tools', compare: 'Comparisons', pages: 'Pages', deskuptime: 'DeskUptime', devnotify: 'DevNotify', transmute: 'Transmute', store: 'Templates', pro: 'Pro' },
          ago: function (m) { return m < 60 ? m + ' min ago' : m < 1440 ? Math.round(m / 60) + ' h ago' : Math.round(m / 1440) + ' d ago'; } },
    da: { search: 'Søg på sitet', noresults: 'Ingen sider matcher', results: 'resultater', copy: 'Kopiér', copied: 'Kopieret', top: 'Til toppen',
          recent: 'Seneste scanninger', clear: 'ryd', link: 'Kopiér link', linked: 'Link kopieret', open: 'Åbn', navigate: 'for at navigere', close: 'for at lukke',
          sections: { blog: 'Blog', guides: 'Guides', checklists: 'Tjeklister', tools: 'Værktøjer', compare: 'Sammenligninger', pages: 'Sider', deskuptime: 'DeskUptime', devnotify: 'DevNotify', transmute: 'Transmute', store: 'Skabeloner', pro: 'Pro' },
          ago: function (m) { return m < 60 ? m + ' min siden' : m < 1440 ? Math.round(m / 60) + ' t siden' : Math.round(m / 1440) + ' d siden'; } },
    de: { search: 'Website durchsuchen', noresults: 'Keine Seiten gefunden', results: 'Treffer', copy: 'Kopieren', copied: 'Kopiert', top: 'Nach oben',
          recent: 'Letzte Scans', clear: 'leeren', link: 'Link kopieren', linked: 'Link kopiert', open: 'Öffnen', navigate: 'zum Navigieren', close: 'zum Schließen',
          sections: { blog: 'Blog', guides: 'Leitfäden', checklists: 'Checklisten', tools: 'Werkzeuge', compare: 'Vergleiche', pages: 'Seiten', deskuptime: 'DeskUptime', devnotify: 'DevNotify', transmute: 'Transmute', store: 'Vorlagen', pro: 'Pro' },
          ago: function (m) { return m < 60 ? 'vor ' + m + ' Min.' : m < 1440 ? 'vor ' + Math.round(m / 60) + ' Std.' : 'vor ' + Math.round(m / 1440) + ' Tagen'; } },
    fr: { search: 'Rechercher sur le site', noresults: 'Aucune page trouvée', results: 'résultats', copy: 'Copier', copied: 'Copié', top: 'Haut de page',
          recent: 'Scans récents', clear: 'effacer', link: 'Copier le lien', linked: 'Lien copié', open: 'Ouvrir', navigate: 'pour naviguer', close: 'pour fermer',
          sections: { blog: 'Blog', guides: 'Guides', checklists: 'Check-lists', tools: 'Outils', compare: 'Comparatifs', pages: 'Pages', deskuptime: 'DeskUptime', devnotify: 'DevNotify', transmute: 'Transmute', store: 'Modèles', pro: 'Pro' },
          ago: function (m) { return m < 60 ? 'il y a ' + m + ' min' : m < 1440 ? 'il y a ' + Math.round(m / 60) + ' h' : 'il y a ' + Math.round(m / 1440) + ' j'; } }
  };
  var t = T[lang] || T.en;
  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } }
  function copy(text, btn, done, idle) {
    var ok = function () { if (!btn) return; var old = btn.textContent; btn.textContent = done; btn.classList.add('is-done'); setTimeout(function () { btn.textContent = idle || old; btn.classList.remove('is-done'); }, 1600); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, ok);
    else { var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} ta.remove(); ok(); }
  }

  /* ---- Theme: light / dark / system, remembered locally ---- */
  var themeBtn = $('.sh-theme');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var cur = root.getAttribute('data-theme');
      var next = cur === 'light' ? 'dark' : cur === 'dark' ? null : 'light';
      if (next) root.setAttribute('data-theme', next); else root.removeAttribute('data-theme');
      store('theme', next);
    });
  }

  /* ---- Mobile menu ---- */
  var header = $('.sh');
  var btn = header && $('.sh-toggle', header);
  var menu = document.getElementById('sh-menu');
  if (header && btn && menu) {
    var isOpen = function () { return btn.getAttribute('aria-expanded') === 'true'; };
    var setOpen = function (open) { btn.setAttribute('aria-expanded', open ? 'true' : 'false'); header.classList.toggle('is-open', open); };
    btn.addEventListener('click', function () { setOpen(!isOpen()); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && isOpen()) { setOpen(false); btn.focus(); } });
    document.addEventListener('click', function (e) { if (isOpen() && !header.contains(e.target)) setOpen(false); });
    var mq = window.matchMedia('(min-width: 900px)');
    var onChange = function (m) { if (m.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener('change', onChange); else if (mq.addListener) mq.addListener(onChange);
  }

  /* ---- Search: shared index, palette and full page ---- */
  var index = null, loading = null;
  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!loading) loading = fetch('/search-index.json', { credentials: 'omit' }).then(function (r) { return r.json(); }).then(function (j) { index = j; return j; }).catch(function () { index = []; return index; });
    return loading;
  }
  function norm(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  function search(q, items, limit) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    var out = [];
    for (var i = 0; i < items.length; i++) {
      var it = items[i], score = 0, ti = norm(it.title), di = norm(it.description), bi = norm(it.body), tg = norm((it.tags || []).join(' '));
      for (var k = 0; k < terms.length; k++) {
        var w = terms[k], s = 0;
        if (ti.indexOf(w) >= 0) s += ti.indexOf(w) === 0 ? 12 : 8;
        if (tg.indexOf(w) >= 0) s += 4;
        if (di.indexOf(w) >= 0) s += 3;
        if (bi.indexOf(w) >= 0) s += 1;
        if (!s) { score = 0; break; }
        score += s;
      }
      if (score) { if (it.lang === lang) score += 5; out.push({ it: it, score: score }); }
    }
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, limit || 30).map(function (r) { return r.it; });
  }
  function hl(text, q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    var safe = esc(text);
    if (!terms.length) return safe;
    var re = new RegExp('(' + terms.map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|') + ')', 'ig');
    return safe.replace(re, '<mark>$1</mark>');
  }
  function snippet(it, q) {
    var b = it.description || it.body || '';
    var w = norm(q).split(/\s+/).filter(Boolean)[0];
    if (w && norm(b).indexOf(w) < 0 && it.body && norm(it.body).indexOf(w) >= 0) {
      var p = norm(it.body).indexOf(w);
      b = (p > 40 ? '…' : '') + it.body.slice(Math.max(0, p - 40), p + 110) + '…';
    }
    return b.length > 150 ? b.slice(0, 148) + '…' : b;
  }

  var pal = null, palInput, palList, palActive = -1, lastFocus = null;
  function buildPalette() {
    pal = document.createElement('div');
    pal.className = 'pal';
    pal.setAttribute('role', 'dialog');
    pal.setAttribute('aria-modal', 'true');
    pal.setAttribute('aria-label', t.search);
    pal.innerHTML = '<div class="pal-box"><div class="pal-in">' +
      '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>' +
      '<input type="search" autocomplete="off" spellcheck="false" placeholder="' + esc(t.search) + '" aria-label="' + esc(t.search) + '" aria-controls="pal-list" aria-autocomplete="list"><kbd>Esc</kbd></div>' +
      '<ul class="pal-list" id="pal-list" role="listbox"></ul>' +
      '<div class="pal-foot"><span><kbd>↑</kbd><kbd>↓</kbd> ' + esc(t.navigate) + '</span><span><kbd>↵</kbd> ' + esc(t.open) + '</span><span><kbd>Esc</kbd> ' + esc(t.close) + '</span></div></div>';
    document.body.appendChild(pal);
    palInput = $('input', pal);
    palList = $('.pal-list', pal);
    pal.addEventListener('click', function (e) { if (e.target === pal) closePalette(); });
    palInput.addEventListener('input', function () { renderPalette(palInput.value); });
    pal.addEventListener('keydown', function (e) {
      var links = $$('a', palList);
      if (e.key === 'Escape') { e.preventDefault(); closePalette(); }
      else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!links.length) return;
        palActive = (palActive + (e.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
        links.forEach(function (a, i) { a.classList.toggle('is-active', i === palActive); a.setAttribute('aria-selected', i === palActive ? 'true' : 'false'); });
        links[palActive].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter') {
        if (palActive >= 0 && links[palActive]) { e.preventDefault(); links[palActive].click(); }
        else if (palInput.value.trim()) { e.preventDefault(); location.href = (lang === 'en' ? '' : '/' + lang) + '/search/?q=' + encodeURIComponent(palInput.value.trim()); }
      } else if (e.key === 'Tab') {
        var f = [palInput].concat(links);
        var i = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    });
  }
  function renderPalette(q) {
    palActive = -1;
    if (!q.trim()) { palList.innerHTML = ''; return; }
    if (!index) { palList.innerHTML = '<li class="pal-empty">…</li>'; loadIndex().then(function () { renderPalette(palInput.value); }); return; }
    var hits = search(q, index, 24);
    if (!hits.length) { palList.innerHTML = '<li class="pal-empty">' + esc(t.noresults) + ' “' + esc(q) + '”.</li>'; return; }
    var groups = {}, order = [];
    hits.forEach(function (h) { var s = h.section || 'pages'; if (!groups[s]) { groups[s] = []; order.push(s); } groups[s].push(h); });
    palList.innerHTML = order.map(function (s) {
      return '<li class="grp" role="presentation">' + esc(t.sections[s] || s) + '</li>' + groups[s].map(function (h) {
        return '<li role="presentation"><a role="option" href="' + esc(h.url) + '" aria-selected="false"><b>' + hl(h.title, q) + '</b><small>' + hl(snippet(h, q), q) + '</small><span class="lang">' + esc((h.lang || 'en').toUpperCase()) + '</span></a></li>';
      }).join('');
    }).join('');
  }
  function openPalette() {
    if (!pal) buildPalette();
    lastFocus = document.activeElement;
    pal.classList.add('is-open');
    document.body.classList.add('pal-lock');
    palInput.value = '';
    palList.innerHTML = '';
    palInput.focus();
    loadIndex();
  }
  function closePalette() {
    if (!pal) return;
    pal.classList.remove('is-open');
    document.body.classList.remove('pal-lock');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  $$('.sh-search, [data-open-search]').forEach(function (b) { b.addEventListener('click', function (e) { e.preventDefault(); openPalette(); }); });
  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    var typing = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 'k') { e.preventDefault(); if (pal && pal.classList.contains('is-open')) closePalette(); else openPalette(); }
    else if (e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); openPalette(); }
  });

  var srch = $('.srch');
  if (srch) {
    var sq = $('#srch-q'), sres = $('#srch-results'), sstat = $('#srch-status');
    var run = function (q) {
      if (!q.trim()) { sres.innerHTML = ''; sstat.textContent = ''; return; }
      loadIndex().then(function (items) {
        var hits = search(q, items, 60);
        sstat.textContent = hits.length ? hits.length + ' ' + t.results + ' · “' + q + '”' : t.noresults + ' “' + q + '”.';
        sres.innerHTML = hits.map(function (h) {
          return '<li><a href="' + esc(h.url) + '">' + hl(h.title, q) + '</a><span class="lang">' + esc((h.lang || 'en').toUpperCase()) + '</span><p>' + hl(snippet(h, q), q) + '</p><span class="path">' + esc(t.sections[h.section] || h.section || '') + ' · ' + esc(h.url) + '</span></li>';
        }).join('');
        try { history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname); } catch (e) {}
      });
    };
    var q0 = new URLSearchParams(location.search).get('q') || '';
    if (q0) { sq.value = q0; run(q0); }
    $('form', srch).addEventListener('submit', function (e) { e.preventDefault(); run(sq.value); });
    var tmr; sq.addEventListener('input', function () { clearTimeout(tmr); tmr = setTimeout(function () { run(sq.value); }, 180); });
  }

  /* ---- Table of contents: scroll-spy (the last heading above the fold line wins) ---- */
  var tocLinks = $$('.toc-side a');
  if (tocLinks.length) {
    var byId = {}, active = null;
    tocLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var heads = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var spy = function () {
      var line = 120, cur = heads[0];
      for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= line) cur = heads[i]; else break; }
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) cur = heads[heads.length - 1];
      if (!cur) return;
      if (active) active.classList.remove('is-active');
      active = byId[cur.id]; active.classList.add('is-active');
    };
    var spyTick = false;
    window.addEventListener('scroll', function () { if (spyTick) return; spyTick = true; requestAnimationFrame(function () { spy(); spyTick = false; }); }, { passive: true });
    spy();
  }

  /* ---- Copy buttons on code blocks ---- */
  $$('main pre').forEach(function (pre) {
    if (pre.parentNode.classList.contains('pre-wrap')) return;
    var wrap = document.createElement('div'); wrap.className = 'pre-wrap';
    pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
    var b = document.createElement('button'); b.type = 'button'; b.className = 'copy-btn'; b.textContent = t.copy;
    b.addEventListener('click', function () { copy(pre.innerText.replace(/\n$/, ''), b, t.copied, t.copy); });
    wrap.appendChild(b);
  });

  /* ---- Copy-link buttons (article share, scan share) ---- */
  $$('[data-copy-link]').forEach(function (b) {
    b.addEventListener('click', function () { copy(location.href.split('#')[0], b, t.linked, t.link); });
  });

  /* ---- Back to top: bottom-left, after 600px ---- */
  var btt = document.createElement('button');
  btt.type = 'button'; btt.className = 'btt'; btt.setAttribute('aria-label', t.top); btt.title = t.top;
  btt.innerHTML = '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  btt.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); var h1 = $('main h1'); if (h1) { h1.setAttribute('tabindex', '-1'); h1.focus({ preventScroll: true }); } });
  document.body.appendChild(btt);
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () { btt.classList.toggle('is-on', window.scrollY > 600); ticking = false; });
  }, { passive: true });

  /* ---- Prefetch internal pages on intent (same origin, not on Save-Data) ---- */
  var conn = navigator.connection || {};
  if (!conn.saveData && !/2g/.test(conn.effectiveType || '')) {
    var seen = {};
    var pre = function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a || a.origin !== location.origin || a.hasAttribute('download')) return;
      var u = a.href.split('#')[0];
      if (seen[u] || u === location.href.split('#')[0] || !/\/(\?.*)?$/.test(u)) return;
      seen[u] = 1;
      var l = document.createElement('link'); l.rel = 'prefetch'; l.href = u; l.as = 'document'; document.head.appendChild(l);
    };
    document.addEventListener('mouseover', pre, { passive: true });
    document.addEventListener('touchstart', pre, { passive: true });
  }

  /* ---- Tables: sticky header only when the table fits (a scrolling wrapper cannot stick) ---- */
  var fitTables = function () {
    $$('.tbl').forEach(function (w) {
      w.classList.remove('fits');
      var tb = $('table', w);
      if (tb && tb.scrollWidth <= w.clientWidth + 1) w.classList.add('fits');
    });
  };
  fitTables();
  window.addEventListener('resize', fitTables, { passive: true });

  /* ---- External links: opener safety and a small mark ---- */
  $$('main a[href^="http"]').forEach(function (a) {
    if (a.host === location.host || a.querySelector('img, svg')) return;
    var rel = (a.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
    if (rel.indexOf('noopener') < 0) rel.push('noopener');
    a.setAttribute('rel', rel.join(' '));
    if (!a.classList.contains('ext') && a.textContent.trim().length > 1 && a.closest('.btn, .btn-primary, .btn-secondary, .pn, .keep-reading, .further-reading, .post') === null) {
      a.classList.add('ext');
      a.insertAdjacentHTML('beforeend', '<svg class="ic ic-ext" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>');
    }
  });

  /* ---- Report a bug (footer) opens the BugBottle panel ---- */
  $$('.sf-bug').forEach(function (b) {
    b.addEventListener('click', function () {
      var host = $('[data-bugbottle="ui"]');
      var trig = host && host.shadowRoot && host.shadowRoot.querySelector('button.trigger');
      if (trig) trig.click(); else location.href = 'https://bugbottle.dev';
    });
  });

  /* ---- Scan page: remember recent scans locally and show when a result arrived ---- */
  var scanForm = document.getElementById('scan-form'), cards = document.getElementById('cards');
  if (scanForm && cards) {
    var KEY = 'ec.recent';
    var read = function () { try { return JSON.parse(store(KEY) || '[]'); } catch (e) { return []; } };
    var box = document.createElement('div'); box.className = 'recent'; box.setAttribute('aria-label', t.recent);
    var after = document.getElementById('scan-err') || scanForm;
    after.parentNode.insertBefore(box, after.nextSibling);
    var render = function () {
      var list = read();
      if (!list.length) { box.innerHTML = ''; box.hidden = true; return; }
      box.hidden = false;
      var now = Date.now();
      box.innerHTML = '<span>' + esc(t.recent) + ':</span>' + list.map(function (r) {
        return '<a href="?url=' + encodeURIComponent(r.host) + '" title="' + esc(t.ago(Math.max(1, Math.round((now - r.at) / 60000)))) + '">' + esc(r.host) + (r.score != null ? ' · ' + esc(r.score) : '') + '</a>';
      }).join('') + '<button type="button">' + esc(t.clear) + '</button>';
      $('button', box).addEventListener('click', function () { store(KEY, null); render(); });
    };
    render();
    var mo = new MutationObserver(function () {
      if (!cards.querySelector('.rcard')) return;
      var host = new URLSearchParams(location.search).get('url');
      if (!host) return;
      var scoreEl = document.getElementById('score-num');
      var score = scoreEl && /\d/.test(scoreEl.textContent) ? scoreEl.textContent.trim() : null;
      var list = read().filter(function (r) { return r.host !== host; });
      list.unshift({ host: host, score: score, at: Date.now() });
      store(KEY, JSON.stringify(list.slice(0, 6)));
      render();
      var meta = document.getElementById('score-meta');
      if (meta && !meta.querySelector('.last-scanned')) {
        var d = new Date();
        meta.insertAdjacentHTML('beforeend', ' <span class="last-scanned"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12l5 5L20 6"/></svg><time datetime="' + d.toISOString() + '">' + d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC</time></span>');
      }
    });
    mo.observe(cards, { childList: true });
  }

  /* ---- Checklists: keep ticks between visits, offer a reset ---- */
  var boxes = $$('main label.item input[type="checkbox"]');
  if (boxes.length > 4) {
    var CK = 'ec.check:' + location.pathname;
    var saved = {}; try { saved = JSON.parse(store(CK) || '{}'); } catch (e) {}
    boxes.forEach(function (b, i) {
      if (saved[i]) { b.checked = true; b.dispatchEvent(new Event('change', { bubbles: true })); }
      b.addEventListener('change', function () { saved[i] = b.checked ? 1 : 0; store(CK, JSON.stringify(saved)); });
    });
  }
})();
