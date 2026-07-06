"""GitHub two-way sync.

Path A (admin edits -> GitHub): write files, then git add/commit/push.
Path B (GitHub edits -> server): GitHub webhook fires, we git pull.

Uses system git via subprocess — no extra Python dependency, and the backend
container already has git installed.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
from typing import Optional

from .config import settings


def _git(*args: str, cwd: Optional[str] = None) -> str:
    repo = cwd or str(settings.content_dir)
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def ensure_repo() -> None:
    """Make sure /app/content is a git repo with the right remote and identity."""
    if not settings.sync_enabled or not settings.github_configured:
        return
    content = settings.content_dir
    content.mkdir(parents=True, exist_ok=True)
    if not (content / ".git").exists():
        _git("init", "-b", settings.github_branch)
        _git("config", "user.name", settings.git_author_name)
        _git("config", "user.email", settings.git_author_email)
        remote_url = f"https://x-access-token:{settings.github_token}@github.com/{settings.github_repo}.git"
        _git("remote", "add", "origin", remote_url)
        # Try to pull existing content (so we don't overwrite the GitHub backup)
        try:
            _git("pull", "origin", settings.github_branch, "--allow-unrelated-histories")
        except Exception:
            pass
    else:
        # Ensure identity is set (in case volume was re-created)
        try:
            _git("config", "user.name", settings.git_author_name)
            _git("config", "user.email", settings.git_author_email)
        except Exception:
            pass


def push_changes(message: str = "update content via ClassMemorial admin") -> dict:
    """Commit and push all changes under content/. Safe to call when nothing changed."""
    if not settings.sync_enabled:
        return {"synced": False, "reason": "sync disabled"}
    if not settings.github_configured:
        return {"synced": False, "reason": "github not configured"}
    ensure_repo()
    # .gitignore inside content excludes runtime files
    _write_gitignore()
    _git("add", "-A")
    status = _git("status", "--porcelain")
    if not status:
        return {"synced": True, "changed": False, "message": "nothing to push"}
    _git("commit", "-m", message)
    try:
        _git("push", "origin", settings.github_branch)
        return {"synced": True, "changed": True, "message": message}
    except Exception as e:
        # Push failed (maybe remote ahead) — try pull --rebase then push again
        try:
            _git("pull", "origin", settings.github_branch, "--rebase", "--allow-unrelated-histories")
            _git("push", "origin", settings.github_branch)
            return {"synced": True, "changed": True, "message": message, "rebased": True}
        except Exception:
            raise RuntimeError(f"push failed: {e}")


def pull_changes() -> dict:
    """Pull latest from GitHub (called after webhook). Returns whether changed."""
    if not settings.sync_enabled or not settings.github_configured:
        return {"pulled": False, "reason": "sync disabled / github not configured"}
    ensure_repo()
    _write_gitignore()
    try:
        before = _git("rev-parse", "HEAD")
    except Exception:
        before = ""
    _git("fetch", "origin", settings.github_branch)
    _git("reset", "--hard", f"origin/{settings.github_branch}")
    after = _git("rev-parse", "HEAD")
    return {"pulled": True, "changed": before != after, "before": before, "after": after}


def verify_webhook_signature(payload: bytes, signature_header: str) -> bool:
    """GitHub sends X-Hub-Signature-256 = 'sha256=<hex>'. Verify against shared secret."""
    if not settings.github_webhook_secret:
        return True  # no secret configured → accept (set one in production!)
    if not signature_header:
        return False
    try:
        algo, hexsig = signature_header.split("=", 1)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    expected = hmac.new(settings.github_webhook_secret.encode("utf-8"),
                        payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, hexsig)


def _write_gitignore() -> None:
    gi = settings.content_dir / ".gitignore"
    gi.write_text(
        "# runtime / non-source files\n"
        ".db/\n"
        "*.db\n"
        "*.db-journal\n"
        ".DS_Store\n",
        encoding="utf-8",
    )


def status() -> dict:
    """Return sync status for the admin dashboard."""
    if not settings.sync_enabled:
        return {"enabled": False, "configured": False}
    out = {
        "enabled": True,
        "configured": settings.github_configured,
        "repo": settings.github_repo,
        "branch": settings.github_branch,
    }
    if settings.github_configured and (settings.content_dir / ".git").exists():
        try:
            out["head"] = _git("rev-parse", "--short", "HEAD")
            out["dirty"] = bool(_git("status", "--porcelain"))
            out["last_log"] = _git("log", "-1", "--pretty=%h %s (%cr)")
        except Exception as e:
            out["error"] = str(e)
    return out
