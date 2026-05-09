"""CRUD helpers for conversations and messages."""

from __future__ import annotations

from datetime import datetime

from db import SessionLocal
from db.models import Conversation, Message


MAX_TITLE_LEN = 60


def _shape_title(text: str) -> str:
    """Pull a sensible title out of the user's first message."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return "New conversation"
    if len(cleaned) <= MAX_TITLE_LEN:
        return cleaned
    return cleaned[: MAX_TITLE_LEN - 1].rstrip() + "…"


def list_conversations(user_id: int, limit: int = 50) -> list[dict]:
    """Return the user's conversations, most-recently-updated first."""
    with SessionLocal() as session:
        rows = (
            session.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "updated_at": r.updated_at,
                "created_at": r.created_at,
            }
            for r in rows
        ]


def create_conversation(user_id: int, first_user_message: str = "") -> int:
    """Create a new conversation and return its id."""
    with SessionLocal() as session:
        conv = Conversation(
            user_id=user_id,
            title=_shape_title(first_user_message),
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)
        return conv.id


def get_messages(conversation_id: int) -> list[dict]:
    """Return ordered message dicts ready to drop into st.session_state.messages."""
    with SessionLocal() as session:
        rows = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .all()
        )
        return [
            {
                "role": r.role,
                "content": r.content,
                "metadata": r.extra or None,
            }
            for r in rows
        ]


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    """Append a message to a conversation and bump the conversation's updated_at."""
    with SessionLocal() as session:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            extra=metadata,
        )
        session.add(msg)
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conv is not None:
            conv.updated_at = datetime.utcnow()
        session.commit()


def update_title(conversation_id: int, title: str) -> None:
    with SessionLocal() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conv is not None:
            conv.title = _shape_title(title)
            session.commit()


def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Delete a conversation only if it belongs to the given user."""
    with SessionLocal() as session:
        conv = (
            session.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )
        if conv is None:
            return False
        session.delete(conv)
        session.commit()
        return True
