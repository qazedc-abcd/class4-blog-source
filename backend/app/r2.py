"""Cloudflare R2 image upload via S3-compatible API.

R2 is fully S3-compatible. We use boto3 with a custom endpoint:
    https://<account_id>.r2.cloudflarestorage.com

Images are stored under a `classmemorial/<year-month>/` prefix and served via
the configured public base URL (e.g. a custom domain bound to the bucket).
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from .config import settings


def _client():
    if not settings.r2_configured:
        raise RuntimeError("R2 is not configured. Set R2_ACCOUNT_ID/R2_ACCESS_KEY/R2_SECRET_KEY/R2_BUCKET in .env")
    import boto3
    from botocore.client import Config
    endpoint = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
        region_name="auto",
        config=Config(s3={"addressing_style": "path"}),
    )


def upload_image(filename: str, data: bytes, *, content_type: str = "image/jpeg",
                 prefix: str = "classmemorial") -> dict:
    """Upload bytes to R2 and return {key, url, public_url}."""
    client = _client()
    ts = datetime.utcnow().strftime("%Y%m")
    safe_name = f"{int(time.time() * 1000)}-{filename}"
    # Avoid path separators / non-ascii issues in key
    key = f"{prefix}/{ts}/{safe_name}"
    client.put_object(Bucket=settings.r2_bucket, Key=key, Body=data, ContentType=content_type)
    public_url = f"{settings.r2_public_base}/{key}" if settings.r2_public_base else None
    return {"key": key, "url": public_url or f"r2://{settings.r2_bucket}/{key}", "public_url": public_url}


def delete_image(key: str) -> bool:
    if not settings.r2_configured:
        return False
    client = _client()
    client.delete_object(Bucket=settings.r2_bucket, Key=key)
    return True


def guess_content_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith(".gif"):
        return "image/gif"
    if name.endswith(".svg"):
        return "image/svg+xml"
    return "image/jpeg"
