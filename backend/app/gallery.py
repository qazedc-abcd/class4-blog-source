"""Gallery management. Metadata lives in content/gallery/manifest.yml;
the image binaries live in Cloudflare R2 (referenced by URL)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from .config import settings


def _load_manifest() -> list[dict]:
    p = settings.gallery_manifest_path
    if not p.exists():
        return []
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_manifest(items: list[dict]) -> None:
    p = settings.gallery_manifest_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(items, allow_unicode=True, sort_keys=False), encoding="utf-8")


def list_photos() -> list[dict]:
    return _load_manifest()


def add_photo(url: str, *, title: str = "", desc: str = "", group: str = "",
              r2key: str = "", thumb: str = "") -> dict:
    items = _load_manifest()
    item = {
        "id": f"p{len(items) + 1:04d}-{int(datetime.utcnow().timestamp())}",
        "url": url,
        "thumb": thumb or url,
        "title": title,
        "desc": desc,
        "group": group,
        "r2key": r2key,
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    }
    items.append(item)
    _save_manifest(items)
    return item


def update_photo(photo_id: str, *, title: Optional[str] = None, desc: Optional[str] = None,
                 group: Optional[str] = None) -> Optional[dict]:
    items = _load_manifest()
    for it in items:
        if it.get("id") == photo_id:
            if title is not None:
                it["title"] = title
            if desc is not None:
                it["desc"] = desc
            if group is not None:
                it["group"] = group
            _save_manifest(items)
            return it
    return None


def delete_photo(photo_id: str) -> bool:
    items = _load_manifest()
    new_items = [it for it in items if it.get("id") != photo_id]
    if len(new_items) == len(items):
        return False
    _save_manifest(new_items)
    return True


def groups() -> list[str]:
    seen = []
    for it in _load_manifest():
        g = it.get("group") or "未分组"
        if g not in seen:
            seen.append(g)
    return seen
