# Hexo 协议弹窗插件维护与使用教程

本文档用于 **长期维护与交接**，适用于：

* Hexo 博客
* 任意主题（Fluid / NexT / Butterfly 等）
* 当前已部署的「协议弹窗 + 独立 hash 校验」方案

---

## 一、插件功能概述

该插件用于在用户首次访问或协议内容更新后：

* 强制弹出《免责声明》《用户协议》
* 要求用户阅读 ≥5 秒后才能勾选同意
* 用户同意后记录到浏览器 localStorage
* **任意一份协议内容变更 → 自动要求用户重新同意**

该方案：

* 无后端依赖
* 不依赖主题
* 只需维护 Markdown 协议正文

---

## 二、目录结构说明（非常重要）

```text
hexo-blog/
├─ scripts/
│  └─ agreement-plugin.js        # Hexo 注入插件（一般无需改）
│
├─ source/
│  ├─ agreement/
│  │  ├─ agreement.css          # 弹窗样式
│  │  ├─ agreement.js           # 核心逻辑（hash / 倒计时）
│  │  └─ agreement.html         # 弹窗 HTML 模板
│  │
│  ├─ 免责声明.md                # 协议正文（Markdown）
│  └─ 用户协议.md                # 协议正文（Markdown）
```

维护时 **90% 的操作只涉及最后两个 Markdown 文件**。

---

## 三、日常维护指南（最常用）

### 1️⃣ 修改协议内容（最常见）

**操作步骤：**

1. 打开以下任意文件：

   * `source/免责声明.md`
   * `source/用户协议.md`
2. 正常修改 Markdown 内容（增删条款、调整措辞）
3. 保存文件
4. 重新生成站点：

```bash
hexo clean
hexo g
hexo d   # 或 hexo s 本地测试
```

**结果：**

* 所有用户下次访问时
* 浏览器会检测到 hash 变化
* **强制重新弹出协议确认框**

> ⚠️ 无需手动清缓存、无需改 JS

---

### 2️⃣ 仅修改样式 / 文案（不触发重弹）

以下修改 **不会** 触发用户重新同意：

* 修改 `agreement.css`
* 修改 `agreement.html` 中的提示文字
* 修改倒计时秒数（如 5 → 10）

原因：

> hash 只计算 **协议正文内容**，不包含 UI

---

## 四、协议页面规范（必须遵守）

### 1️⃣ 协议页面必须可访问

每个协议 Markdown **必须设置固定 permalink**：

```yaml
---
title: 免责声明
permalink: /免责声明/
---
```

```yaml
---
title: 用户协议
permalink: /用户协议/
---
```

否则弹窗无法正确加载内容。

---

### 2️⃣ 不要对协议页面做以下操作

❌ 页面加密 / 密码访问
❌ 仅登录可见
❌ JS 动态渲染正文

否则 `fetch()` 会失败。

---

## 五、协议更新后的标准操作流程（可交接）

> **推荐直接复制给运营 / 管理员**

### ✅ 协议更新 SOP

1. 打开对应协议 Markdown
2. 修改内容
3. 保存
4. 执行：

```bash
hexo clean
hexo g
hexo d
```

5. 发布完成

📌 **不需要通知用户、不需要额外操作**

---

## 六、测试与排错指南

### 1️⃣ 本地测试重弹是否生效

1. 浏览器打开 DevTools
2. Application → Local Storage
3. 删除 `HEXO_SITE_AGREEMENT`
4. 刷新页面 → 必须弹窗

---

### 2️⃣ 常见问题

#### ❓ 弹窗不出现

* 是否已同意过
* localStorage 是否未清空
* 是否使用无痕模式测试

---

#### ❓ 协议内容显示为空

* permalink 是否正确
* 协议页面是否能直接访问
* 是否被主题插件拦截

---

## 七、升级与扩展建议（可选）

### 可安全升级的方向

* 使用 SHA-256（WebCrypto）替代简单 hash
* 记录同意时间戳
* 增加协议版本号展示

### 不建议做的事

* 强制禁用浏览器返回
* 禁用开发者工具
* 过度反爬 / 反用户操作

---

## 八、交接说明（写给未来维护者）

* **不要删除 scripts/agreement-plugin.js**
* **不要随意修改 agreement.js 的 hash 逻辑**
* 协议维护只改 Markdown
* UI 调整只改 CSS / HTML

---

## 九、一句话总结

> **这是一个“内容驱动”的协议系统：**
>
> * 内容变 → 用户重同意
> * 内容不变 → 用户无感知
>
> 维护成本极低，合规风险可控。







# Class4 博客 CMS 维护文档

## 系统架构

```
┌─────────────────────────────────────────┐
│  博客访问: https://class4.zichenccc.cn   │
│  CMS管理: https://class4.zichenccc.cn/cms │
└─────────────────────────────────────────┘
           ↓
    Cloudflare Pages (自动构建)
           ↓
    GitHub 仓库: qazedc-abcd/class4-blog-source
           ↓
    OAuth认证: https://oauth.zichenccc.cn (Worker)
           ↓
    文章编辑 → 自动部署
```

---

## 日常使用

### 发布/编辑文章

1. 访问 `https://class4.zichenccc.cn/cms/`
2. 点击 **Login with GitHub** 登录
3. 左侧选择 **博客文章**
4. 点击 **New 博客文章** 创建，或点击现有文章编辑
5. 编辑完成后点击右上角 **Publish** 发布
6. 等待 1-2 分钟，博客自动更新

### 上传图片

- 在文章编辑界面，点击 **封面图** 或内容中的图片按钮
- 选择本地图片上传
- 图片自动保存到 `source/images/uploads/`

---

## 故障排查

| 问题           | 解决方案                                        |
| -------------- | ----------------------------------------------- |
| 无法登录 CMS   | 清除浏览器缓存，或换无痕模式重试                |
| 登录后显示空白 | 检查网络，刷新页面                              |
| 保存文章失败   | 检查 GitHub 仓库是否可访问                      |
| 博客未更新     | 等待 2-3 分钟，或手动触发 Cloudflare Pages 重建 |
| 图片上传失败   | 检查 `source/images/uploads/` 目录是否存在      |

---

## 关键组件维护

### 1. OAuth Worker (oauth.zichenccc.cn)

**位置**: Cloudflare Worker `blog-oauth`

**文件**: `C:\Users\admin\Desktop\blog-oauth\index.js`

**重启/更新**:
```powershell
cd C:\Users\admin\Desktop\blog-oauth
wrangler deploy
```

**查看日志**:
```powershell
wrangler tail blog-oauth
```

**环境变量** (Secrets):
- `GITHUB_CLIENT_ID`: GitHub OAuth App ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth App Secret

---

### 2. GitHub OAuth App

**位置**: https://github.com/settings/developers

**配置**:
- Homepage URL: `https://class4.zichenccc.cn`
- Authorization callback URL: `https://oauth.zichenccc.cn/callback`

**如需重置**:
1. 点击 **Reset client secret**
2. 复制新的 Secret
3. 更新 Worker: `wrangler secret put GITHUB_CLIENT_SECRET`

---

### 3. Cloudflare Pages (博客)

**项目名称**: `class4-blog`

**构建设置**:
- Build command: `npm install && npm install hexo-cli -g && hexo clean && hexo generate`
- Build output: `public`

**手动重建**:
- Dashboard → Workers & Pages → class4-blog → Deployments → Retry deployment

---

### 4. CMS 文件位置

```
source/
├── _posts/          # 博客文章
├── images/uploads/  # 图片上传目录
└── cms/             # CMS 管理界面
    ├── index.html   # CMS 入口
    └── config.yml   # CMS 配置
```

---

## 备份与恢复

### 备份博客源文件

```powershell
cd C:\users\admin\my-blog
git pull  # 确保最新
# 整个文件夹就是备份
```

### 恢复

```powershell
git clone https://github.com/qazedc-abcd/class4-blog-source.git
cd class4-blog-source
npm install
```

---

## 添加协作者（多人使用）

1. **GitHub 仓库添加协作者**:
   - https://github.com/qazedc-abcd/class4-blog-source/settings/access
   - Invite a collaborator → 输入对方 GitHub 用户名

2. **对方使用流程**:
   - 访问 `https://class4.zichenccc.cn/cms/`
   - 用自己的 GitHub 账号登录
   - 即可编辑文章

---

## 紧急联系

- **GitHub 仓库**: https://github.com/qazedc-abcd/class4-blog-source
- **Cloudflare Dashboard**: https://dash.cloudflare.com
- **Netlify** (如使用): https://app.netlify.com

---

## 更新记录

| 日期       | 更新内容                         |
| ---------- | -------------------------------- |
| 2026-02-14 | 初始部署，OAuth + Decap CMS 方案 |
|            | 修复跨域认证问题                 |
|            | 完成 CMS 与博客整合              |

---

**文档版本**: 1.0  
**最后更新**: 2026-02-14