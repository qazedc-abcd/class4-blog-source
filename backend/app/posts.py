"""Post (Markdown) read/write with frontmatter parsing."""
from __future__ import annotations

import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import frontmatter

from .config import settings


def _to_datetime(d):
    """Normalize date or datetime or str to datetime (for safe comparison)."""
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime(d.year, d.month, d.day)
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d)
        except Exception:
            return datetime.now()
    return datetime.now()


def slugify(text: str) -> str:
    # Keep CJK characters; strip punctuation/whitespace
    text = re.sub(r"[\\/:*?\"<>|!\?,。.;:;'\"()【】《》「」『』、·\s]+", "-", text.strip())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def list_posts() -> list[dict]:
    """Return all posts sorted by date desc. Each item: meta + slug + excerpt."""
    posts = []
    if not settings.posts_dir.exists():
        return posts
    for f in sorted(settings.posts_dir.glob("*.md")):
        try:
            post = frontmatter.load(f)
        except Exception:
            continue
        meta = dict(post.metadata)
        slug = f.stem
        body = post.content
        meta.setdefault("title", slug)
        meta["date"] = _to_datetime(meta.get("date", datetime.now()))
        meta["slug"] = slug
        meta["excerpt"] = make_excerpt(body)
        meta["sticky"] = int(meta.get("sticky", 0) or 0)
        posts.append(meta)
    posts.sort(key=lambda p: (p.get("sticky", 0), p["date"]), reverse=True)
    return posts


def get_post(slug: str) -> Optional[dict]:
    path = settings.posts_dir / f"{slug}.md"
    if not path.exists():
        return None
    post = frontmatter.load(path)
    meta = dict(post.metadata)
    meta["slug"] = slug
    meta.setdefault("title", slug)
    meta["date"] = _to_datetime(meta.get("date", datetime.now()))
    meta["body"] = post.content
    return meta


def save_post(slug: str, title: str, body: str, *, categories=None, tags=None,
              date: Optional[str] = None, sticky: int = 0, cover: str = "",
              is_new: bool = False) -> dict:
    """Create or update a post. Returns the resulting metadata."""
    safe_slug = slugify(slug) if is_new else slug
    path = settings.posts_dir / f"{safe_slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    post = frontmatter.Post(body)
    post["title"] = title
    post["date"] = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if categories:
        post["categories"] = categories if isinstance(categories, list) else [categories]
    if tags:
        post["tags"] = tags if isinstance(tags, list) else [tags]
    if sticky:
        post["sticky"] = int(sticky)
    if cover:
        post["cover"] = cover

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return {"slug": safe_slug, "title": title, "path": str(path)}


def delete_post(slug: str) -> bool:
    path = settings.posts_dir / f"{slug}.md"
    if path.exists():
        path.unlink()
        return True
    return False


def make_excerpt(body: str, length: int = 120) -> str:
    # Hexo-style <!-- more -->: if present, use only the text BEFORE it as excerpt
    m = re.search(r"<!--\s*more\s*-->", body, re.IGNORECASE)
    if m:
        body = body[:m.start()]
        length = max(length, 200)  # author explicitly chose this much — keep more of it
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body)          # images
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)       # links
    text = re.sub(r"[#>*_`~\-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length] + ("…" if len(text) > length else "")


def list_pages() -> list[dict]:
    pages = []
    if not settings.pages_dir.exists():
        return pages
    for f in sorted(settings.pages_dir.glob("*.md")):
        try:
            p = frontmatter.load(f)
        except Exception:
            continue
        meta = dict(p.metadata)
        meta["slug"] = f.stem
        meta.setdefault("title", f.stem)
        pages.append(meta)
    return pages


def get_page(slug: str) -> Optional[dict]:
    path = settings.pages_dir / f"{slug}.md"
    if not path.exists():
        return None
    p = frontmatter.load(path)
    meta = dict(p.metadata)
    meta["slug"] = slug
    meta["body"] = p.content
    return meta


def save_page(slug: str, title: str, body: str, *, permalink: str = "") -> dict:
    path = settings.pages_dir / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(body)
    post["title"] = title
    if permalink:
        post["permalink"] = permalink
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return {"slug": slug, "title": title, "path": str(path)}
