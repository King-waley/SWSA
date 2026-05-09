"""Admin role check.

Admin status is governed by an `ADMIN_USERNAMES` environment variable —
a comma-separated whitelist of usernames. Set it once on Railway, no
schema changes needed. Promote or demote anyone by editing the var.

Example:
    ADMIN_USERNAMES=tobi-king
    ADMIN_USERNAMES=tobi-king,alice,bob
"""

from __future__ import annotations

import os

from auth import UserInfo


def admin_usernames() -> set[str]:
    raw = os.getenv("ADMIN_USERNAMES", "")
    return {u.strip() for u in raw.split(",") if u.strip()}


def is_admin(user: UserInfo | None) -> bool:
    if user is None:
        return False
    return user.username in admin_usernames()
