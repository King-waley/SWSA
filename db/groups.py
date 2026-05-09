"""CRUD helpers for the support_groups table (admin-managed)."""

from __future__ import annotations

import logging

from db import SessionLocal
from db.models import SupportGroup

logger = logging.getLogger(__name__)


def list_groups(active_only: bool = False) -> list[dict]:
    """Return groups ordered by sort_order then id."""
    with SessionLocal() as session:
        q = session.query(SupportGroup)
        if active_only:
            q = q.filter(SupportGroup.is_active.is_(True))
        rows = q.order_by(SupportGroup.sort_order.asc(), SupportGroup.id.asc()).all()
        return [
            {
                "id": g.id,
                "icon": g.icon,
                "name": g.name,
                "description": g.description or "",
                "url": g.url,
                "sort_order": g.sort_order,
                "is_active": g.is_active,
                "created_at": g.created_at,
                "updated_at": g.updated_at,
            }
            for g in rows
        ]


def create_group(
    icon: str,
    name: str,
    description: str,
    url: str,
    sort_order: int | None = None,
    is_active: bool = True,
) -> tuple[int | None, str | None]:
    """Insert a new group. Returns (id, error_message)."""
    name = (name or "").strip()
    url = (url or "").strip()
    if not name:
        return None, "Name is required."
    if not url:
        return None, "Invite URL is required."

    with SessionLocal() as session:
        if sort_order is None:
            current_max = (
                session.query(SupportGroup.sort_order)
                .order_by(SupportGroup.sort_order.desc())
                .first()
            )
            sort_order = (current_max[0] + 10) if current_max else 0

        group = SupportGroup(
            icon=(icon or "💬")[:20],
            name=name[:120],
            description=description or "",
            url=url[:500],
            sort_order=sort_order,
            is_active=is_active,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        return group.id, None


def update_group(
    group_id: int,
    *,
    icon: str | None = None,
    name: str | None = None,
    description: str | None = None,
    url: str | None = None,
    sort_order: int | None = None,
    is_active: bool | None = None,
) -> tuple[bool, str | None]:
    with SessionLocal() as session:
        group = session.query(SupportGroup).filter(SupportGroup.id == group_id).first()
        if group is None:
            return False, "Group not found."
        if icon is not None:
            group.icon = (icon or "💬")[:20]
        if name is not None:
            n = (name or "").strip()
            if not n:
                return False, "Name can't be blank."
            group.name = n[:120]
        if description is not None:
            group.description = description
        if url is not None:
            u = (url or "").strip()
            if not u:
                return False, "URL can't be blank."
            group.url = u[:500]
        if sort_order is not None:
            group.sort_order = int(sort_order)
        if is_active is not None:
            group.is_active = bool(is_active)
        session.commit()
        return True, None


def delete_group(group_id: int) -> bool:
    with SessionLocal() as session:
        group = session.query(SupportGroup).filter(SupportGroup.id == group_id).first()
        if group is None:
            return False
        session.delete(group)
        session.commit()
        return True


def seed_from_config_if_empty() -> int:
    """First-boot seed: if the support_groups table is empty, copy the
    entries from config.SUPPORT_GROUPS into the DB. Returns the number
    of rows inserted (0 if the table already had data).
    """
    from config import SUPPORT_GROUPS  # local import — avoids circular issues

    with SessionLocal() as session:
        if session.query(SupportGroup).count() > 0:
            return 0
        for i, entry in enumerate(SUPPORT_GROUPS or []):
            group = SupportGroup(
                icon=str(entry.get("icon", "💬"))[:20],
                name=str(entry.get("name", "Group"))[:120],
                description=entry.get("description", "") or "",
                url=str(entry.get("url", "")).strip()[:500] or "(missing)",
                sort_order=i * 10,
                is_active=True,
            )
            session.add(group)
        seeded = len(SUPPORT_GROUPS or [])
        session.commit()
        if seeded:
            logger.info("Seeded %d support groups from config.py", seeded)
        return seeded
