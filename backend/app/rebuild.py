"""Rebuild orchestration: rebuild static site, with a lockfile guard so
concurrent edits don't trigger overlapping builds."""
from __future__ import annotations

import os
import time
from pathlib import Path

from .config import settings
from . import builder


def rebuild_site() -> dict:
    """Rebuild the static site. Returns {ok, pages, seconds}."""
    lock = settings.rebuild_lockfile
    if lock.exists():
        # stale lock if older than 120s
        try:
            age = time.time() - lock.stat().st_mtime
            if age < 120:
                return {"ok": False, "reason": "another build in progress", "age_s": int(age)}
        except Exception:
            pass
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()), encoding="utf-8")
    t0 = time.time()
    try:
        pages = builder.build_site()
        return {"ok": True, "pages": pages, "seconds": round(time.time() - t0, 2)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            lock.unlink()
        except Exception:
            pass


def rebuild_and_push(message: str = "update site") -> dict:
    """Rebuild, then push content to GitHub. Used after admin edits."""
    result = rebuild_site()
    push_result = None
    try:
        from . import sync
        push_result = sync.push_changes(message)
    except Exception as e:
        push_result = {"synced": False, "error": str(e)}
    return {"rebuild": result, "sync": push_result}
