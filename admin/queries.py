"""Admin-only database queries: stats, listings, destructive operations."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from db import SessionLocal
from db.models import AdminPromotion, Conversation, Message, User, UserSession


# ── Read-only ─────────────────────────────────────────────────────────


def stats() -> dict:
    """Return high-level counts for the admin dashboard."""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    with SessionLocal() as session:
        return {
            "total_users": session.query(User).count(),
            "total_conversations": session.query(Conversation).count(),
            "total_messages": session.query(Message).count(),
            "active_sessions": session.query(UserSession)
            .filter(UserSession.expires_at > now)
            .count(),
            "new_users_24h": session.query(User)
            .filter(User.created_at > last_24h)
            .count(),
            "new_users_7d": session.query(User)
            .filter(User.created_at > last_7d)
            .count(),
            "msgs_24h": session.query(Message)
            .filter(Message.created_at > last_24h)
            .count(),
        }


def _env_admin_usernames() -> set[str]:
    """Admin usernames coming from env vars (ADMIN_USERNAME / ADMIN_USERNAMES)."""
    import os

    raw = os.getenv("ADMIN_USERNAMES", "")
    names = {u.strip() for u in raw.split(",") if u.strip()}
    bootstrap = os.getenv("ADMIN_USERNAME", "").strip()
    if bootstrap:
        names.add(bootstrap)
    return names


def all_users_with_stats() -> list[dict]:
    """Every user, with conversation count, last activity, and admin flag."""
    env_admins = _env_admin_usernames()
    with SessionLocal() as session:
        rows = (
            session.query(
                User,
                func.count(Conversation.id).label("conv_count"),
                func.max(Conversation.updated_at).label("last_active"),
            )
            .outerjoin(Conversation, Conversation.user_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
            .all()
        )

        # Pull all promoted user_ids in one query so we don't N+1.
        promoted_ids: set[int] = {
            r.user_id for r in session.query(AdminPromotion.user_id).all()
        }

        return [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "created_at": user.created_at,
                "conv_count": int(conv_count or 0),
                "last_active": last_active,
                "is_admin": (
                    user.username in env_admins or user.id in promoted_ids
                ),
                "admin_source": (
                    "env" if user.username in env_admins
                    else ("db" if user.id in promoted_ids else None)
                ),
            }
            for user, conv_count, last_active in rows
        ]


def all_conversations(limit: int = 200) -> list[dict]:
    """Most recent conversations across all users."""
    with SessionLocal() as session:
        rows = (
            session.query(
                Conversation,
                User.username,
                func.count(Message.id).label("msg_count"),
            )
            .join(User, User.id == Conversation.user_id)
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .group_by(Conversation.id, User.username)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "username": username,
                "user_id": conv.user_id,
                "updated_at": conv.updated_at,
                "created_at": conv.created_at,
                "msg_count": int(msg_count or 0),
            }
            for conv, username, msg_count in rows
        ]


def conversation_with_messages(conv_id: int) -> dict | None:
    """Full conversation including every message — for admin viewing."""
    with SessionLocal() as session:
        conv = session.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv is None:
            return None
        owner = session.query(User).filter(User.id == conv.user_id).first()
        msgs = (
            session.query(Message)
            .filter(Message.conversation_id == conv_id)
            .order_by(Message.id.asc())
            .all()
        )
        return {
            "id": conv.id,
            "title": conv.title,
            "username": owner.username if owner else "(deleted user)",
            "user_id": conv.user_id,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                    "extra": m.extra or {},
                }
                for m in msgs
            ],
        }


def recent_signups(limit: int = 10) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "username": u.username,
                "full_name": u.full_name,
                "created_at": u.created_at,
            }
            for u in rows
        ]


# ── Destructive ───────────────────────────────────────────────────────


def admin_delete_user(user_id: int) -> bool:
    """Delete a user and cascade-delete their conversations, messages, sessions."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            return False
        session.delete(user)
        session.commit()
        return True


def admin_delete_conversation(conv_id: int) -> bool:
    with SessionLocal() as session:
        conv = session.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv is None:
            return False
        session.delete(conv)
        session.commit()
        return True


def admin_reset_password(user_id: int, new_password: str) -> tuple[bool, str | None]:
    """Force-reset a user's password without needing the old one. Also
    invalidates all their existing browser sessions so they have to
    re-log-in everywhere."""
    if len(new_password or "") < 6:
        return False, "Password must be at least 6 characters."

    # Local import to avoid circular dependency at module load time.
    from auth import _hash_password

    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            return False, "User not found."
        user.password_hash = _hash_password(new_password)
        session.query(UserSession).filter(UserSession.user_id == user_id).delete()
        session.commit()
        return True, None


def admin_logout_user(user_id: int) -> int:
    """Invalidate all browser sessions for a user. Returns count removed."""
    with SessionLocal() as session:
        deleted = (
            session.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .delete()
        )
        session.commit()
        return int(deleted or 0)


def admin_create_user(
    username: str,
    password: str,
    full_name: str | None = None,
    email: str | None = None,
    make_admin: bool = False,
) -> tuple[int | None, str | None]:
    """Admin-side user creation. Reuses the public signup() validation."""
    from auth import signup

    info, err = signup(username, password, full_name=full_name, email=email)
    if err:
        return None, err
    if make_admin and info is not None:
        admin_promote(info.id)
    return (info.id if info else None), None


def admin_promote(user_id: int) -> bool:
    """Mark a user as admin via the admin_promotions table. Idempotent."""
    with SessionLocal() as session:
        existing = (
            session.query(AdminPromotion)
            .filter(AdminPromotion.user_id == user_id)
            .first()
        )
        if existing is not None:
            return True
        session.add(AdminPromotion(user_id=user_id))
        session.commit()
        return True


def admin_demote(user_id: int) -> bool:
    """Remove DB-level admin promotion. Note: this can't remove env-var
    admin status (ADMIN_USERNAME / ADMIN_USERNAMES) — that's set in
    Railway. Returns True if a row was deleted."""
    with SessionLocal() as session:
        n = (
            session.query(AdminPromotion)
            .filter(AdminPromotion.user_id == user_id)
            .delete()
        )
        session.commit()
        return bool(n)
