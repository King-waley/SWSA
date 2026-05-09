"""Admin role check + bootstrap admin account.

Admin status comes from two complementary env vars:

  ADMIN_USERNAMES   Comma-separated whitelist of usernames that are
                    admin. Use this to promote existing users.
                      ADMIN_USERNAMES=alice,bob

  ADMIN_USERNAME    A single username that should always be admin.
  ADMIN_PASSWORD    Combined with ADMIN_USERNAME, this auto-creates a
                    dedicated admin account on first boot if it
                    doesn't exist. Use this when you want a clean
                    admin login that's separate from regular users.
                      ADMIN_USERNAME=admin
                      ADMIN_PASSWORD=<chosen-strong-password>

The bootstrap user is *only* created — never overwritten. To rotate
the password, log in and change it from Account settings.
"""

from __future__ import annotations

import logging
import os

from auth import UserInfo

logger = logging.getLogger(__name__)


def admin_usernames() -> set[str]:
    """All usernames that should be treated as admin in the current
    deployment — combined from ADMIN_USERNAMES (the whitelist) and
    ADMIN_USERNAME (the bootstrap admin)."""
    raw = os.getenv("ADMIN_USERNAMES", "")
    names = {u.strip() for u in raw.split(",") if u.strip()}
    bootstrap = os.getenv("ADMIN_USERNAME", "").strip()
    if bootstrap:
        names.add(bootstrap)
    return names


def is_admin(user: UserInfo | None) -> bool:
    if user is None:
        return False
    # Env-var admin OR DB-promoted admin (UserInfo.is_admin is populated
    # by auth._to_info from both sources at login / session restore).
    return user.is_admin or user.username in admin_usernames()


def bootstrap_admin_from_env() -> None:
    """If ADMIN_USERNAME + ADMIN_PASSWORD are set, ensure that user
    exists in the database with that password. Idempotent — does NOT
    overwrite the password if the user already exists. Safe to call
    every boot.
    """
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        return  # bootstrap not configured; nothing to do

    # Local imports to avoid a circular dependency at module load time
    # (auth/__init__.py imports from db, and db's bootstrap may import
    # from auth/admin.py).
    from auth import _hash_password
    from db import SessionLocal
    from db.models import User

    try:
        with SessionLocal() as session:
            existing = (
                session.query(User).filter(User.username == username).first()
            )
            if existing is not None:
                return  # don't touch a real user's password
            user = User(
                username=username,
                password_hash=_hash_password(password),
                full_name="Administrator",
            )
            session.add(user)
            session.commit()
            logger.info("Bootstrap admin account created: %s", username)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to bootstrap admin account from env vars")
