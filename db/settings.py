"""Admin-controlled key-value settings store, plus typed accessors for
the ones the app uses (announcement banner, maintenance mode, feature
flags, knowledge-base override)."""

from __future__ import annotations

from typing import Any

from db import SessionLocal
from db.models import Setting


# ── Generic get/set ─────────────────────────────────────────────────


def get_setting(key: str, default: Any = None) -> Any:
    with SessionLocal() as session:
        row = session.query(Setting).filter(Setting.key == key).first()
        if row is None:
            return default
        return row.value


def set_setting(key: str, value: Any) -> None:
    """Upsert a setting. Works on both Postgres and SQLite."""
    with SessionLocal() as session:
        row = session.query(Setting).filter(Setting.key == key).first()
        if row is None:
            session.add(Setting(key=key, value=value))
        else:
            row.value = value
        session.commit()


def delete_setting(key: str) -> None:
    with SessionLocal() as session:
        session.query(Setting).filter(Setting.key == key).delete()
        session.commit()


# ── Announcement banner ─────────────────────────────────────────────


ANNOUNCEMENT_KEY = "announcement"


def get_announcement() -> dict | None:
    """Returns {'text': str, 'severity': 'info'|'warning'|'urgent'} or None."""
    a = get_setting(ANNOUNCEMENT_KEY)
    if not a or not isinstance(a, dict):
        return None
    if not a.get("active"):
        return None
    if not (a.get("text") or "").strip():
        return None
    return {
        "text": a["text"],
        "severity": a.get("severity", "info"),
    }


def set_announcement(text: str, severity: str = "info", active: bool = True) -> None:
    set_setting(
        ANNOUNCEMENT_KEY,
        {"text": text, "severity": severity, "active": bool(active)},
    )


def get_announcement_full() -> dict:
    """Used by the admin editor — includes inactive ones."""
    a = get_setting(ANNOUNCEMENT_KEY) or {}
    return {
        "text": a.get("text", ""),
        "severity": a.get("severity", "info"),
        "active": bool(a.get("active", False)),
    }


# ── Maintenance mode ────────────────────────────────────────────────


MAINTENANCE_KEY = "maintenance_mode"


def is_maintenance_mode() -> bool:
    return bool(get_setting(MAINTENANCE_KEY, False))


def set_maintenance_mode(enabled: bool) -> None:
    set_setting(MAINTENANCE_KEY, bool(enabled))


# ── Feature flags ───────────────────────────────────────────────────


# Default behaviour is "on" for all features. Admins can disable them
# from the panel. Listed here so the UI can render checkboxes for each.
FEATURES = [
    ("signups", "Allow new sign-ups", True),
    ("file_upload", "Allow file upload in chat", True),
    ("study_tools", "Show Study Tools page", True),
    ("community", "Show Community page", True),
]


def is_feature_enabled(key: str) -> bool:
    default = next((d for k, _, d in FEATURES if k == key), True)
    val = get_setting(f"feature.{key}")
    if val is None:
        return default
    return bool(val)


def set_feature_enabled(key: str, enabled: bool) -> None:
    set_setting(f"feature.{key}", bool(enabled))


# ── Knowledge-base override ─────────────────────────────────────────


KB_KEY = "kb_override"


def get_kb_override() -> dict | None:
    val = get_setting(KB_KEY)
    if isinstance(val, dict):
        return val
    return None


def set_kb_override(kb: dict | None) -> None:
    if kb is None:
        delete_setting(KB_KEY)
    else:
        set_setting(KB_KEY, kb)
