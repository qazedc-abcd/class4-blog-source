"""Static site builder: reads Markdown content + Jinja2 templates → site/ HTML.

This runs inside the backend container (no separate build service needed),
which keeps the Docker footprint tiny. Called by rebuild.rebuild_site().
"""
from __future__ import annotations

import html as html_lib
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import settings
from . import posts as posts_mod
from . import gallery as gallery_mod
from .site import load_site_config


def _md() -> markdown.Markdown:
    # extra/fenced_code/sane_lists = standard; pymdownx.tilde = ~~删除线~~;
    # pymdownx.caret = ^^下划线^^; pymdownx.mark = ==高亮==; pymdownx.magiclink = 自动链接
    return markdown.Markdown(
        extensions=["extra", "codehilite", "toc", "sane_lists", "admonition",
                    "pymdownx.tilde", "pymdownx.caret", "pymdownx.mark",
                    "pymdownx.magiclink", "pymdownx.tasklist", "pymdownx.emoji"],
        extension_configs={
            "codehilite": {"guess_lang": False, "noclasses": True},
            "pymdownx.tasklist": {"custom_checkbox": True},
            "pymdownx.magiclink": {"repo_url_shortener": False},
            # smart_delete=False so ~~strikethrough~~ works adjacent to CJK chars;
            # subscript=False → only ~~ (GFM strikethrough) is honored, single ~ stays literal
            "pymdownx.tilde": {"smart_delete": False, "subscript": False},
        })


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(settings.frontend_dir / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    env.filters["rfc3339"] = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S+08:00") if hasattr(d, "strftime") else str(d)
    env.filters["datefmt"] = lambda d: d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    env.filters["datetimefmt"] = lambda d: d.strftime("%Y-%m-%d %H:%M") if hasattr(d, "strftime") else str(d)
    return env


def build_site() -> int:
    """Render the whole site into settings.site_dir. Returns number of pages written."""
    site = settings.site_dir
    site.mkdir(parents=True, exist_ok=True)
    # Clean previous output (keep the dir itself)
    for child in site.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    cfg = load_site_config()
    env = _env()
    md = _md()

    # 1. Copy static assets (css/js/img) → /static
    static_src = settings.frontend_dir / "static"
    static_dst = site / "static"
    if static_src.exists():
        shutil.copytree(static_src, static_dst)

    # 2. Home page (post list, sticky first)
    post_list = posts_mod.list_posts()
    for p in post_list:
        p["date_str"] = p["date"].strftime("%Y-%m-%d") if hasattr(p["date"], "strftime") else str(p["date"])
        p["categories_list"] = _as_list(p.get("categories"))
        p["tags_list"] = _as_list(p.get("tags"))
    home = env.get_template("index.html").render(
        site=cfg, posts=post_list, section="home", page_title=cfg["title"],
        hero=cfg.get("hero", {}))
    _write(site / "index.html", home)

    # 3. Post detail pages → /p/<slug>/index.html  (clean short URLs)
    # Also emit /<year>/<month>/<day>/<title>/ for back-compat with the old Hexo site.
    for p in post_list:
        md.reset()
        raw_body = p.get("body", "") if "body" in p else (posts_mod.get_post(p["slug"]) or {}).get("body", "")
        body_html = md.convert(_strip_more(raw_body))
        ctx = dict(site=cfg, post=p, content=body_html, section="post",
                   page_title=f"{p['title']} - {cfg['title']}")
        out = env.get_template("post.html").render(**ctx)
        slug_dir = site / "p" / p["slug"]
        _write(slug_dir / "index.html", out)
        # Back-compat permalink (only for posts that have a date)
        if hasattr(p["date"], "strftime"):
            legacy_dir = site / f"{p['date'].year:04d}" / f"{p['date'].month:02d}" / f"{p['date'].day:02d}" / p["slug"]
            _write(legacy_dir / "index.html", out)

    # 4. Archive page
    arch = env.get_template("archive.html").render(
        site=cfg, posts=post_list, section="archive", page_title=f"归档 - {cfg['title']}")
    _write(site / "archives" / "index.html", arch)

    # 5. Gallery page
    if cfg.get("gallery", {}).get("enable", True):
        photos = gallery_mod.list_photos()
        gal = env.get_template("gallery.html").render(
            site=cfg, photos=photos, groups=gallery_mod.groups(), section="gallery",
            page_title=f"{cfg.get('gallery',{}).get('title','图库')} - {cfg['title']}")
        _write(site / "gallery" / "index.html", gal)

    # 6. Standalone pages (用户协议 / 免责声明 / about)
    for pg in posts_mod.list_pages():
        full = posts_mod.get_page(pg["slug"])
        if not full:
            continue
        md.reset()
        body_html = md.convert(_strip_more(full.get("body", "")))
        permalink = full.get("permalink") or f"/{pg['slug']}/"
        ctx = dict(site=cfg, page=full, content=body_html, section="page",
                   page_title=f"{full.get('title', pg['slug'])} - {cfg['title']}")
        out = env.get_template("page.html").render(**ctx)
        # permalink may be like /用户协议/ — write to /用户协议/index.html
        rel = permalink.strip("/")
        _write(site / rel / "index.html", out)

    # 7. 404
    notfound = env.get_template("404.html").render(
        site=cfg, section="none", page_title="404 - " + cfg["title"])
    _write(site / "404.html", notfound)

    # 8. robots.txt + sitemap.xml (SEO + EdgeOne friendly)
    _write(site / "robots.txt", "User-agent: *\nAllow: /\n")
    sm_urls = ["/"] + [f"/p/{p['slug']}/" for p in post_list] + ["/archives/", "/gallery/"]
    for pg in posts_mod.list_pages():
        sm_urls.append(f"/{(pg.get('permalink') or '/'+pg['slug']+'/').strip('/')}/")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sm_urls:
        sm.append(f"  <url><loc>{_escape(u)}</loc><lastmod>{datetime.utcnow().date()}</lastmod></url>")
    sm.append("</urlset>")
    _write(site / "sitemap.xml", "\n".join(sm))

    return len(post_list) + len(posts_mod.list_pages()) + 3  # approx page count


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_MORE_RE = re.compile(r"<!--\s*more\s*-->", re.IGNORECASE)


def _strip_more(body: str) -> str:
    """Remove the Hexo-style <!-- more --> marker before rendering."""
    return _MORE_RE.sub("", body)


def _as_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _escape(s: str) -> str:
    return html_lib.escape(s, quote=True)
