"""User signup, login, and password hashing."""

from __future__ import annotations

import re
from dataclasses import dataclass

import bcrypt

from db import SessionLocal
from db.models import User

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")


@dataclass
class UserInfo:
    """Lightweight, detached snapshot of a User row safe to keep in session_state."""
    id: int
    username: str
    full_name: str | None
    email: str | None


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _to_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
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
        return _to_info(user), None


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
        return _to_info(user), None


def get_user(user_id: int) -> UserInfo | None:
    """Look up a user by id (used to refresh session_state if needed)."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return _to_info(user) if user else None
