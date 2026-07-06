# 06 Twikoo 前端更新指南

Twikoo 负责评论系统。本框架保留了原站点的 Twikoo 环境 ID（`envId`），并支持在后台修改前端 CDN 版本。

---

## 当前配置（示例）

在 `content/site.yml` 中：

```yaml
twikoo:
  enable: true
  env_id: https://twikoo.zichenccc.cn/.netlify/functions/twikoo
  cdn: https://lib.baomitu.com/twikoo/1.6.8/twikoo.all.min.js
```

这意味着当前使用：

- Twikoo 评论服务地址：`https://twikoo.zichenccc.cn/.netlify/functions/twikoo`
- 前端 JS 版本：`1.6.8`，通过 360 静态资源 CDN（baomitu）加载

---

## 什么时候需要更新

- Twikoo 官方发布新版本，想升级功能或修复 bug。
- 想换 CDN（比如 baomitu 无法访问，换 jsdelivr 或 unpkg）。
- 想换评论服务地址（比如自建 Twikoo 服务器）。

---

## 更新方法

### 方法 A：在后台修改（推荐，最方便）

1. 打开 `https://class4.zichenccc.cn/admin/`。
2. 左侧菜单 → **站点设置**。
3. 找到 **Twikoo 评论** 区域。
4. 修改 **envId** 或 **CDN**。
5. 点击 **保存设置（自动重建+推送）**。
6. 清理 EdgeOne 缓存（如有），刷新站点文章页查看。

### 方法 B：直接修改 site.yml（适合批量/代码提交）

1. 在服务器上编辑 `content/site.yml`：

   ```bash
   cd /opt/classmemorial
   nano content/site.yml
   ```

2. 找到 `twikoo:` 部分，修改 `cdn:` 或 `env_id:`。

3. 保存后，手动触发重建：

   ```bash
   docker compose exec backend python -c "from app.rebuild import rebuild_site; print(rebuild_site())"
   ```

   或者进入后台 → 同步 → 仅重建站点。

---

## 如何选择 CDN 版本

Twikoo 官方文档：https://twikoo.js.org/

常用 CDN 地址格式：

```
https://cdn.jsdelivr.net/npm/twikoo@1.6.8/dist/twikoo.all.min.js
https://unpkg.com/twikoo@1.6.8/dist/twikoo.all.min.js
https://lib.baomitu.com/twikoo/1.6.8/twikoo.all.min.js
```

如果国内访问慢，优先用 **baomitu**；如果 baomitu 没有最新版本，用 **jsdelivr**。

把版本号换成你想要的，例如 `1.6.9`：

```yaml
cdn: https://lib.baomitu.com/twikoo/1.6.9/twikoo.all.min.js
```

> 注意：版本号不能乱填，必须是 Twikoo 官方发布的版本，否则 CDN 404。

---

## 如何验证更新成功

1. 打开任意文章页。
2. 按 F12 → Network → 搜索 `twikoo`。
3. 确认加载的 JS 路径是你填的版本。
4. 评论框正常显示，说明 OK。

---

## 常见问题

### 评论不显示

- 检查 `env_id` 是否还能访问（浏览器打开 `env_id` 看有没有 Twikoo 首页）。
- 检查 CDN 是否 404（Network 面板看红色请求）。
- 检查站点设置里是否关闭了 Twikoo 启用开关。

### 升级后评论区样式崩了

- 可能是跨版本 CSS 变化。尝试把 `cdn` 改回原来的版本，再慢慢测。
- 或者联系 Twikoo 作者查看迁移说明。

### 想迁移评论数据

Twikoo 的评论数据存在你原来的 `env_id` 后端里。如果只是换前端 CDN，评论数据不变。如果换 `env_id`，需要在新后端重新导入数据。Twikoo 官方提供导出/导入工具，请查阅 Twikoo 文档。

---

## 提示

- 更新 CDN 版本不会丢失评论数据。
- 如果你看到" Powered by Twikoo v1.6.8 "，说明当前版本就是 1.6.8。
- 不要随意修改 `env_id`，除非你确定新的后端里有相同的评论数据。
