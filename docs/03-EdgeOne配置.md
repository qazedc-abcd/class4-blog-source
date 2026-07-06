# 03 EdgeOne 接入配置

EdgeOne 是腾讯云的边缘加速/CDN 产品。它能让：

- 海外流量走 EdgeOne 节点回源，提高国内访问速度；
- 提供 SSL 证书，实现 HTTPS；
- 提供 DDoS/CC 基础防护；
- 缓存静态资源，降低服务器压力。

---

## 前提

已经完成 [02-部署指南](02-部署指南.md)，即：

- 服务器上 Docker 在跑，nginx 监听 80 端口；
- 域名 `class4.zichenccc.cn` 已解析到服务器 IP；
- 直接访问 `http://class4.zichenccc.cn/` 能看到站点。

---

## 1. 在 EdgeOne 添加站点

1. 登录 [腾讯云 EdgeOne 控制台](https://console.cloud.tencent.com/edgeone)。
2. 点击 **添加站点**。
3. 输入域名：`class4.zichenccc.cn`。
4. 选择接入方式：
   - 如果只是加速，不修改 DNS：选 **CNAME 接入**。
   - 如果想全面接管 DNS：选 **NS 接入**。

> 推荐 **CNAME 接入**，因为你可能还有其他子域名（如 astrbot 所在的域名）不想被 EdgeOne 接管。

5. 按提示完成验证。EdgeOne 会给你分配一个 CNAME 地址。

---

## 2. 修改 DNS 记录

在你的域名 DNS 管理（如 DNSPod）里：

| 修改前 | 修改后 |
|---|---|
| A 记录 `class4` → 服务器 IP | CNAME 记录 `class4` → EdgeOne 分配的 CNAME 地址 |

保存后等待生效（通常 5–15 分钟，TTL 越低越快）。

---

## 3. 配置回源

在 EdgeOne 控制台 → 站点详情 → **回源配置**：

- 回源协议：选择 **HTTP**（服务器本地 nginx 监听 80，EdgeOne 和服务器之间用 HTTP 即可，证书由 EdgeOne 提供）。
- 回源地址：填你的服务器公网 IP。
- 回源 Host：填 `class4.zichenccc.cn`。
- 回源端口：80。
- 负载均衡：如有多台服务器可添加，只有一台就填一个。

> 注意：服务器防火墙需要允许 EdgeOne 的回源 IP 段访问 80 端口。EdgeOne 回源 IP 可在控制台文档里找到，通常腾讯云服务器默认放行腾讯云内网/边缘节点。如果不放心，可以临时放行 0.0.0.0/0:80，等测试完再收紧。

---

## 4. 开启 HTTPS

EdgeOne → **域名管理** → 点击你的域名 → **HTTPS 配置**：

1. 开启 HTTPS。
2. 证书来源：选择 **EdgeOne 托管证书** 或 **腾讯云 SSL 证书**。
3. 如果没有证书，可申请一个免费的 **TrustAsia** 证书。
4. 强制 HTTPS（可选）：把 HTTP 自动 301 跳转到 HTTPS。

保存后，访问 `https://class4.zichenccc.cn/` 应该就能正常打开。

---

## 5. 缓存配置

EdgeOne → **规则引擎** 或 **缓存配置**：

- 静态资源（`*.css`, `*.js`, `*.png`, `*.jpg`, `*.svg`）：缓存 7 天。
- 首页和文章页（`/`、`/p/*`、`/archives/`、`/gallery/`）：缓存 5 分钟或 1 小时，按你的更新频率。

> 提示：每次后台发布文章后，EdgeOne 可能还缓存着旧页面。可以在 EdgeOne 控制台点击 **刷新缓存** 进行手动刷新，或在规则里缩短 HTML 缓存时间。

---

## 6. 配置 Webhook 白名单（重要）

GitHub Webhook 会 POST 到 `https://class4.zichenccc.cn/api/webhook/github`。

EdgeOne 的 WAF 可能把 GitHub 的请求误判为攻击。需要在 EdgeOne 里：

1. **放行 `/api/webhook/github` 路径**：在规则引擎里添加一条规则，URL 路径为 `/api/webhook/github` 时跳过 CC 防护。
2. 或者设置 **IP 白名单**：GitHub Webhook 的 IP 段比较广，不太适合白名单；更推荐路径放行。

如果不放行，可能会出现"后台编辑后 GitHub 更新了，但服务器没拉取"的情况。

---

## 7. 验证

1. 访问 `https://class4.zichenccc.cn/`，看证书是否有效。
2. 访问 `https://class4.zichenccc.cn/admin/`，登录后台，发表一篇文章。
3. 等待 1 分钟，看站点是否更新。

---

## 为什么回源用 HTTP 而不是 HTTPS？

EdgeOne 到用户是 HTTPS（证书在 EdgeOne 上），EdgeOne 到服务器是 HTTP。

这样服务器不需要维护证书，省心。服务器内部 Docker 网络是可信的，HTTP 即可。

如果你坚持服务器也用 HTTPS，需要在 1Panel 或 nginx 里配置证书，并把 EdgeOne 回源协议改为 HTTPS。

---

## 下一步

[04-GitHub同步配置](04-GitHub同步配置.md)
