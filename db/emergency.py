"""CRUD for the sidebar's Emergency contacts list."""

from __future__ import annotations

import logging

from db import SessionLocal
from db.models import EmergencyContact

logger = logging.getLogger(__name__)


_DEFAULT_CONTACTS = [
    ("Samaritans", "116 123 (24/7)"),
    ("Crisis Text", "Text SHOUT to 85258"),
    ("NHS Emergency", "999"),
    ("NHS Non-Emergency", "111"),
    ("Campus Security", "0191 227 4500"),
]


def list_contacts(active_only: bool = False) -> list[dict]:
    with SessionLocal() as session:
        q = session.query(EmergencyContact)
        if active_only:
            q = q.filter(EmergencyContact.is_active.is_(True))
        rows = q.order_by(
            EmergencyContact.sort_order.asc(), EmergencyContact.id.asc()
        ).all()
        return [
            {
                "id": c.id,
                "label": c.label,
                "value": c.value,
                "sort_order": c.sort_order,
                "is_active": c.is_active,
            }
            for c in rows
        ]


def create_contact(
    label: str, value: str, sort_order: int | None = None, is_active: bool = True
) -> tuple[int | None, str | None]:
    label = (label or "").strip()
    value = (value or "").strip()
    if not label or not value:
        return None, "Label and value are both required."
    with SessionLocal() as session:
        if sort_order is None:
            row = (
                session.query(EmergencyContact.sort_order)
                .order_by(EmergencyContact.sort_order.desc())
                .first()
            )
            sort_order = (row[0] + 10) if row else 0
        c = EmergencyContact(
            label=label[:120],
            value=value[:200],
            sort_order=int(sort_order),
            is_active=bool(is_active),
        )
        session.add(c)
        session.commit()
        session.refresh(c)
        return c.id, None


def update_contact(
    contact_id: int,
    *,
    label: str | None = None,
    value: str | None = None,
    sort_order: int | None = None,
    is_active: bool | None = None,
) -> tuple[bool, str | None]:
    with SessionLocal() as session:
        c = (
            session.query(EmergencyContact)
            .filter(EmergencyContact.id == contact_id)
            .first()
        )
        if c is None:
            return False, "Contact not found."
        if label is not None:
            l = (label or "").strip()
            if not l:
                return False, "Label can't be blank."
            c.label = l[:120]
        if value is not None:
            v = (value or "").strip()
            if not v:
                return False, "Value can't be blank."
            c.value = v[:200]
        if sort_order is not None:
            c.sort_order = int(sort_order)
        if is_active is not None:
            c.is_active = bool(is_active)
        session.commit()
        return True, None


def delete_contact(contact_id: int) -> bool:
    with SessionLocal() as session:
        c = (
            session.query(EmergencyContact)
            .filter(EmergencyContact.id == contact_id)
            .first()
        )
        if c is None:
            return False
        session.delete(c)
        session.commit()
        return True


def seed_defaults_if_empty() -> int:
    """First-boot seed of standard UK student emergency contacts."""
    with SessionLocal() as session:
        if session.query(EmergencyContact).count() > 0:
            return 0
        for i, (label, value) in enumerate(_DEFAULT_CONTACTS):
            session.add(
                EmergencyContact(
                    label=label, value=value, sort_order=i * 10, is_active=True
                )
            )
        session.commit()
        return len(_DEFAULT_CONTACTS)
