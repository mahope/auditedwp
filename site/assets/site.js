/* EUComply shell: mobile menu. No dependencies, no tracking. */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var header = document.querySelector('.sh');
  var btn = header && header.querySelector('.sh-toggle');
  var menu = document.getElementById('sh-menu');
  if (!header || !btn || !menu) return;

  function isOpen() { return btn.getAttribute('aria-expanded') === 'true'; }
  function setOpen(open) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    header.classList.toggle('is-open', open);
  }

  btn.addEventListener('click', function () { setOpen(!isOpen()); });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen()) { setOpen(false); btn.focus(); }
  });

  document.addEventListener('click', function (e) {
    if (isOpen() && !header.contains(e.target)) setOpen(false);
  });

  var mq = window.matchMedia('(min-width: 761px)');
  var onChange = function (m) { if (m.matches) setOpen(false); };
  if (mq.addEventListener) mq.addEventListener('change', onChange);
  else if (mq.addListener) mq.addListener(onChange);
})();
