/* Agreement popup — content-driven re-consent.
   Ported from the original Hexo site: fetch the rendered agreement pages,
   compute a hash of their text, store consent in localStorage. When the
   agreement content changes, the hash changes and users must re-agree. */
(function () {
  'use strict';
  if (!window.SITE || !window.SITE.agreement || !window.SITE.agreement.enable) return;

  var cfg = window.SITE.agreement;
  var KEY = cfg.storage_key || 'site_agreement_v1';
  var COUNTDOWN = cfg.countdown_seconds || 7;
  var PAGES = cfg.pages || ['用户协议', '免责声明'];
  var root = document.getElementById('agreement-root');
  if (!root) return;

  function hashText(text) {
    // FNV-1a 32-bit, stable across browsers, no crypto needed
    var h = 0x811c9dc5;
    for (var i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
    }
    return (h >>> 0).toString(16);
  }

  function extractMain(html) {
    // pull the markdown-body / post-content region; fall back to <main>
    var m = html.match(/<div class="(?:post-content|markdown-body)[^"]*">([\s\S]*?)<\/div>\s*(?:<p class="post-license"|<section|<\/article)/);
    var body = m ? m[1] : (html.match(/<main[^>]*>([\s\S]*?)<\/main>/) || ['', html])[1];
    // strip script/style, keep tags for display
    return body.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '');
  }

  function buildPopup(contentHtml, h) {
    root.innerHTML =
      '<div class="agreement-mask">' +
        '<div class="agreement-box">' +
          '<h2>使用前请阅读并同意</h2>' +
          '<div class="agreement-content">' + contentHtml + '</div>' +
          '<div class="agreement-actions">' +
            '<label><input type="checkbox" id="agree-checkbox" disabled> 我已阅读并同意（<span id="countdown">' + COUNTDOWN + '</span>s）</label>' +
            '<div class="btns"><button id="agree-btn" disabled>同意</button><button id="reject-btn">不同意</button></div>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.style.overflow = 'hidden';

    var left = COUNTDOWN;
    var timer = setInterval(function () {
      left--;
      var el = document.getElementById('countdown');
      if (el) el.textContent = left;
      if (left <= 0) {
        clearInterval(timer);
        document.getElementById('agree-checkbox').disabled = false;
        document.getElementById('agree-btn').disabled = false;
      }
    }, 1000);

    var cb = document.getElementById('agree-checkbox');
    var btn = document.getElementById('agree-btn');
    cb.addEventListener('change', function () { btn.disabled = !cb.checked; });
    btn.addEventListener('click', function () {
      if (!cb.checked) return;
      try { localStorage.setItem(KEY, 'yes:' + h); } catch (e) {}
      close();
    });
    document.getElementById('reject-btn').addEventListener('click', function () {
      // not agreed → send visitor to a safe page
      window.location.href = 'about:blank';
    });
  }

  function close() {
    root.innerHTML = '';
    root.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  // already agreed to this exact hash?
  var stored = '';
  try { stored = localStorage.getItem(KEY) || ''; } catch (e) {}

  // fetch all agreement pages, then render
  Promise.all(PAGES.map(function (name) {
    return fetch('/' + encodeURIComponent(name) + '/').then(function (r) { return r.text(); });
  })).then(function (htmls) {
    var combined = htmls.map(extractMain).join('<hr>');
    var plain = combined.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    var h = hashText(plain);
    if (stored === 'yes:' + h) return; // consent valid, no popup
    buildPopup(combined, h);
  }).catch(function () {
    // network error fetching agreements — don't block the site
  });
})();
