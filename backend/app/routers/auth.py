# backend/app/routers/auth.py
"""Authentication API Router providing JWT register, login, profile, and Google auth."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.db_models import User
from app.db_session import get_session
from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_google_id_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatarUrl: Optional[str] = None
    providerId: Optional[str] = None


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatarUrl": user.avatar_url,
        "provider": user.provider,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


def _get_current_user_from_header(authorization: Optional[str]) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token required.")
    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    session = get_session()
    try:
        user = session.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User account no longer exists.")
        return user
    finally:
        session.close()


@router.post("/register")
def register_user(payload: RegisterRequest):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Valid email address is required.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters long.")
    
    name = (payload.name or email.split("@")[0]).strip()
    session = get_session()
    try:
        existing = session.scalar(select(User).where(User.email == email))
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email address already exists.")
        
        user = User(
            id=f"usr_{uuid.uuid4().hex[:12]}",
            email=email,
            hashed_password=hash_password(payload.password),
            name=name,
            provider="local",
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_access_token(user.id, user.email)
        return {"token": token, "user": _user_dict(user)}
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {exc}")
    finally:
        session.close()


@router.post("/login")
def login_user(payload: LoginRequest):
    email = payload.email.strip().lower()
    session = get_session()
    try:
        user = session.scalar(select(User).where(User.email == email))
        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        token = create_access_token(user.id, user.email)
        return {"token": token, "user": _user_dict(user)}
    finally:
        session.close()


@router.get("/me")
def get_current_profile(authorization: Optional[str] = Header(None)):
    user = _get_current_user_from_header(authorization)
    return {"user": _user_dict(user)}


@router.post("/google")
def google_auth(payload: GoogleAuthRequest):
    session = get_session()
    try:
        if payload.credential:
            profile = verify_google_id_token(payload.credential)
            email = profile["email"]
            name = profile["name"]
            avatar_url = profile["avatar_url"]
            provider_id = profile["provider_id"]
        elif payload.email and payload.providerId:
            email = payload.email.strip().lower()
            name = payload.name or email.split("@")[0]
            avatar_url = payload.avatarUrl
            provider_id = payload.providerId
        else:
            raise HTTPException(status_code=422, detail="Google authentication payload incomplete.")

        user = session.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                id=f"usr_{uuid.uuid4().hex[:12]}",
                email=email,
                name=name,
                avatar_url=avatar_url,
                provider="google",
                provider_id=provider_id,
                created_at=datetime.now(timezone.utc),
            )
            session.add(user)
        else:
            if avatar_url:
                user.avatar_url = avatar_url
            if provider_id:
                user.provider_id = provider_id

        session.commit()
        session.refresh(user)

        token = create_access_token(user.id, user.email)
        return {"token": token, "user": _user_dict(user)}
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Google authentication failed: {exc}")
    finally:
        session.close()
