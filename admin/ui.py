"""Streamlit UI for the admin panel."""

from __future__ import annotations

import os

import streamlit as st

import config
from admin.queries import (
    admin_delete_conversation,
    admin_delete_user,
    admin_logout_user,
    admin_reset_password,
    all_conversations,
    all_users_with_stats,
    conversation_with_messages,
    recent_signups,
    stats,
)
from auth.admin import admin_usernames


def _format_dt(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def render_admin_panel() -> None:
    col_title, col_back = st.columns([6, 2])
    with col_title:
        st.markdown("## 🛠️ Admin Panel")
    with col_back:
        if st.button("← Back to chat", use_container_width=True, key="admin_back_btn"):
            st.session_state.mode = "chat"
            st.rerun()

    st.caption(
        f"Signed in as **{st.session_state.user.username}** · admin role granted via "
        "`ADMIN_USERNAMES` environment variable"
    )

    tabs = st.tabs(
        ["📊 Dashboard", "👥 Users", "💬 Conversations", "⚙️ System", "⚠️ Danger zone"]
    )
    with tabs[0]:
        _dashboard()
    with tabs[1]:
        _users()
    with tabs[2]:
        _conversations()
    with tabs[3]:
        _system()
    with tabs[4]:
        _danger_zone()


# ── Tabs ────────────────────────────────────────────────────────────


def _dashboard() -> None:
    s = stats()
    st.markdown("### Live counts")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Total users",
        s["total_users"],
        delta=f"+{s['new_users_24h']} (24h)" if s["new_users_24h"] else None,
    )
    c2.metric("Conversations", s["total_conversations"])
    c3.metric(
        "Messages",
        s["total_messages"],
        delta=f"+{s['msgs_24h']} (24h)" if s["msgs_24h"] else None,
    )
    c4.metric("Active sessions", s["active_sessions"])

    st.markdown("---")
    st.markdown("### Recent signups")
    signups = recent_signups(limit=10)
    if not signups:
        st.caption("No signups yet.")
    else:
        for u in signups:
            st.markdown(
                f"- **@{u['username']}** "
                f"{('(' + u['full_name'] + ')') if u['full_name'] else ''} · "
                f"{_format_dt(u['created_at'])}"
            )


def _users() -> None:
    users = all_users_with_stats()
    st.markdown(f"### {len(users)} user(s)")

    search = st.text_input(
        "Search by username, name, or email", key="admin_user_search", placeholder="…"
    ).strip().lower()
    if search:
        users = [
            u
            for u in users
            if search in (u["username"] or "").lower()
            or search in (u["full_name"] or "").lower()
            or search in (u["email"] or "").lower()
        ]

    for u in users:
        with st.container(border=True):
            cols = st.columns([3, 3, 2, 2])

            cols[0].markdown(
                f"**@{u['username']}**  \n"
                f"{u['full_name'] or '_(no name)_'}"
            )
            cols[0].caption(f"📧 {u['email'] or '—'}")

            cols[1].caption(f"📅 Joined {_format_dt(u['created_at'])}")
            cols[1].caption(f"🕐 Last active {_format_dt(u['last_active'])}")

            cols[2].metric("Chats", u["conv_count"])

            with cols[3]:
                with st.popover("🔑 Reset password", use_container_width=True):
                    with st.form(f"reset_form_{u['id']}"):
                        new_pw = st.text_input(
                            "New password", type="password", key=f"newpw_{u['id']}"
                        )
                        if st.form_submit_button("Force-reset"):
                            ok, err = admin_reset_password(u["id"], new_pw)
                            if err:
                                st.error(err)
                            else:
                                st.success(
                                    f"Reset. @{u['username']} has been logged out everywhere."
                                )

                with st.popover("🚪 Force log-out", use_container_width=True):
                    st.write(f"Invalidate all sessions for **@{u['username']}**?")
                    if st.button(
                        "Confirm",
                        key=f"logout_{u['id']}",
                        use_container_width=True,
                    ):
                        n = admin_logout_user(u["id"])
                        st.success(f"Removed {n} session(s).")

                with st.popover("🗑️ Delete user", use_container_width=True):
                    st.warning(
                        f"Delete **@{u['username']}** and all their "
                        f"{u['conv_count']} conversation(s)?"
                    )
                    if st.button(
                        "I'm sure, delete",
                        key=f"del_user_{u['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        admin_delete_user(u["id"])
                        st.rerun()


def _conversations() -> None:
    if "admin_view_conv_id" not in st.session_state:
        st.session_state.admin_view_conv_id = None

    if st.session_state.admin_view_conv_id is not None:
        conv = conversation_with_messages(st.session_state.admin_view_conv_id)
        if conv is None:
            st.session_state.admin_view_conv_id = None
            st.rerun()
        if st.button("← Back to list", key="admin_conv_back"):
            st.session_state.admin_view_conv_id = None
            st.rerun()
        st.markdown(f"### {conv['title']}")
        st.caption(
            f"@{conv['username']} · {len(conv['messages'])} messages · "
            f"started {_format_dt(conv['created_at'])}"
        )
        for m in conv["messages"]:
            avatar = "🧑‍🎓" if m["role"] == "user" else "🛡️"
            with st.chat_message(m["role"], avatar=avatar):
                st.markdown(m["content"])
        return

    convs = all_conversations()
    st.markdown(f"### {len(convs)} most recent conversation(s)")
    for c in convs:
        with st.container(border=True):
            cols = st.columns([4, 2, 1, 1, 1])
            cols[0].markdown(f"**{c['title']}**")
            cols[0].caption(f"@{c['username']}")
            cols[1].caption(f"🕐 {_format_dt(c['updated_at'])}")
            cols[2].metric("Msgs", c["msg_count"])
            if cols[3].button("👁️ View", key=f"view_conv_{c['id']}", use_container_width=True):
                st.session_state.admin_view_conv_id = c["id"]
                st.rerun()
            with cols[4].popover("🗑️", use_container_width=True):
                if st.button(
                    "Delete", key=f"del_conv_{c['id']}", type="primary",
                    use_container_width=True,
                ):
                    admin_delete_conversation(c["id"])
                    st.rerun()


def _system() -> None:
    st.markdown("### Environment")

    db_url = os.getenv("DATABASE_URL", "")
    db_kind = "Postgres (Railway)" if "postgres" in db_url else (
        "SQLite (local file)" if not db_url else "Other"
    )

    rows = [
        ("Database", db_kind),
        ("OpenAI key", "✅ Configured" if config.OPENAI_API_KEY else "❌ Not set"),
        ("Classifier model", config.OPENAI_CLASSIFIER_MODEL),
        ("Response model", config.OPENAI_RESPONSE_MODEL),
        ("Railway env", os.getenv("RAILWAY_ENVIRONMENT") or "(local dev)"),
        ("Railway service", os.getenv("RAILWAY_SERVICE_NAME") or "—"),
        ("Admin usernames", ", ".join(sorted(admin_usernames())) or "(none configured)"),
    ]
    for label, value in rows:
        a, b = st.columns([2, 5])
        a.markdown(f"**{label}**")
        b.markdown(value)

    st.markdown("---")
    st.markdown("### Available models")
    st.markdown(
        "Change `OPENAI_CLASSIFIER_MODEL` / `OPENAI_RESPONSE_MODEL` in "
        "`config.py` and redeploy to swap models."
    )


def _danger_zone() -> None:
    st.markdown("### Danger zone")
    st.warning(
        "These actions are irreversible. They affect every user, not just yours."
    )

    with st.expander("Delete ALL conversations (every user)"):
        st.write(
            "This wipes every conversation and message in the database. Users "
            "stay registered and can keep chatting; their history just vanishes."
        )
        confirm = st.text_input(
            "Type **DELETE EVERYTHING** to confirm", key="danger_confirm_convs"
        )
        if st.button(
            "Wipe all conversations",
            disabled=confirm != "DELETE EVERYTHING",
            type="primary",
        ):
            from db import SessionLocal
            from db.models import Conversation

            with SessionLocal() as session:
                count = session.query(Conversation).count()
                session.query(Conversation).delete()
                session.commit()
            st.success(f"Deleted {count} conversation(s).")

    with st.expander("Force-log-out every user"):
        st.write(
            "Invalidate every browser session. Everyone (including you) will "
            "be redirected to the login screen on their next request."
        )
        confirm = st.text_input(
            "Type **LOG OUT EVERYONE** to confirm", key="danger_confirm_sessions"
        )
        if st.button(
            "Force-log-out everyone",
            disabled=confirm != "LOG OUT EVERYONE",
            type="primary",
        ):
            from db import SessionLocal
            from db.models import UserSession

            with SessionLocal() as session:
                count = session.query(UserSession).count()
                session.query(UserSession).delete()
                session.commit()
            st.success(f"Invalidated {count} session(s). You're next.")
