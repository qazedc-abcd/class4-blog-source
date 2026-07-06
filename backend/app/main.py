"""ClassMemorial backend — FastAPI entrypoint.

Public, read-only JSON feeds live under /api/public/*.
Admin (auth-required) endpoints live under /api/*.
GitHub webhook lives at /api/webhook/github.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from .config import settings
from . import auth, posts as posts_mod, gallery as gallery_mod, r2, sync, site as site_mod, rebuild


app = FastAPI(title="ClassMemorial API", version="1.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ----------------------------- models -----------------------------

class LoginIn(BaseModel):
    password: str

class PostIn(BaseModel):
    title: str
    body: str = ""
    categories: Optional[list] = []
    tags: Optional[list] = []
    date: Optional[str] = None
    sticky: int = 0
    cover: str = ""

class PageIn(BaseModel):
    title: str
    body: str = ""
    permalink: str = ""

class PhotoIn(BaseModel):
    url: str
    title: str = ""
    desc: str = ""
    group: str = ""
    r2key: str = ""
    thumb: str = ""

class PhotoUpdate(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    group: Optional[str] = None

class SiteConfigIn(BaseModel):
    config: dict


# ----------------------------- auth dep -----------------------------

def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    token = authorization.split(" ", 1)[1]
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(401, "invalid or expired token")
    return payload


# ----------------------------- startup -----------------------------

@app.on_event("startup")
async def _startup():
    # Ensure content dirs exist with defaults if this is a fresh deploy
    for d in (settings.content_dir, settings.posts_dir, settings.pages_dir,
              settings.gallery_dir, settings.data_dir, settings.site_dir):
        d.mkdir(parents=True, exist_ok=True)
    if not settings.site_yml_path.exists():
        site_mod.save_site_config(site_mod.DEFAULT_SITE_CONFIG)
    if not settings.gallery_manifest_path.exists():
        settings.gallery_manifest_path.write_text("[]", encoding="utf-8")
    # Init/pull the GitHub repo in the background (best-effort)
    try:
        sync.ensure_repo()
    except Exception as e:
        print(f"[startup] sync.ensure_repo warning: {e}")
    # First build so the site is served immediately
    try:
        rebuild.rebuild_site()
    except Exception as e:
        print(f"[startup] initial rebuild warning: {e}")


# ----------------------------- auth routes -----------------------------

@app.post("/api/login")
def login(body: LoginIn):
    if not auth.verify_password(body.password):
        raise HTTPException(401, "密码错误")
    return {"token": auth.create_token(), "expires_in": settings.jwt_ttl_hours * 3600}


@app.get("/api/me")
def me(_=Depends(require_auth)):
    return {"ok": True, "subject": "admin"}


# ----------------------------- public (read-only) -----------------------------

@app.get("/api/public/site")
def public_site():
    cfg = site_mod.load_site_config()
    # Only expose what the frontend needs
    return {
        "title": cfg["title"], "subtitle": cfg.get("subtitle", ""),
        "twikoo": cfg.get("twikoo", {}),
        "agreement": cfg.get("agreement", {}),
        "nav": cfg.get("nav", []),
        "gallery_enabled": cfg.get("gallery", {}).get("enable", True),
    }


@app.get("/api/public/posts")
def public_posts():
    return [{"slug": p["slug"], "title": p["title"],
             "date": p["date"].strftime("%Y-%m-%d") if hasattr(p["date"], "strftime") else str(p["date"]),
             "categories": p.get("categories_list", p.get("categories")),
             "excerpt": p.get("excerpt", "")} for p in posts_mod.list_posts()]


# ----------------------------- posts (admin) -----------------------------

@app.get("/api/posts")
def api_list_posts(_=Depends(require_auth)):
    out = []
    for p in posts_mod.list_posts():
        out.append({
            "slug": p["slug"], "title": p["title"],
            "date": p["date"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(p["date"], "strftime") else str(p["date"]),
            "categories": _as_list(p.get("categories")), "tags": _as_list(p.get("tags")),
            "sticky": p.get("sticky", 0), "cover": p.get("cover", ""),
            "excerpt": p.get("excerpt", ""),
        })
    return out


@app.get("/api/posts/{slug}")
def api_get_post(slug: str, _=Depends(require_auth)):
    p = posts_mod.get_post(slug)
    if not p:
        raise HTTPException(404, "post not found")
    return {
        "slug": p["slug"], "title": p["title"],
        "date": p["date"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(p["date"], "strftime") else str(p["date"]),
        "categories": _as_list(p.get("categories")), "tags": _as_list(p.get("tags")),
        "sticky": p.get("sticky", 0), "cover": p.get("cover", ""),
        "body": p.get("body", ""),
    }


@app.post("/api/posts/{slug}")
def api_save_post(slug: str, body: PostIn, _=Depends(require_auth)):
    is_new = not (settings.posts_dir / f"{slug}.md").exists()
    result = posts_mod.save_post(slug, body.title, body.body, categories=body.categories,
                                 tags=body.tags, date=body.date, sticky=body.sticky,
                                 cover=body.cover, is_new=is_new)
    rebuild.rebuild_and_push(f"update post: {body.title}")
    return {"ok": True, **result}


@app.put("/api/posts/{slug}")
def api_rename_post(slug: str, new_slug: str = "", _=Depends(require_auth)):
    # simple rename
    if new_slug and new_slug != slug:
        src = settings.posts_dir / f"{slug}.md"
        dst = settings.posts_dir / f"{new_slug}.md"
        if src.exists():
            src.rename(dst)
            rebuild.rebuild_and_push(f"rename post {slug} -> {new_slug}")
    return {"ok": True}


@app.delete("/api/posts/{slug}")
def api_delete_post(slug: str, _=Depends(require_auth)):
    ok = posts_mod.delete_post(slug)
    if not ok:
        raise HTTPException(404, "post not found")
    rebuild.rebuild_and_push(f"delete post: {slug}")
    return {"ok": True}


# ----------------------------- pages (admin) -----------------------------

@app.get("/api/pages")
def api_list_pages(_=Depends(require_auth)):
    return posts_mod.list_pages()


@app.get("/api/pages/{slug}")
def api_get_page(slug: str, _=Depends(require_auth)):
    p = posts_mod.get_page(slug)
    if not p:
        raise HTTPException(404, "page not found")
    return {"slug": p["slug"], "title": p.get("title", p["slug"]),
            "permalink": p.get("permalink", ""), "body": p.get("body", "")}


@app.post("/api/pages/{slug}")
def api_save_page(slug: str, body: PageIn, _=Depends(require_auth)):
    result = posts_mod.save_page(slug, body.title, body.body, permalink=body.permalink)
    rebuild.rebuild_and_push(f"update page: {body.title}")
    return {"ok": True, **result}


# ----------------------------- gallery (admin) -----------------------------

@app.get("/api/gallery")
def api_gallery(_=Depends(require_auth)):
    return {"photos": gallery_mod.list_photos(), "groups": gallery_mod.groups()}


@app.post("/api/gallery")
def api_add_photo(body: PhotoIn, _=Depends(require_auth)):
    item = gallery_mod.add_photo(body.url, title=body.title, desc=body.desc,
                                 group=body.group, r2key=body.r2key, thumb=body.thumb)
    rebuild.rebuild_and_push("add gallery photo")
    return {"ok": True, "photo": item}


@app.put("/api/gallery/{photo_id}")
def api_update_photo(photo_id: str, body: PhotoUpdate, _=Depends(require_auth)):
    item = gallery_mod.update_photo(photo_id, title=body.title, desc=body.desc, group=body.group)
    if not item:
        raise HTTPException(404, "photo not found")
    rebuild.rebuild_and_push("update gallery photo")
    return {"ok": True, "photo": item}


@app.delete("/api/gallery/{photo_id}")
def api_delete_photo(photo_id: str, _=Depends(require_auth)):
    ok = gallery_mod.delete_photo(photo_id)
    if not ok:
        raise HTTPException(404, "photo not found")
    rebuild.rebuild_and_push("delete gallery photo")
    return {"ok": True}


# ----------------------------- R2 upload -----------------------------

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...), _=Depends(require_auth)):
    if not settings.r2_configured:
        raise HTTPException(500, "R2 未配置，请在 .env 中设置 R2_* 变量")
    data = await file.read()
    ctype = r2.guess_content_type(file.filename or "image.jpg")
    try:
        result = r2.upload_image(file.filename or "image.jpg", data, content_type=ctype)
    except Exception as e:
        raise HTTPException(500, f"R2 上传失败: {e}")
    return {"ok": True, **result, "content_type": ctype, "size": len(data)}


@app.post("/api/upload/gallery")
async def api_upload_gallery(file: UploadFile = File(...),
                             title: str = Form(""), desc: str = Form(""),
                             group: str = Form(""), _=Depends(require_auth)):
    """One-shot: upload to R2 AND register in the gallery manifest."""
    if not settings.r2_configured:
        raise HTTPException(500, "R2 未配置")
    data = await file.read()
    ctype = r2.guess_content_type(file.filename or "image.jpg")
    try:
        up = r2.upload_image(file.filename or "image.jpg", data, content_type=ctype)
    except Exception as e:
        raise HTTPException(500, f"R2 上传失败: {e}")
    item = gallery_mod.add_photo(up["url"], title=title, desc=desc, group=group,
                                 r2key=up.get("key", ""))
    rebuild.rebuild_and_push("upload gallery photo")
    return {"ok": True, "upload": up, "photo": item}


# ----------------------------- site config (admin) -----------------------------

@app.get("/api/site")
def api_get_site(_=Depends(require_auth)):
    return site_mod.load_site_config()


@app.put("/api/site")
def api_put_site(body: SiteConfigIn, _=Depends(require_auth)):
    cfg = site_mod.save_site_config(body.config)
    rebuild.rebuild_and_push("update site config")
    return {"ok": True, "config": cfg}


# ----------------------------- sync + rebuild -----------------------------

@app.get("/api/sync/status")
def api_sync_status(_=Depends(require_auth)):
    return sync.status()


@app.post("/api/sync/push")
def api_sync_push(_=Depends(require_auth)):
    return sync.push_changes("manual push from admin")


@app.post("/api/sync/pull")
def api_sync_pull(_=Depends(require_auth)):
    result = sync.pull_changes()
    if result.get("changed"):
        rebuild.rebuild_site()
    return result


@app.post("/api/rebuild")
def api_rebuild(_=Depends(require_auth)):
    return rebuild.rebuild_site()


# ----------------------------- GitHub webhook (no auth, signed) -----------------------------

@app.post("/api/webhook/github")
async def github_webhook(request: Request,
                         x_hub_signature_256: Optional[str] = Header(None),
                         x_github_event: Optional[str] = Header(None)):
    payload = await request.body()
    if not sync.verify_webhook_signature(payload, x_hub_signature_256 or ""):
        raise HTTPException(401, "invalid signature")
    if x_github_event != "push":
        return {"ignored": True, "event": x_github_event}
    result = sync.pull_changes()
    if result.get("changed"):
        rb = rebuild.rebuild_site()
        result["rebuild"] = rb
    return {"ok": True, **result}


@app.get("/api/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat(), "version": "1.0.0"}


def _as_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]
