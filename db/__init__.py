"""Database connection and schema bootstrap.

Uses Railway's auto-injected `DATABASE_URL` when deployed; falls back to a
local SQLite file (`swsa.db`) when running on a developer machine without
Postgres set up. SQLAlchemy handles the dialect difference transparently.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        # Local fallback. SQLite file lives next to the project.
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
            logger.error(
                "DATABASE_URL is not set on this Railway service. "
                "Falling back to SQLite, which lives in the ephemeral "
                "container filesystem and will be WIPED on every redeploy. "
                "Add a Postgres add-on and link it via "
                "Variables -> Add Reference -> Postgres -> DATABASE_URL."
            )
        return "sqlite:///./swsa.db"
    # SQLAlchemy 2.x dropped support for the legacy `postgres://` scheme.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _resolve_database_url()


def is_persistent_db() -> bool:
    """True if the app is using a real database, False if it's an
    ephemeral SQLite file that will be lost on container restart."""
    return not DATABASE_URL.startswith("sqlite")


def is_running_on_railway() -> bool:
    return bool(
        os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID")
    )

# `check_same_thread` is only meaningful for SQLite; Streamlit reuses the
# connection across reruns from the same thread, but we keep the flag off
# so a single engine works with Streamlit's threading model.
_engine_kwargs: dict = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create any tables that don't exist yet. Safe to call repeatedly."""
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        logger.error("Database init failed: %s", e)
        raise


__all__ = [
    "engine",
    "SessionLocal",
    "init_db",
    "DATABASE_URL",
    "is_persistent_db",
    "is_running_on_railway",
]
