/* Twikoo init. Reads env_id from window.SITE (rendered by the backend from site.yml).
   To update Twikoo version or env_id, edit content/site.yml and rebuild — see docs/06-Twikoo更新.md */
(function () {
  'use strict';
  function init() {
    if (!window.SITE || !window.SITE.twikoo || !window.SITE.twikoo.env_id) return;
    if (typeof twikoo === 'undefined') {
      // CDN may have failed; retry once after 800ms
      setTimeout(init, 800);
      return;
    }
    try {
      twikoo.init({
        envId: window.SITE.twikoo.env_id,
        el: '#twikoo',
        lang: 'zh-CN',
        region: 'cn-shanghai'
      });
    } catch (e) {
      console.warn('[twikoo] init failed:', e);
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
