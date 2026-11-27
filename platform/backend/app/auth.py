"""Supabase Auth verification.

The frontend signs users in with Supabase and sends `Authorization: Bearer <access_token>`.
We verify the token here: HS256 with SUPABASE_JWT_SECRET (legacy projects) or asymmetric keys
from the project's JWKS endpoint (projects using JWT signing keys).

With REQUIRE_AUTH=false (default for local development) unauthenticated requests are treated
as a single local user; the Settings page says so explicitly.
"""
from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Header, HTTPException

from app.config import get_settings

LOCAL_USER = {"id": "local", "email": None, "mode": "local-single-user"}


@lru_cache
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{url.rstrip('/')}/auth/v1/.well-known/jwks.json", cache_keys=True)


def verify_token(token: str) -> dict:
    s = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg == "HS256":
            if not s.supabase_jwt_secret:
                raise HTTPException(401, "HS256 token received but SUPABASE_JWT_SECRET is not configured")
            claims = jwt.decode(token, s.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        else:
            if not s.supabase_url:
                raise HTTPException(401, "Asymmetric token received but SUPABASE_URL is not configured")
            key = _jwks_client(s.supabase_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=[alg], audience="authenticated")
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid access token: {e}") from e
    return {"id": claims.get("sub"), "email": claims.get("email"), "mode": "supabase"}


def current_user(authorization: str | None = Header(default=None)) -> dict:
    s = get_settings()
    if authorization and authorization.lower().startswith("bearer "):
        return verify_token(authorization.split(" ", 1)[1])
    if s.require_auth:
        raise HTTPException(401, "Authentication required")
    return LOCAL_USER
