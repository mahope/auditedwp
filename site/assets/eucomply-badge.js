/**
 * EUComply Compliance Badge
 * Embeddable widget — shows "Scanned by EUComply" on any website.
 * 
 * Usage:
 *   <script async src="https://auditedwp.pages.dev/assets/eucomply-badge.js"
 *           data-eucomply-badge
 *           data-url="https://example.com"
 *           data-position="bottom-right"></script>
 *
 * Options (data-attributes):
 *   data-url        — Your site URL (default: window.location.origin)
 *   data-position   — bottom-left | bottom-right (default: bottom-right)
 *   data-theme      — light | dark (default: light)
 *   data-hide-link  — true to show badge text without hyperlink (default: false)
 */
(function () {
  "use strict";

  var SCRIPT = document.currentScript || document.querySelector('script[data-eucomply-badge]');
  if (!SCRIPT) return;

  var ORIGIN = 'https://auditedwp.pages.dev';
  var SITE_URL = SCRIPT.getAttribute('data-url') || window.location.origin;
  var POSITION = SCRIPT.getAttribute('data-position') || 'bottom-right';
  var THEME    = SCRIPT.getAttribute('data-theme') || 'light';
  var HIDE_LINK = SCRIPT.getAttribute('data-hide-link') === 'true';

  // Already injected on this page?
  if (document.getElementById('eucomply-badge-container')) return;

  var isDark = THEME === 'dark';
  var colors = {
    bg: isDark ? '#1a2332' : '#ffffff',
    text: isDark ? '#d0d8e0' : '#4a5a6a',
    accent: '#2868d0',
    border: isDark ? '#2d3a4a' : '#d0d8e0',
    ok: '#1a7a44',
  };

  var container = document.createElement('div');
  container.id = 'eucomply-badge-container';
  container.setAttribute('aria-label', 'EU Compliance Badge — Scanned by EUComply');

  var edge = POSITION === 'bottom-left' ? 'left' : 'right';
  container.style.cssText = [
    'position:fixed',
    'bottom:16px',
    edge + ':16px',
    'z-index:2147483647',
    'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif',
    'font-size:12px',
    'line-height:1.4',
    'border:1px solid ' + colors.border,
    'border-radius:8px',
    'background:' + colors.bg,
    'padding:8px 12px 8px 10px',
    'box-shadow:0 2px 8px rgba(0,0,0,.08)',
    'color:' + colors.text,
    'display:flex',
    'align-items:center',
    'gap:8px',
    'transition:opacity .2s,transform .2s',
    'opacity:0',
    'transform:' + (edge === 'right' ? 'translateX(20px)' : 'translateX(-20px)'),
  ].join(';');

  // Shield icon (SVG inline)
  var icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  icon.setAttribute('width', '16');
  icon.setAttribute('height', '16');
  icon.setAttribute('viewBox', '0 0 24 24');
  icon.setAttribute('fill', 'none');
  icon.innerHTML = '<path d="M12 2L3 7v6c0 5.25 3.75 10.08 9 11 5.25-.92 9-5.75 9-11V7l-9-5z" fill="' + colors.ok + '" opacity=".15"/><path d="M12 2L3 7v6c0 5.25 3.75 10.08 9 11 5.25-.92 9-5.75 9-11V7l-9-5zM12 4l7 4v5c0 4.2-2.8 8.1-7 9-4.2-.9-7-4.8-7-9V8l7-4z" fill="' + colors.ok + '"/><path d="M10 15.5l-3-3 1.5-1.5L10 12.5l5.5-5.5L17 8.5l-7 7z" fill="' + colors.ok + '"/>';

  var textSpan = document.createElement('span');
  textSpan.style.cssText = 'display:flex;align-items:center;gap:4px;';

  if (HIDE_LINK) {
    textSpan.textContent = '✓ EUComply';
  } else {
    var link = document.createElement('a');
    link.href = ORIGIN + '/?ref=badge';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = '✓ Scanned by EUComply';
    link.style.cssText = 'color:' + colors.accent + ';text-decoration:none;font-weight:600;';
    link.onmouseover = function () { link.style.textDecoration = 'underline'; };
    link.onmouseout = function () { link.style.textDecoration = 'none'; };
    textSpan.appendChild(link);
  }

  container.appendChild(icon);
  container.appendChild(textSpan);
  document.body.appendChild(container);

  // Animate in
  requestAnimationFrame(function () {
    container.style.opacity = '1';
    container.style.transform = 'translateX(0)';
  });
})();