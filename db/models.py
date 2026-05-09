"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120))
    email = Column(String(120))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(120), nullable=False, default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    # Categories, sentiment, sub-agents used, api_error, etc. Stored as JSON
    # so the UI can rerender badges + warnings exactly as on the original turn.
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class AdminPromotion(Base):
    """A user that has been promoted to admin via the admin panel.

    The bootstrap admin (ADMIN_USERNAME env var) and any usernames in
    ADMIN_USERNAMES are also admin without needing a row here. This
    table only tracks promotions made at runtime through the UI.
    """

    __tablename__ = "admin_promotions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    promoted_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SupportGroup(Base):
    """A WhatsApp / community support group shown on the Community page."""

    __tablename__ = "support_groups"

    id = Column(Integer, primary_key=True)
    icon = Column(String(20), nullable=False, default="💬")
    name = Column(String(120), nullable=False)
    description = Column(Text, default="")
    url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class UserSession(Base):
    """A persisted login session — a token issued to a browser cookie that
    maps back to a user. Lets users stay logged in across page refreshes."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(80), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
