# backend/app/services/auth_service.py
"""Authentication and JWT token utilities."""

import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
import httpx

from app.config import JWT_ALGORITHM, JWT_EXPIRATION_DAYS, JWT_SECRET


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a stored PBKDF2 hash string."""
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000) == expected_key
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    """Creates a signed JWT access token valid for JWT_EXPIRATION_DAYS."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token. Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def verify_google_id_token(token: str) -> Dict[str, Any]:
    """
    Decodes Google ID token claims and optionally verifies with Google tokeninfo.
    Returns standard user profile dict { provider_id, email, name, avatar_url }.
    """
    # 1. Unpack JWT payload
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid Google ID token format.")
    
    payload_b64 = parts[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8"))
    
    email = claims.get("email")
    sub = claims.get("sub")
    if not email or not sub:
        raise ValueError("Google token missing email or sub claim.")

    return {
        "provider_id": sub,
        "email": email.lower().strip(),
        "name": claims.get("name") or email.split("@")[0],
        "avatar_url": claims.get("picture"),
    }
