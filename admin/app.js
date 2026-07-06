/* ClassMemorial admin SPA — vanilla JS, no framework.
   Token persisted in localStorage. All mutations call the backend API which
   rebuilds the site + pushes to GitHub automatically. */
(function () {
  'use strict';
  var TOKEN_KEY = 'cm_admin_token';
  var app = document.getElementById('app');

  // ---------- api ----------
  function token() { return localStorage.getItem(TOKEN_KEY) || ''; }
  function authed() { return !!token(); }
  function logout() { localStorage.removeItem(TOKEN_KEY); location.hash = '#/login'; render(); }

  async function api(path, opts) {
    opts = opts || {};
    var headers = { 'Content-Type': 'application/json' };
    if (authed()) headers['Authorization'] = 'Bearer ' + token();
    opts.headers = Object.assign({}, headers, opts.headers || {});
    var r = await fetch('/api' + path, opts);
    if (r.status === 401) { logout(); throw new Error('未登录'); }
    var data = r.status === 204 ? null : await r.json().catch(function () { return null; });
    if (!r.ok) throw new Error((data && data.detail) || ('HTTP ' + r.status));
    return data;
  }
  async function apiUpload(path, formData) {
    var headers = {};
    if (authed()) headers['Authorization'] = 'Bearer ' + token();
    var r = await fetch('/api' + path, { method: 'POST', headers: headers, body: formData });
    if (r.status === 401) { logout(); throw new Error('未登录'); }
    var data = await r.json().catch(function () { return null; });
    if (!r.ok) throw new Error((data && data.detail) || ('HTTP ' + r.status));
    return data;
  }

  function toast(msg, isErr) {
    var t = document.createElement('div');
    t.className = 'toast' + (isErr ? ' err' : '');
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add('show'); }, 10);
    setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 250); }, 2200);
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  // ---------- router ----------
  function render() {
    var hash = location.hash.slice(1) || '/login';
    if (!authed() && hash !== '/login') { location.hash = '/login'; return render(); }
    if (hash === '/login') { return viewLogin(); }
    if (hash === '/logout') { logout(); return; }
    viewShell(hash);
  }
  window.addEventListener('hashchange', render);

  // ---------- login ----------
  function viewLogin() {
    app.innerHTML = '';
    app.appendChild(document.getElementById('tpl-login').content.cloneNode(true));
    document.getElementById('loginForm').addEventListener('submit', async function (e) {
      e.preventDefault();
      var pw = this.password.value;
      try {
        var d = await api('/login', { method: 'POST', body: JSON.stringify({ password: pw }) });
        localStorage.setItem(TOKEN_KEY, d.token);
        location.hash = '#/dashboard';
      } catch (err) {
        document.getElementById('loginErr').textContent = '登录失败：' + err.message;
      }
    });
  }

  // ---------- shell ----------
  function viewShell(hash) {
    if (!app.querySelector('.sidebar')) {
      app.innerHTML = '';
      app.appendChild(document.getElementById('tpl-shell').content.cloneNode(true));
      document.getElementById('menuFab').addEventListener('click', function () {
        document.querySelector('.sidebar').classList.toggle('open');
      });
    }
    var route = (hash.split('/')[1] || 'dashboard');
    var sub = hash.split('/').slice(2).join('/');
    document.querySelectorAll('.sidebar nav a').forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-route') === route);
    });
    var view = document.getElementById('view');
    document.querySelector('.sidebar').classList.remove('open');
    var map = { dashboard: viewDashboard, posts: viewPosts, pages: viewPages, gallery: viewGallery, settings: viewSettings, sync: viewSync };
    (map[route] || viewDashboard)(view, sub);
  }

  // ---------- dashboard ----------
  async function viewDashboard(el) {
    el.innerHTML = '<h1>仪表盘</h1><p class="muted">加载中…</p>';
    try {
      var posts = await api('/posts');
      var status = await api('/sync/status').catch(function () { return { enabled: false }; });
      el.innerHTML = '<div class="page-head"><h1>仪表盘</h1><a class="btn btn-primary" href="#/posts/new">写新文章</a></div>' +
        '<div class="metrics">' +
          '<div class="metric"><div class="num">' + posts.length + '</div><div class="lbl">文章数</div></div>' +
          '<div class="metric"><div class="num">' + (status.enabled ? '已启用' : '未启用') + '</div><div class="lbl">GitHub 同步</div></div>' +
          '<div class="metric"><div class="num">' + (status.head || '—') + '</div><div class="lbl">最新提交</div></div>' +
        '</div>' +
        '<div class="card"><h3>快速操作</h3>' +
          '<p><a class="btn" href="#/posts">管理文章</a> &nbsp; <a class="btn" href="#/gallery">上传图片到图库</a> &nbsp; ' +
          '<a class="btn" href="#/settings">站点设置</a> &nbsp; <a class="btn" href="#/sync">同步状态</a></p>' +
        '</div>' +
        '<div class="card"><h3>说明</h3><p class="muted">所有改动会自动：① 重建静态站点 ② 推送到 GitHub 备份。无需手动操作。</p></div>';
    } catch (e) { el.innerHTML = '<h1>仪表盘</h1><p class="muted">加载失败：' + esc(e.message) + '</p>'; }
  }

  // ---------- posts ----------
  async function viewPosts(el, sub) {
    if (sub === 'new' || sub === 'edit') return viewPostEdit(el, sub === 'new' ? '' : sub);
    el.innerHTML = '<div class="page-head"><h1>文章</h1><a class="btn btn-primary" href="#/posts/new">+ 新建</a></div><div class="card"><p class="muted">加载中…</p></div>';
    try {
      var posts = await api('/posts');
      var rows = posts.map(function (p) {
        return '<li><span class="title">' + esc(p.title) + (p.sticky ? ' <span class="tag">置顶</span>' : '') + '</span>' +
          '<span class="meta">' + esc(p.date) + '</span>' +
          '<a class="btn btn-sm" href="#/posts/edit/' + encodeURIComponent(p.slug) + '">编辑</a>' +
          '<button class="btn btn-sm btn-danger" data-del="' + esc(p.slug) + '">删除</button></li>';
      }).join('');
      el.querySelector('.card').innerHTML = '<ul class="row-list">' + (rows || '<li class="muted">还没有文章</li>') + '</ul>';
      el.querySelectorAll('[data-del]').forEach(function (b) {
        b.addEventListener('click', async function () {
          if (!confirm('确认删除这篇文章？')) return;
          try { await api('/posts/' + encodeURIComponent(b.dataset.del), { method: 'DELETE' }); toast('已删除'); viewPosts(el, ''); }
          catch (e) { toast(e.message, true); }
        });
      });
    } catch (e) { el.querySelector('.card').innerHTML = '<p class="muted">加载失败：' + esc(e.message) + '</p>'; }
  }

  async function viewPostEdit(el, slug) {
    var isNew = !slug;
    el.innerHTML = '<div class="page-head"><h1>' + (isNew ? '新建文章' : '编辑文章') + '</h1>' +
      '<button class="btn" id="backBtn">返回</button></div>' +
      '<div class="card"><div class="field"><label>标题</label><input id="title" placeholder="文章标题"></div>' +
      '<div class="grid2"><div class="field"><label>分类（逗号分隔）</label><input id="cats" placeholder="梗, 同学"></div>' +
      '<div class="field"><label>标签（逗号分隔）</label><input id="tags" placeholder="杂项"></div></div>' +
      '<div class="grid2"><div class="field"><label>发布时间</label><input id="date" type="text" placeholder="2026-01-17 23:32:00"></div>' +
      '<div class="field"><label>置顶权重（0=不置顶，数字越大越靠前）</label><input id="sticky" type="number" value="0"></div></div>' +
      '<div class="field"><label>封面图（可选，填 R2 直链）</label><input id="cover" placeholder="https://..."></div>' +
      '<div class="field"><label>正文（Markdown）<button class="btn btn-sm" id="upImg" style="float:right">插入 R2 图片</button></label>' +
      '<div class="editor-split"><textarea id="body" placeholder="# 标题&#10;&#10;正文…"></textarea><div class="preview" id="preview"></div></div></div>' +
      '<div style="margin-top:14px"><button class="btn btn-primary" id="save">保存并发布</button> <span class="muted" id="saving"></span></div></div>';
    document.getElementById('backBtn').addEventListener('click', function () { location.hash = '#/posts'; });

    var titleEl = document.getElementById('title'), bodyEl = document.getElementById('body'), prevEl = document.getElementById('preview');
    function preview() { try { prevEl.innerHTML = marked.parse(bodyEl.value); } catch (e) { prevEl.innerHTML = '<p class="muted">预览不可用</p>'; } }
    bodyEl.addEventListener('input', preview);

    document.getElementById('upImg').addEventListener('click', function () {
      var inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
      inp.addEventListener('change', async function () {
        var f = inp.files[0]; if (!f) return;
        var fd = new FormData(); fd.append('file', f);
        document.getElementById('saving').textContent = '上传图片中…';
        try {
          var d = await apiUpload('/upload', fd);
          var md = '![' + esc(f.name) + '](' + d.url + ')';
          bodyEl.value = bodyEl.value + '\n' + md + '\n'; preview();
          toast('图片已插入');
        } catch (e) { toast(e.message, true); }
        document.getElementById('saving').textContent = '';
      });
      inp.click();
    });

    if (!isNew) {
      try {
        var p = await api('/posts/' + encodeURIComponent(slug));
        titleEl.value = p.title; bodyEl.value = p.body; document.getElementById('cats').value = (p.categories || []).join(', ');
        document.getElementById('tags').value = (p.tags || []).join(', '); document.getElementById('date').value = p.date;
        document.getElementById('sticky').value = p.sticky || 0; document.getElementById('cover').value = p.cover || '';
        preview();
      } catch (e) { toast('加载失败：' + e.message, true); }
    } else {
      document.getElementById('date').value = new Date().toISOString().slice(0, 19).replace('T', ' ');
      preview();
    }

    document.getElementById('save').addEventListener('click', async function () {
      var title = titleEl.value.trim(); if (!title) { toast('请填标题', true); return; }
      var slugVal = slug || title.replace(/[\\/:*?\"<>|!\?,。.;:;'\"()【】《》「」『』、·\s]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') || 'post';
      var body = {
        title: title, body: bodyEl.value,
        categories: document.getElementById('cats').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean),
        tags: document.getElementById('tags').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean),
        date: document.getElementById('date').value || null,
        sticky: parseInt(document.getElementById('sticky').value) || 0,
        cover: document.getElementById('cover').value.trim()
      };
      document.getElementById('saving').textContent = '保存中（重建+推送 GitHub）…';
      try {
        await api('/posts/' + encodeURIComponent(slugVal), { method: 'POST', body: JSON.stringify(body) });
        toast('已保存并发布'); location.hash = '#/posts';
      } catch (e) { toast(e.message, true); }
      document.getElementById('saving').textContent = '';
    });
  }

  // ---------- pages ----------
  async function viewPages(el, sub) {
    if (sub === 'edit') return viewPageEdit(el, sub === 'new' ? '' : (location.hash.split('/edit/')[1] || ''));
    el.innerHTML = '<div class="page-head"><h1>单页</h1></div><div class="card"><p class="muted">加载中…</p></div>';
    try {
      var pages = await api('/pages');
      var rows = pages.map(function (p) {
        return '<li><span class="title">' + esc(p.title) + '</span><span class="meta">/' + esc(p.slug) + '/</span>' +
          '<a class="btn btn-sm" href="#/pages/edit/' + encodeURIComponent(p.slug) + '">编辑</a></li>';
      }).join('');
      el.querySelector('.card').innerHTML = '<p class="muted">系统页面（用户协议、免责声明、关于等）在这里编辑。permalink 在每页 frontmatter 里设置。</p><ul class="row-list">' + (rows || '<li class="muted">无</li>') + '</ul>';
    } catch (e) { el.querySelector('.card').innerHTML = '<p class="muted">加载失败：' + esc(e.message) + '</p>'; }
  }
  async function viewPageEdit(el, slug) {
    slug = decodeURIComponent(slug || '');
    el.innerHTML = '<div class="page-head"><h1>编辑页面：' + esc(slug) + '</h1><button class="btn" id="backBtn">返回</button></div>' +
      '<div class="card"><div class="field"><label>标题</label><input id="title"></div>' +
      '<div class="field"><label>permalink（如 /用户协议/）</label><input id="permalink"></div>' +
      '<div class="field"><label>正文（Markdown）</label><textarea id="body" style="min-height:420px"></textarea></div>' +
      '<button class="btn btn-primary" id="save">保存</button> <span class="muted" id="saving"></span></div>';
    document.getElementById('backBtn').addEventListener('click', function () { location.hash = '#/pages'; });
    try {
      var p = await api('/pages/' + encodeURIComponent(slug));
      document.getElementById('title').value = p.title; document.getElementById('permalink').value = p.permalink || ''; document.getElementById('body').value = p.body;
    } catch (e) { toast('加载失败：' + e.message, true); }
    document.getElementById('save').addEventListener('click', async function () {
      var body = { title: document.getElementById('title').value, permalink: document.getElementById('permalink').value, body: document.getElementById('body').value };
      document.getElementById('saving').textContent = '保存中…';
      try { await api('/pages/' + encodeURIComponent(slug), { method: 'POST', body: JSON.stringify(body) }); toast('已保存'); location.hash = '#/pages'; }
      catch (e) { toast(e.message, true); }
      document.getElementById('saving').textContent = '';
    });
  }

  // ---------- gallery ----------
  async function viewGallery(el) {
    el.innerHTML = '<div class="page-head"><h1>图库</h1></div>' +
      '<div class="card"><div class="upload-zone" id="drop">点击或拖拽图片上传到 R2 + 图库</div>' +
      '<div class="grid2" style="margin-top:14px"><input id="gtitle" placeholder="标题（可选）"><input id="ggroup" placeholder="分组（如 高一、运动会）"></div>' +
      '<input id="gdesc" placeholder="描述（可选）" style="width:100%;margin-top:8px;padding:10px;border:1px solid var(--c-border);border-radius:8px"></div>' +
      '<div class="card"><p class="muted">加载中…</p></div>';
    var drop = document.getElementById('drop');
    async function uploadFiles(files) {
      var title = document.getElementById('gtitle').value, group = document.getElementById('ggroup').value, desc = document.getElementById('gdesc').value;
      for (var i = 0; i < files.length; i++) {
        var fd = new FormData(); fd.append('file', files[i]); fd.append('title', title); fd.append('group', group); fd.append('desc', desc);
        toast('上传中 ' + (i + 1) + '/' + files.length);
        try { await apiUpload('/upload/gallery', fd); } catch (e) { toast(e.message, true); }
      }
      toast('上传完成'); viewGallery(el);
    }
    drop.addEventListener('click', function () { var i = document.createElement('input'); i.type = 'file'; i.multiple = true; i.accept = 'image/*'; i.addEventListener('change', function () { uploadFiles(i.files); }); i.click(); });
    drop.addEventListener('dragover', function (e) { e.preventDefault(); drop.classList.add('has-drag'); });
    drop.addEventListener('dragleave', function () { drop.classList.remove('has-drag'); });
    drop.addEventListener('drop', function (e) { e.preventDefault(); drop.classList.remove('has-drag'); uploadFiles(e.dataTransfer.files); });

    try {
      var d = await api('/gallery');
      var card = el.querySelectorAll('.card')[1];
      if (!d.photos.length) { card.innerHTML = '<p class="muted">图库为空，上传第一张吧。</p>'; return; }
      var groups = {}; d.photos.forEach(function (p) { var g = p.group || '未分组'; (groups[g] = groups[g] || []).push(p); });
      card.innerHTML = Object.keys(groups).map(function (g) {
        return '<h3 style="margin:4px 0 10px">' + esc(g) + '</h3><div class="gal-grid">' + groups[g].map(function (p) {
          return '<div class="gal-thumb"><img src="' + esc(p.thumb || p.url) + '" loading="lazy"><button class="del" data-del="' + esc(p.id) + '">×</button></div>';
        }).join('') + '</div>';
      }).join('');
      card.querySelectorAll('[data-del]').forEach(function (b) {
        b.addEventListener('click', async function () {
          if (!confirm('删除这张照片？（仅从图库移除，R2 文件保留）')) return;
          try { await api('/gallery/' + encodeURIComponent(b.dataset.del), { method: 'DELETE' }); toast('已删除'); viewGallery(el); }
          catch (e) { toast(e.message, true); }
        });
      });
    } catch (e) { el.querySelectorAll('.card')[1].innerHTML = '<p class="muted">加载失败：' + esc(e.message) + '</p>'; }
  }

  // ---------- settings ----------
  async function viewSettings(el) {
    el.innerHTML = '<div class="page-head"><h1>站点设置</h1></div><div class="card"><p class="muted">加载中…</p></div>';
    try {
      var cfg = await api('/site');
      var b = cfg.beian || {}, t = cfg.twikoo || {}, a = cfg.agreement || {};
      el.querySelector('.card').innerHTML =
        '<div class="field"><label>站点标题</label><input id="s_title" value="' + esc(cfg.title) + '"></div>' +
        '<div class="field"><label>副标题</label><input id="s_sub" value="' + esc(cfg.subtitle) + '"></div>' +
        '<div class="grid2"><div class="field"><label>作者</label><input id="s_author" value="' + esc(cfg.author) + '"></div>' +
        '<div class="field"><label>邮箱</label><input id="s_email" value="' + esc(cfg.email) + '"></div></div>' +
        '<div class="grid2"><div class="field"><label>起始年份</label><input id="s_year" type="number" value="' + esc(cfg.start_year) + '"></div>' +
        '<div class="field"><label>许可证</label><input id="s_lic" value="' + esc(cfg.license) + '"></div></div>' +
        '<h3 style="margin:22px 0 10px">首页横幅大合照</h3>' +
        '<div class="field"><label><span class="switch"><input type="checkbox" id="h_on" ' + (cfg.hero && cfg.hero.enable ? 'checked' : '') + '><span></span></span> 显示首页横幅</label></div>' +
        '<div class="field"><label>横幅图片 R2 直链</label><input id="h_img" value="' + esc((cfg.hero && cfg.hero.image) || '') + '" placeholder="https://drive.zichenccc.cn/raw/..."></div>' +
        '<div class="grid2"><div class="field"><label>标题</label><input id="h_title" value="' + esc((cfg.hero && cfg.hero.title) || '') + '"></div>' +
        '<div class="field"><label>副标题</label><input id="h_sub" value="' + esc((cfg.hero && cfg.hero.subtitle) || '') + '"></div></div>' +
        '<div class="grid2"><div class="field"><label>黑色蒙版透明度（0-1）</label><input id="h_mask" value="' + esc((cfg.hero && cfg.hero.mask_alpha) || 0.35) + '"></div>' +
        '<div class="field"><label>高度占屏幕比例（0-100）</label><input id="h_h" type="number" value="' + esc((cfg.hero && cfg.hero.height) || 70) + '"></div></div>' +
        '<h3 style="margin:22px 0 10px">备案信息（各自可开关）</h3>' +
        '<div class="field"><label><span class="switch"><input type="checkbox" id="icp_on" ' + (b.icp && b.icp.enable ? 'checked' : '') + '><span></span></span> ICP 备案显示</label>' +
          '<input id="icp_text" value="' + esc(b.icp ? b.icp.text : '') + '" placeholder="鄂ICP备XXXXXXXX号"></div>' +
        '<div class="field"><label><span class="switch"><input type="checkbox" id="police_on" ' + (b.police && b.police.enable ? 'checked' : '') + '><span></span></span> 公安备案显示</label>' +
          '<input id="police_text" value="' + esc(b.police ? b.police.text : '') + '" placeholder="鄂公安网备XXXXXXXX号">' +
          '<input id="police_code" value="' + esc(b.police ? b.police.code : '') + '" placeholder="公安备案号纯数字" style="margin-top:8px"></div>' +
        '<h3 style="margin:18px 0 8px">Twikoo 评论</h3>' +
        '<div class="field"><label><span class="switch"><input type="checkbox" id="tw_on" ' + (t.enable ? 'checked' : '') + '><span></span></span> 启用评论</label></div>' +
        '<div class="field"><label>Twikoo envId</label><input id="tw_env" value="' + esc(t.env_id) + '"></div>' +
        '<div class="field"><label>Twikoo CDN</label><input id="tw_cdn" value="' + esc(t.cdn) + '"></div>' +
        '<h3 style="margin:18px 0 8px">协议弹窗</h3>' +
        '<div class="field"><label><span class="switch"><input type="checkbox" id="ag_on" ' + (a.enable ? 'checked' : '') + '><span></span></span> 启用首次访问协议弹窗</label></div>' +
        '<div class="grid2"><div class="field"><label>倒计时秒数</label><input id="ag_cd" type="number" value="' + esc(a.countdown_seconds) + '"></div>' +
        '<div class="field"><label>localStorage key</label><input id="ag_key" value="' + esc(a.storage_key) + '"></div></div>' +
        '<button class="btn btn-primary" id="save" style="margin-top:8px">保存设置（自动重建+推送）</button> <span class="muted" id="saving"></span>';
      document.getElementById('save').addEventListener('click', async function () {
        cfg.title = val('s_title'); cfg.subtitle = val('s_sub'); cfg.author = val('s_author'); cfg.email = val('s_email');
        cfg.start_year = parseInt(val('s_year')) || 2025; cfg.license = val('s_lic');
        cfg.hero = { enable: checked('h_on'), image: val('h_img'), title: val('h_title'), subtitle: val('h_sub'),
                     mask_alpha: parseFloat(val('h_mask')) || 0.35, height: parseInt(val('h_h')) || 70 };
        cfg.beian = {
          icp: { enable: checked('icp_on'), text: val('icp_text'), url: 'https://beian.miit.gov.cn/' },
          police: { enable: checked('police_on'), text: val('police_text'), code: val('police_code'),
                    url: 'http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=' + val('police_code') }
        };
        cfg.twikoo = { enable: checked('tw_on'), env_id: val('tw_env'), cdn: val('tw_cdn') };
        cfg.agreement = { enable: checked('ag_on'), countdown_seconds: parseInt(val('ag_cd')) || 7, storage_key: val('ag_key'), pages: cfg.agreement.pages };
        document.getElementById('saving').textContent = '保存中…';
        try { await api('/site', { method: 'PUT', body: JSON.stringify({ config: cfg }) }); toast('已保存并生效'); }
        catch (e) { toast(e.message, true); }
        document.getElementById('saving').textContent = '';
      });
    } catch (e) { el.querySelector('.card').innerHTML = '<p class="muted">加载失败：' + esc(e.message) + '</p>'; }
  }
  function val(id) { return document.getElementById(id).value; }
  function checked(id) { return document.getElementById(id).checked; }

  // ---------- sync ----------
  async function viewSync(el) {
    el.innerHTML = '<div class="page-head"><h1>GitHub 同步</h1></div><div class="card"><p class="muted">加载中…</p></div>';
    async function refresh() {
      try {
        var s = await api('/sync/status');
        var card = el.querySelector('.card');
        if (!s.enabled) { card.innerHTML = '<p class="muted">同步未启用。在 .env 设置 SYNC_ENABLED=true 与 GITHUB_REPO/GITHUB_TOKEN 开启。</p>'; return; }
        card.innerHTML =
          '<p>仓库：<code>' + esc(s.repo) + '</code> · 分支：<code>' + esc(s.branch) + '</code></p>' +
          '<p>最新提交：<code>' + esc(s.head || '—') + '</code></p>' +
          '<p>最近：<span class="muted">' + esc(s.last_log || '—') + '</span></p>' +
          '<p>工作区状态：' + (s.dirty ? '<span style="color:var(--c-red)">有未提交改动</span>' : '<span style="color:var(--c-green)">干净</span>') + '</p>' +
          '<div style="margin-top:14px">' +
            '<button class="btn btn-primary" id="push">立即推送</button> ' +
            '<button class="btn" id="pull">从 GitHub 拉取</button> ' +
            '<button class="btn" id="rebuild">仅重建站点</button></div>' +
          '<p class="muted" id="out" style="margin-top:12px"></p>';
        document.getElementById('push').addEventListener('click', async function () { out('推送中…'); try { var d = await api('/sync/push', { method: 'POST' }); out(JSON.stringify(d)); toast('推送完成'); } catch (e) { out(e.message, true); } });
        document.getElementById('pull').addEventListener('click', async function () { out('拉取中…'); try { var d = await api('/sync/pull', { method: 'POST' }); out(JSON.stringify(d)); toast('拉取完成'); } catch (e) { out(e.message, true); } });
        document.getElementById('rebuild').addEventListener('click', async function () { out('重建中…'); try { var d = await api('/rebuild', { method: 'POST' }); out(JSON.stringify(d)); toast('重建完成'); } catch (e) { out(e.message, true); } });
      } catch (e) { el.querySelector('.card').innerHTML = '<p class="muted">加载失败：' + esc(e.message) + '</p>'; }
    }
    function out(msg, err) { var o = document.getElementById('out'); if (o) o.textContent = msg; if (err) toast(msg, true); }
    refresh();
  }

  // boot
  render();
})();
