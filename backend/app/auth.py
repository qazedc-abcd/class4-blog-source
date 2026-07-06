"""Admin authentication: PBKDF2 password hashing + JWT tokens."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional

import jwt

from .config import settings


def _pbkdf2(password: str, salt: str, iterations: int = 200_000) -> str:
    raw = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return raw.hex()


def hash_password(password: str, iterations: int = 200_000) -> str:
    """Return a string suitable for ADMIN_PASSWORD_HASH: pbkdf2_sha256$iter$salt$hash"""
    salt = secrets.token_hex(16)
    return f"pbkdf2_sha256${iterations}${salt}${_pbkdf2(password, salt, iterations)}"


def verify_password(password: str) -> bool:
    """Verify against hash (preferred) or plain env password (fallback)."""
    h = settings.admin_password_hash
    if h:
        try:
            algo, iter_s, salt, digest = h.split("$")
            if algo != "pbkdf2_sha256":
                return False
            expected = _pbkdf2(password, salt, int(iter_s))
            return hmac.compare_digest(expected, digest)
        except Exception:
            return False
    # Fallback: plain password compare (constant-time)
    return hmac.compare_digest(password, settings.admin_password)


def create_token(subject: str = "admin") -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + settings.jwt_ttl_hours * 3600,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except Exception:
        return None
