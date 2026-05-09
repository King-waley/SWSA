"""Streamlit UI for the admin panel."""

from __future__ import annotations

import os

import streamlit as st

import config
from admin.queries import (
    admin_create_user,
    admin_delete_conversation,
    admin_delete_user,
    admin_demote,
    admin_logout_user,
    admin_promote,
    admin_reset_password,
    all_conversations,
    all_users_with_stats,
    conversation_with_messages,
    recent_signups,
    stats,
)
from auth.admin import admin_usernames
from db.groups import (
    create_group,
    delete_group,
    list_groups,
    update_group,
)


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
        [
            "📊 Dashboard",
            "👥 Users",
            "💬 Conversations",
            "🌐 Community",
            "⚙️ System",
            "⚠️ Danger zone",
        ]
    )
    with tabs[0]:
        _dashboard()
    with tabs[1]:
        _users()
    with tabs[2]:
        _conversations()
    with tabs[3]:
        _community_groups()
    with tabs[4]:
        _system()
    with tabs[5]:
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
    # ── Create new user ──────────────────────────────────────
    with st.expander("➕ Create new user"):
        with st.form("admin_create_user_form", clear_on_submit=True):
            cu_cols = st.columns(2)
            with cu_cols[0]:
                cu_username = st.text_input(
                    "Username", key="cu_username",
                    help="3-50 chars: letters, numbers, '.', '_', '-'",
                )
                cu_full_name = st.text_input("Full name (optional)", key="cu_fullname")
            with cu_cols[1]:
                cu_password = st.text_input(
                    "Password", type="password", key="cu_password",
                    help="At least 6 characters",
                )
                cu_email = st.text_input("Email (optional)", key="cu_email")
            cu_make_admin = st.checkbox(
                "Make this user an admin", value=False, key="cu_make_admin"
            )
            if st.form_submit_button("Create user", type="primary"):
                _, err = admin_create_user(
                    cu_username, cu_password,
                    full_name=cu_full_name, email=cu_email,
                    make_admin=cu_make_admin,
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"Created @{cu_username.strip()}.")
                    st.rerun()

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

            admin_badge = ""
            if u["is_admin"]:
                src = u.get("admin_source")
                tag = "env" if src == "env" else "promoted"
                admin_badge = f" &nbsp;<span style='background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:8px;font-size:0.7rem;font-weight:600'>🛠️ admin · {tag}</span>"

            cols[0].markdown(
                f"**@{u['username']}**{admin_badge}  \n"
                f"{u['full_name'] or '_(no name)_'}",
                unsafe_allow_html=True,
            )
            cols[0].caption(f"📧 {u['email'] or '—'}")

            cols[1].caption(f"📅 Joined {_format_dt(u['created_at'])}")
            cols[1].caption(f"🕐 Last active {_format_dt(u['last_active'])}")

            cols[2].metric("Chats", u["conv_count"])

            with cols[3]:
                # Promote / demote (DB-side only — env-set admins are
                # immutable from the UI, by design).
                if u["admin_source"] == "env":
                    st.caption("Admin via env var (not editable here)")
                elif u["is_admin"]:
                    if st.button(
                        "⬇️ Remove admin",
                        key=f"demote_{u['id']}",
                        use_container_width=True,
                    ):
                        admin_demote(u["id"])
                        st.success(f"@{u['username']} is no longer an admin.")
                        st.rerun()
                else:
                    if st.button(
                        "⬆️ Make admin",
                        key=f"promote_{u['id']}",
                        use_container_width=True,
                    ):
                        admin_promote(u["id"])
                        st.success(f"@{u['username']} is now an admin.")
                        st.rerun()

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


def _community_groups() -> None:
    st.markdown("### 🌐 WhatsApp / Community groups")
    st.caption(
        "Edit the groups shown to students on the Community page. Inactive "
        "groups stay in the DB but are hidden from students."
    )

    # ── Add a new group ──────────────────────────────────────
    with st.expander("➕ Add a new group"):
        with st.form("admin_add_group_form", clear_on_submit=True):
            row = st.columns([1, 4])
            with row[0]:
                ng_icon = st.text_input("Icon", value="💬", key="ng_icon")
            with row[1]:
                ng_name = st.text_input("Name", key="ng_name")
            ng_desc = st.text_area("Description", key="ng_desc", height=80)
            ng_url = st.text_input("Invite URL", key="ng_url")
            ng_active = st.checkbox("Active", value=True, key="ng_active")
            if st.form_submit_button("Add group", type="primary"):
                _, err = create_group(
                    icon=ng_icon, name=ng_name,
                    description=ng_desc, url=ng_url,
                    is_active=ng_active,
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"Added '{ng_name.strip()}'.")
                    st.rerun()

    # ── Existing groups ──────────────────────────────────────
    groups = list_groups(active_only=False)
    if not groups:
        st.info("No groups yet. Use **Add a new group** above.")
        return

    st.markdown(f"#### {len(groups)} group(s)")
    for g in groups:
        with st.container(border=True):
            head_cols = st.columns([1, 5, 2, 2, 1])
            head_cols[0].markdown(f"# {g['icon']}")
            head_cols[1].markdown(f"### {g['name']}")
            head_cols[1].caption(g["description"] or "_(no description)_")
            head_cols[2].caption(f"🔗 {g['url'][:40]}{'…' if len(g['url']) > 40 else ''}")
            head_cols[3].caption(
                "✅ Active" if g["is_active"] else "🚫 Hidden from students"
            )
            with head_cols[4]:
                with st.popover("Edit", use_container_width=True):
                    with st.form(f"edit_group_{g['id']}"):
                        e_row = st.columns([1, 4])
                        with e_row[0]:
                            new_icon = st.text_input(
                                "Icon", value=g["icon"], key=f"e_icon_{g['id']}"
                            )
                        with e_row[1]:
                            new_name = st.text_input(
                                "Name", value=g["name"], key=f"e_name_{g['id']}"
                            )
                        new_desc = st.text_area(
                            "Description",
                            value=g["description"] or "",
                            key=f"e_desc_{g['id']}",
                            height=80,
                        )
                        new_url = st.text_input(
                            "Invite URL", value=g["url"], key=f"e_url_{g['id']}"
                        )
                        new_active = st.checkbox(
                            "Active",
                            value=bool(g["is_active"]),
                            key=f"e_active_{g['id']}",
                        )
                        new_order = st.number_input(
                            "Sort order (lower = higher up)",
                            value=int(g["sort_order"]),
                            step=10,
                            key=f"e_order_{g['id']}",
                        )
                        save_col, del_col = st.columns(2)
                        with save_col:
                            save_clicked = st.form_submit_button(
                                "💾 Save", type="primary", use_container_width=True
                            )
                        with del_col:
                            del_clicked = st.form_submit_button(
                                "🗑️ Delete", use_container_width=True
                            )
                        if save_clicked:
                            ok, err = update_group(
                                g["id"],
                                icon=new_icon,
                                name=new_name,
                                description=new_desc,
                                url=new_url,
                                is_active=new_active,
                                sort_order=int(new_order),
                            )
                            if err:
                                st.error(err)
                            else:
                                st.success("Saved.")
                                st.rerun()
                        if del_clicked:
                            delete_group(g["id"])
                            st.rerun()


def _system() -> None:
    st.markdown("### Environment")

    db_url = os.getenv("DATABASE_URL", "")
    db_kind = "Postgres (Railway)" if "postgres" in db_url else (
        "SQLite (local file)" if not db_url else "Other"
    )

    rows = [
        ("Database", db_kind),
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
    st.markdown("### 🔑 OpenAI API Key")

    if config.OPENAI_API_KEY:
        key = config.OPENAI_API_KEY
        masked = f"{key[:7]}…{key[-4:]}" if len(key) > 12 else "(set)"
        st.success(f"AI mode is **active** — current key: `{masked}`")
    else:
        st.warning("AI mode is **OFF** — no API key configured. The chat will fall back to templates.")

    new_key = st.text_input(
        "Update or set API key",
        type="password",
        placeholder="sk-proj-…",
        help=(
            "Hot-swaps the key for the running process. "
            "For a permanent change set OPENAI_API_KEY in Railway → Variables."
        ),
        key="admin_api_key_input",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "💾 Save key",
            type="primary",
            use_container_width=True,
            key="admin_save_api_key",
        ):
            if new_key and new_key.strip():
                config.OPENAI_API_KEY = new_key.strip()
                os.environ["OPENAI_API_KEY"] = new_key.strip()
                st.success("Key saved. New chat replies will use this key.")
                st.rerun()
            else:
                st.warning("Paste a key first.")
    with col_b:
        if st.button(
            "🗑 Clear key (disable AI)",
            use_container_width=True,
            key="admin_clear_api_key",
        ):
            config.OPENAI_API_KEY = ""
            os.environ.pop("OPENAI_API_KEY", None)
            st.info("Key cleared. Chats will use template fallback.")
            st.rerun()

    st.caption(
        "ℹ️ A hot-swap only persists until the next redeploy. To make a "
        "change survive deploys, edit `OPENAI_API_KEY` in Railway → Variables."
    )

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
