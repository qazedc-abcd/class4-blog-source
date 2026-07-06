# ClassMemorial

一个面向**班级纪念站**的开源、自托管、低占用博客框架。

> 本项目把原本基于 Hexo + Cloudflare Pages 的「26届4班纪念站」
> 迁移到一台 2H2G 的国内服务器（已装 1Panel / Python / astrbot），
> 外层用 **EdgeOne** 加速，图片继续放 **Cloudflare R2**，
> 后台改成自研 Web 管理界面，原 GitHub 仓库继续作为**备份与公开源**。

---

## 特性

- **零 Hexo，零复杂依赖**：Python FastAPI + 静态 HTML 前端，小白也能维护。
- **Docker 化**：`docker compose up -d` 即可运行，内存占用约 200MB。
- **GitHub 双向同步**：后台改完自动推 GitHub；GitHub 上改完 webhook 自动拉回服务器。
- **R2 一键上传**：写文章、传图库时直接上传到 Cloudflare R2，拿到直链。
- **图库**：瀑布流 + 灯箱 + 分组筛选，移动端可左右滑动。
- **备案自由开关**：ICP 备案、公安备案可各自独立开启/关闭。
- **Twikoo 评论**：保留 Twikoo，前端版本和 envId 随时可改。
- **协议弹窗**：首次访问自动弹窗，协议正文变化时自动要求重新同意。
- **微信/移动端优化**：触屏友好、无 hover-only 交互、图片响应式。

---

## 目录

- [快速开始](docs/01-快速开始.md)
- [部署指南：1Panel + Docker](docs/02-部署指南.md)
- [EdgeOne 接入配置](docs/03-EdgeOne配置.md)
- [GitHub 同步配置](docs/04-GitHub同步配置.md)
- [后台使用](docs/05-后台使用.md)
- [Twikoo 前端更新指南](docs/06-Twikoo更新.md)
- [图库使用](docs/07-图库使用.md)
- [ICP/公安备案开关](docs/08-ICP公安备案.md)
- [故障排查](docs/09-故障排查.md)
- [二次开发 / 复用为其他班级站](docs/10-二次开发.md)

---

## 项目结构

```
classmemorial/
├── docker-compose.yml
├── .env.example              # 复制为 .env 后填写
├── backend/                  # FastAPI 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/                  # API + Markdown 构建器 + R2 + Git 同步
├── frontend/                 # Jinja2 模板 + 静态资源
│   ├── templates/
│   └── static/
├── admin/                    # Web 管理后台（单页应用，无构建）
│   ├── index.html
│   ├── app.js
│   └── style.css
├── nginx/                    # nginx 镜像配置
├── content/                  # 数据（会被提交到 GitHub）
│   ├── site.yml              # 站点配置
│   ├── posts/                # 文章 Markdown
│   ├── pages/                # 单页（用户协议、免责声明、关于）
│   └── gallery/manifest.yml  # 图库索引
├── docs/                     # 技术文档（就是你在看的）
└── scripts/
    ├── hash_password.py      # 生成管理员密码 hash
    └── test_build.py         # 本地测试构建
```

---

## 适合谁用

- 班级纪念站、毕业纪念站、同好小站等**内容型小站**。
- 对 Hexo 生态不再想维护、想要一个更现代化后台的站长。
- 需要在国内服务器 + 海外 CDN（R2 / EdgeOne）混合部署的场景。

---

## 快速开始（Docker）

```bash
cd classmemorial
cp .env.example .env
# 编辑 .env，设置 R2 / GitHub / 管理员密码
python scripts/hash_password.py
# 填好 .env 后：
docker compose up -d --build
```

然后打开 `http://<服务器IP>/admin` 登录，进入后台写文章/传图。

详细步骤请看 [01-快速开始.md](docs/01-快速开始.md)。

---

## 开源协议

本项目代码采用 MIT 协议。站点内容归原作者所有，请保留自己的版权/许可证设置。

