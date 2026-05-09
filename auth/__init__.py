"""User signup, login, and password hashing."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

import bcrypt

from db import SessionLocal
from db.models import AdminPromotion, User, UserSession

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")


@dataclass
class UserInfo:
    """Lightweight, detached snapshot of a User row safe to keep in session_state."""
    id: int
    username: str
    full_name: str | None
    email: str | None
    is_admin: bool = False


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _username_in_env_admins(username: str) -> bool:
    """Check whether a username is admin via env vars (ADMIN_USERNAME or
    ADMIN_USERNAMES). Local-imported here to avoid circular dependency
    on auth.admin at module load."""
    import os

    env_single = os.getenv("ADMIN_USERNAME", "").strip()
    if env_single and username == env_single:
        return True
    raw = os.getenv("ADMIN_USERNAMES", "")
    return username in {u.strip() for u in raw.split(",") if u.strip()}


def _is_promoted_admin(session, user_id: int) -> bool:
    return (
        session.query(AdminPromotion)
        .filter(AdminPromotion.user_id == user_id)
        .first()
        is not None
    )


def _to_info(user: User, *, session=None) -> UserInfo:
    """Build a UserInfo. Populates is_admin from env vars + AdminPromotion."""
    is_admin_flag = _username_in_env_admins(user.username)
    if not is_admin_flag:
        if session is not None:
            is_admin_flag = _is_promoted_admin(session, user.id)
        else:
            with SessionLocal() as s:
                is_admin_flag = _is_promoted_admin(s, user.id)
    return UserInfo(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        is_admin=is_admin_flag,
    )


def signup(
    username: str,
    password: str,
    full_name: str | None = None,
    email: str | None = None,
) -> tuple[UserInfo | None, str | None]:
    """Create a new account. Returns (user_info, error_message)."""
    username = (username or "").strip()
    password = password or ""
    full_name = (full_name or "").strip() or None
    email = (email or "").strip() or None

    if not USERNAME_RE.match(username):
        return None, "Username must be 3-50 characters: letters, numbers, '.', '_', '-'."
    if len(password) < 6:
        return None, "Password must be at least 6 characters."

    with SessionLocal() as session:
        existing = session.query(User).filter(User.username == username).first()
        if existing is not None:
            return None, "That username is already taken."

        user = User(
            username=username,
            password_hash=_hash_password(password),
            full_name=full_name,
            email=email,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return _to_info(user, session=session), None


def login(username: str, password: str) -> tuple[UserInfo | None, str | None]:
    """Verify credentials. Returns (user_info, error_message)."""
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return None, "Please enter both username and password."

    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None or not _verify_password(password, user.password_hash):
            return None, "Invalid username or password."
        return _to_info(user, session=session), None


def get_user(user_id: int) -> UserInfo | None:
    """Look up a user by id (used to refresh session_state if needed)."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return _to_info(user, session=session) if user else None


def update_profile(
    user_id: int,
    full_name: str | None = None,
    email: str | None = None,
) -> tuple[UserInfo | None, str | None]:
    """Update the user's full name and/or email. Empty strings clear the field."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            return None, "Account not found."
        if full_name is not None:
            user.full_name = full_name.strip() or None
        if email is not None:
            user.email = email.strip() or None
        session.commit()
        session.refresh(user)
        return _to_info(user, session=session), None


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
) -> tuple[bool, str | None]:
    """Verify current password and set a new one. Returns (ok, error_message)."""
    if len(new_password or "") < 6:
        return False, "New password must be at least 6 characters."
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            return False, "Account not found."
        if not _verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect."
        user.password_hash = _hash_password(new_password)
        session.commit()
        return True, None


# ── Browser sessions (cookie-backed login persistence) ────────────────


SESSION_COOKIE_NAME = "swsa_session"
SESSION_DAYS = 30


def create_session(user_id: int, days: int = SESSION_DAYS) -> str:
    """Issue a fresh opaque session token and persist it. Returns the token."""
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=days)
    with SessionLocal() as session:
        sess = UserSession(user_id=user_id, token=token, expires_at=expires_at)
        session.add(sess)
        session.commit()
    return token


def get_session_user(token: str | None) -> UserInfo | None:
    """Return the user the token belongs to, or None if invalid/expired."""
    if not token:
        return None
    with SessionLocal() as session:
        sess = (
            session.query(UserSession)
            .filter(
                UserSession.token == token,
                UserSession.expires_at > datetime.utcnow(),
            )
            .first()
        )
        if sess is None:
            return None
        user = session.query(User).filter(User.id == sess.user_id).first()
        return _to_info(user, session=session) if user else None


def delete_session(token: str | None) -> None:
    """Invalidate a token (called on logout). Safe to call with None."""
    if not token:
        return
    with SessionLocal() as session:
        session.query(UserSession).filter(UserSession.token == token).delete()
        session.commit()
