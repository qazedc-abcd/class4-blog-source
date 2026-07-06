"""Runtime configuration. All values come from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


@dataclass
class Settings:
    # --- paths (set by Dockerfile, overridable for local dev) ---
    content_dir: Path = Path(_env("CONTENT_DIR", "./content"))
    data_dir: Path = Path(_env("DATA_DIR", "./data"))
    site_dir: Path = Path(_env("SITE_DIR", "./data/site"))
    frontend_dir: Path = Path(_env("FRONTEND_DIR", "./frontend"))

    # --- site identity ---
    site_title: str = _env("SITE_TITLE", "班级纪念站")

    # --- admin auth ---
    # Either set ADMIN_PASSWORD_HASH (recommended) or ADMIN_PASSWORD (plain, dev only).
    admin_password_hash: str = _env("ADMIN_PASSWORD_HASH", "")
    admin_password: str = _env("ADMIN_PASSWORD", "changeme")
    jwt_secret: str = _env("JWT_SECRET", "please-change-this-secret")
    jwt_ttl_hours: int = int(_env("JWT_TTL_HOURS", "168"))  # 7 days

    # --- GitHub two-way sync ---
    github_repo: str = _env("GITHUB_REPO", "")          # e.g. qazedc-abcd/class4-blog-source
    github_branch: str = _env("GITHUB_BRANCH", "main")
    github_token: str = _env("GITHUB_TOKEN", "")        # PAT with repo scope, for push
    github_webhook_secret: str = _env("GITHUB_WEBHOOK_SECRET", "")
    git_author_name: str = _env("GIT_AUTHOR_NAME", "ClassMemorial Bot")
    git_author_email: str = _env("GIT_AUTHOR_EMAIL", "bot@classmemorial.local")
    sync_enabled: bool = _env("SYNC_ENABLED", "true").lower() == "true"

    # --- Cloudflare R2 (S3-compatible) image storage ---
    r2_account_id: str = _env("R2_ACCOUNT_ID", "")
    r2_access_key: str = _env("R2_ACCESS_KEY", "")
    r2_secret_key: str = _env("R2_SECRET_KEY", "")
    r2_bucket: str = _env("R2_BUCKET", "")
    # Public base URL that maps to the bucket, e.g. https://drive.zichenccc.cn/raw
    r2_public_base: str = _env("R2_PUBLIC_BASE", "").rstrip("/")

    # --- rebuild concurrency guard ---
    rebuild_lockfile: Path = Path(_env("REBUILD_LOCKFILE", "/tmp/classmemorial-rebuild.lock"))

    @property
    def posts_dir(self) -> Path:
        return self.content_dir / "posts"

    @property
    def pages_dir(self) -> Path:
        return self.content_dir / "pages"

    @property
    def gallery_dir(self) -> Path:
        return self.content_dir / "gallery"

    @property
    def site_yml_path(self) -> Path:
        return self.content_dir / "site.yml"

    @property
    def gallery_manifest_path(self) -> Path:
        return self.gallery_dir / "manifest.yml"

    @property
    def r2_configured(self) -> bool:
        return all([self.r2_account_id, self.r2_access_key, self.r2_secret_key, self.r2_bucket])

    @property
    def github_configured(self) -> bool:
        return bool(self.github_repo and self.github_token)


settings = Settings()
