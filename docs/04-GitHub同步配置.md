# 04 GitHub 同步配置

本文教你把 GitHub 仓库和服务器"绑定"起来，实现**一次修改，两段更新**。

---

## 核心逻辑

```
GitHub 仓库 = 备份仓库 + 公开源
服务器     = 运行现场
```

- 你在后台改文章 → 服务器把改动 commit & push 到 GitHub。
- 你在 GitHub 改文章 → GitHub 发通知给服务器 → 服务器 pull 并重建。

---

## 1. 准备 GitHub 仓库

如果你继续使用原来的仓库 `qazedc-abcd/class4-blog-source`：

1. 建议把原仓库的 Hexo 代码**切到一个备份分支**，例如 `legacy-hexo`。
2. 把新框架内容推送到 `main` 分支。

如果你新建仓库：

1. 在 GitHub 创建空仓库，例如 `qazedc-abcd/class4-blog-source-new`。
2. 把 `.env` 里的 `GITHUB_REPO` 改成新仓库名。

---

## 2. 生成 Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**。
2. 点击 **Generate new token (classic)**。
3. 勾选 **`repo`** 权限。
4. 点击 Generate，复制生成的 token（以 `ghp_` 开头）。

> 这个 token 只保存在服务器 `.env` 里，不要公开。

把 token 填到 `.env`：

```env
GITHUB_TOKEN=ghp_xxxxxxxx
```

---

## 3. 设置 Webhook

1. 打开 GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**。
2. Payload URL：

   ```
   https://class4.zichenccc.cn/api/webhook/github
   ```

   如果还没配 EdgeOne，可以先用 `http://<服务器IP>/api/webhook/github` 测试。

3. Content type：选 `application/json`。
4. Secret：填一个随机字符串，然后把这个字符串填到 `.env`：

   ```env
   GITHUB_WEBHOOK_SECRET=你刚填的随机字符串
   ```

5. 触发事件：只选 **Just the push event**。
6. 点击 **Add webhook**。

> 注意：EdgeOne 的 WAF 可能拦截 GitHub 请求，请按 [03-EdgeOne配置](03-EdgeOne配置.md) 里说明放行 `/api/webhook/github`。

---

## 4. 配置 Git 提交信息（可选）

`.env` 里可以改：

```env
GIT_AUTHOR_NAME=ClassMemorial Bot
GIT_AUTHOR_EMAIL=bot@classmemorial.local
```

这是每次后台改内容时 GitHub 提交记录里显示的作者。

---

## 5. 测试同步

### 测试 A：后台改 → GitHub 更新

1. 登录 `https://class4.zichenccc.cn/admin/`。
2. 进入 **文章** → **新建**，写一篇文章，保存。
3. 打开 GitHub 仓库，看 `main` 分支是否有新提交。

### 测试 B：GitHub 改 → 服务器更新

1. 在 GitHub 仓库里直接编辑 `content/posts/某文章.md`。
2. 提交。
3. 等待 10–30 秒，刷新站点，看内容是否更新。

如果更新了，说明双向同步成功。

---

## 6. 常见问题

### 后台保存后 GitHub 没更新

- 看 `.env` 里 `GITHUB_TOKEN` 是否填对，是否有 `repo` 权限。
- 看 `docker compose logs backend` 是否有报错。
- 看 `GITHUB_REPO` 是否写错，格式是 `用户名/仓库名`，不含 `https://github.com/`。

### GitHub 改了服务器没更新

- 看 EdgeOne 是否拦截了 `/api/webhook/github`。
- 看 `.env` 里 `GITHUB_WEBHOOK_SECRET` 和 GitHub 设置的是否一致。
- 在 GitHub Webhook 页面查看 Recent Deliveries，看返回状态码是不是 200。

### 出现冲突

如果服务器和 GitHub 同时改了同一个文件，backend 会先尝试 `pull --rebase` 再 `push`。

如果自动解决不了，可以：

1. SSH 进入服务器容器：

   ```bash
   docker compose exec backend sh
   cd /app/content
   git status
   git pull origin main --rebase
   git push origin main
   ```

2. 或者暂时手动在 GitHub 仓库里把内容统一，然后点后台 **同步 → 拉取**。

---

## 下一步

[05-后台使用](05-后台使用.md)
