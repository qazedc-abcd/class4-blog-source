/* ClassMemorial frontend runtime: nav toggle, gallery lightbox, small UX.
   No frameworks, ~2KB, works in WeChat built-in browser. */
(function () {
  'use strict';

  // ---- mobile nav toggle ----
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    // close nav when a link is tapped (mobile)
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.innerWidth < 720) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ---- gallery: tab filter + lightbox ----
  var tabs = document.querySelectorAll('#galleryTabs .tab');
  var items = document.querySelectorAll('#galleryGrid .gallery-item');
  if (tabs.length) {
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        tabs.forEach(function (x) { x.classList.remove('active'); });
        t.classList.add('active');
        var g = t.getAttribute('data-group');
        items.forEach(function (it) {
          var show = g === '全部' || it.getAttribute('data-group') === g;
          it.style.display = show ? '' : 'none';
        });
      });
    });
  }

  var lb = document.getElementById('lightbox');
  if (lb && items.length) {
    var lbImg = lb.querySelector('.lb-img');
    var lbCap = lb.querySelector('.lb-caption');
    var visible = []; var current = 0;

    function rebuildVisible() {
      visible = Array.prototype.slice.call(items).filter(function (it) {
        return it.style.display !== 'none';
      });
    }
    function show(i) {
      rebuildVisible();
      if (!visible.length) return;
      current = (i + visible.length) % visible.length;
      var it = visible[current];
      lbImg.src = it.getAttribute('data-src');
      var cap = it.querySelector('.gi-title');
      lbCap.textContent = cap ? cap.textContent : '';
      lb.classList.add('open');
      lb.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
    function close() {
      lb.classList.remove('open');
      lb.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
    items.forEach(function (it, idx) {
      it.addEventListener('click', function () { show(idx); });
    });
    lb.querySelector('.lb-close').addEventListener('click', close);
    lb.querySelector('.lb-prev').addEventListener('click', function (e) { e.stopPropagation(); show(current - 1); });
    lb.querySelector('.lb-next').addEventListener('click', function (e) { e.stopPropagation(); show(current + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    // swipe support for WeChat/mobile
    var sx = 0, sy = 0;
    lb.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - sx;
      var dy = e.changedTouches[0].clientY - sy;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
        show(current + (dx < 0 ? 1 : -1));
      } else if (Math.abs(dy) > 80 && dy > 0) {
        close();
      }
    }, { passive: true });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    });
  }
})();
