(function () {
  const root = document.getElementById('agreement-root');
  if (!root) {
    console.warn('[Agreement] root not found');
    return;
  }

  const AGREEMENT_KEY = 'site_agreement_v1';
  if (localStorage.getItem(AGREEMENT_KEY) === 'yes') {
    return;
  }

  // 创建遮罩 + 弹窗
  root.innerHTML = `
    <div class="agreement-mask">
      <div class="agreement-box">
        <h2>使用前请阅读并同意</h2>
        <div class="agreement-content">
          <p>正在加载协议内容...</p>
        </div>
        <div class="agreement-actions">
          <label>
            <input type="checkbox" id="agree-checkbox" disabled>
            我已阅读并同意（<span id="countdown">7</span>s）
          </label>
          <div class="btns">
            <button id="agree-btn" disabled>同意</button>
            <button id="reject-btn">不同意</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // 禁止背景滚动
  document.body.style.overflow = 'hidden';

  const contentEl = root.querySelector('.agreement-content');

  // ✅ 关键：加载「生成后的 HTML 页面」
  Promise.all([
    fetch('/用户协议/').then(r => r.text()),
    fetch('/免责声明/').then(r => r.text())
  ]).then(([uaHtml, disHtml]) => {
    contentEl.innerHTML = `
      <h3></h3>
      ${extractMain(uaHtml)}
      <hr>
      <h3></h3>
      ${extractMain(disHtml)}
    `;
  }).catch(() => {
    contentEl.innerHTML = '<p style="color:red">协议内容加载失败</p>';
  });

  // 倒计时逻辑
  let sec = 7;
  const countdownEl = root.querySelector('#countdown');
  const checkbox = root.querySelector('#agree-checkbox');
  const agreeBtn = root.querySelector('#agree-btn');

  const timer = setInterval(() => {
    sec--;
    countdownEl.textContent = sec;
    if (sec <= 0) {
      clearInterval(timer);
      checkbox.disabled = false;
    }
  }, 1000);

  checkbox.addEventListener('change', () => {
    agreeBtn.disabled = !checkbox.checked;
  });

  agreeBtn.addEventListener('click', () => {
    localStorage.setItem(AGREEMENT_KEY, 'yes');
    close();
  });

  root.querySelector('#reject-btn').addEventListener('click', () => {
    history.back();
  });

  function close() {
    root.innerHTML = '';
    document.body.style.overflow = '';
  }

  // 从完整 HTML 中提取正文（避免 footer / header 再出现）
  function extractMain(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const main = doc.querySelector('main');
    return main ? main.innerHTML : '<p>内容解析失败</p>';
  }
})();

