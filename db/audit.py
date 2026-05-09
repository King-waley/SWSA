"""Append-only audit log of admin actions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from db import SessionLocal
from db.models import AuditLog

logger = logging.getLogger(__name__)


def log(
    *,
    admin_user_id: int | None,
    admin_username: str | None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    details: dict | None = None,
) -> None:
    """Best-effort audit-log append. Swallows DB errors so a logging
    failure never breaks the action that triggered it."""
    try:
        with SessionLocal() as session:
            entry = AuditLog(
                admin_user_id=admin_user_id,
                admin_username=admin_username,
                action=action[:80],
                target_type=(target_type or None) and target_type[:50],
                target_id=target_id,
                details=details,
            )
            session.add(entry)
            session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("audit log append failed for action=%s", action)


def recent(limit: int = 200) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "created_at": r.created_at,
                "admin_username": r.admin_username,
                "admin_user_id": r.admin_user_id,
                "action": r.action,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "details": r.details or {},
            }
            for r in rows
        ]


def purge_older_than(days: int) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    with SessionLocal() as session:
        n = session.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
        session.commit()
        return int(n or 0)
