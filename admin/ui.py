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
    category_distribution,
    conversation_with_messages,
    crisis_count,
    crisis_messages,
    export_conversations_json,
    export_users_csv,
    messages_per_day,
    recent_signups,
    signups_per_day,
    stats,
    user_detail,
)
from auth.admin import admin_usernames
from db import audit
from db.emergency import (
    create_contact,
    delete_contact,
    list_contacts,
    update_contact,
)
from db.groups import (
    create_group,
    delete_group,
    list_groups,
    update_group,
)
from db.settings import (
    FEATURES,
    get_announcement_full,
    get_kb_override,
    is_feature_enabled,
    is_maintenance_mode,
    set_announcement,
    set_feature_enabled,
    set_kb_override,
    set_maintenance_mode,
)
from db.usage import usage_per_day, usage_summary


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
            "🚨 Crisis",
            "📝 Content",
            "📈 Insight",
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
        _crisis()
    with tabs[4]:
        _content()
    with tabs[5]:
        _insight()
    with tabs[6]:
        _system()
    with tabs[7]:
        _danger_zone()


def _current_admin() -> tuple[int | None, str | None]:
    u = st.session_state.get("user")
    if u is None:
        return None, None
    return u.id, u.username


# ── Tabs ────────────────────────────────────────────────────────────


def _dashboard() -> None:
    s = stats()
    cost = usage_summary()
    crisis_n = crisis_count()

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

    st.markdown("### Welfare & cost")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("🚨 Crisis turns", crisis_n, help="Assistant replies that fired the crisis-detection path.")
    d2.metric("Tokens (today)", f"{cost['today']['total_tokens']:,}")
    d3.metric("Tokens (7d)", f"{cost['week']['total_tokens']:,}")
    d4.metric("Spend (7d)", f"${cost['week']['cost_usd']:.2f}")

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
                        aid, aname = _current_admin()
                        audit.log(admin_user_id=aid, admin_username=aname,
                                  action="user.demote", target_type="user",
                                  target_id=u["id"],
                                  details={"username": u["username"]})
                        st.success(f"@{u['username']} is no longer an admin.")
                        st.rerun()
                else:
                    if st.button(
                        "⬆️ Make admin",
                        key=f"promote_{u['id']}",
                        use_container_width=True,
                    ):
                        admin_promote(u["id"])
                        aid, aname = _current_admin()
                        audit.log(admin_user_id=aid, admin_username=aname,
                                  action="user.promote", target_type="user",
                                  target_id=u["id"],
                                  details={"username": u["username"]})
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
                        aid, aname = _current_admin()
                        audit.log(admin_user_id=aid, admin_username=aname,
                                  action="user.delete", target_type="user",
                                  target_id=u["id"],
                                  details={"username": u["username"]})
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
    sub = st.tabs(
        ["🔑 API key", "🚧 Feature flags", "🌍 Environment", "📥 Export"]
    )
    with sub[0]:
        _api_key_panel()
    with sub[1]:
        _feature_flags_panel()
    with sub[2]:
        _environment_panel()
    with sub[3]:
        _export_panel()


def _api_key_panel() -> None:
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
                aid, aname = _current_admin()
                audit.log(admin_user_id=aid, admin_username=aname,
                          action="api_key.update")
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
            aid, aname = _current_admin()
            audit.log(admin_user_id=aid, admin_username=aname,
                      action="api_key.clear")
            st.info("Key cleared. Chats will use template fallback.")
            st.rerun()

    st.caption(
        "ℹ️ A hot-swap only persists until the next redeploy. To make a "
        "change survive deploys, edit `OPENAI_API_KEY` in Railway → Variables."
    )


def _feature_flags_panel() -> None:
    st.markdown("### 🚧 Feature flags")
    st.caption(
        "Turn parts of the app on or off without redeploying. Useful while "
        "fixing a bug or staging a launch."
    )

    # Maintenance mode (special)
    with st.container(border=True):
        cols = st.columns([4, 2])
        with cols[0]:
            st.markdown("**🛠️ Maintenance mode**")
            st.caption(
                "When ON, regular users see a 'we'll be back' splash. "
                "Admins can still log in and reach the panel."
            )
        with cols[1]:
            current = is_maintenance_mode()
            new_val = st.toggle("Enabled", value=current, key="maint_toggle")
            if new_val != current:
                set_maintenance_mode(new_val)
                aid, aname = _current_admin()
                audit.log(admin_user_id=aid, admin_username=aname,
                          action="maintenance.toggle",
                          details={"enabled": new_val})
                st.rerun()

    st.markdown("---")
    for key, label, _default in FEATURES:
        with st.container(border=True):
            cols = st.columns([4, 2])
            with cols[0]:
                st.markdown(f"**{label}**")
                st.caption(f"Flag key: `feature.{key}`")
            with cols[1]:
                current = is_feature_enabled(key)
                new_val = st.toggle(
                    "Enabled", value=current, key=f"flag_{key}"
                )
                if new_val != current:
                    set_feature_enabled(key, new_val)
                    aid, aname = _current_admin()
                    audit.log(admin_user_id=aid, admin_username=aname,
                              action="feature.toggle",
                              details={"key": key, "enabled": new_val})
                    st.rerun()


def _environment_panel() -> None:
    st.markdown("### 🌍 Environment")
    db_url = os.getenv("DATABASE_URL", "")
    db_kind = (
        "Postgres (Railway)" if "postgres" in db_url else
        ("SQLite (local file)" if not db_url else "Other")
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
    st.markdown("### Available models")
    st.markdown(
        "Change `OPENAI_CLASSIFIER_MODEL` / `OPENAI_RESPONSE_MODEL` in "
        "`config.py` and redeploy to swap models."
    )


def _export_panel() -> None:
    from datetime import datetime as _dt

    st.markdown("### 📥 Export everything")
    st.caption(
        "Download user accounts and full conversation history. Useful for "
        "backups, research, or GDPR-style data requests."
    )
    stamp = _dt.utcnow().strftime("%Y-%m-%d-%H%M")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**👥 Users (CSV)**")
        st.caption("One row per user with conversation/message counts.")
        st.download_button(
            "Download users.csv",
            data=export_users_csv(),
            file_name=f"swsa-users-{stamp}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with cols[1]:
        st.markdown("**💬 Conversations (JSON)**")
        st.caption("Every conversation with all messages and metadata.")
        st.download_button(
            "Download conversations.json",
            data=export_conversations_json(),
            file_name=f"swsa-conversations-{stamp}.json",
            mime="application/json",
            type="primary",
            use_container_width=True,
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


# ── New top-level tabs ──────────────────────────────────────────────


def _crisis() -> None:
    st.markdown("### 🚨 Crisis-flagged conversations")
    st.caption(
        "Every assistant turn that fired the crisis-detection path "
        "(self-harm / suicide / immediate danger), newest first."
    )
    rows = crisis_messages(limit=200)
    if not rows:
        st.success("No crisis-flagged turns yet.")
        return
    for r in rows:
        with st.container(border=True):
            head = st.columns([4, 2, 2, 1])
            head[0].markdown(
                f"**{r['conversation_title']}**  \n"
                f"by **@{r['username']}**"
            )
            head[1].caption(f"🕐 {_format_dt(r['created_at'])}")
            head[2].caption(
                f"📂 {', '.join(r.get('categories') or []) or '—'}"
            )
            with head[3]:
                if st.button("Open", key=f"open_crisis_{r['message_id']}", use_container_width=True):
                    st.session_state.admin_view_conv_id = r["conversation_id"]
                    st.rerun()
            st.markdown(f"> {r['snippet']}…")


def _content() -> None:
    st.caption(
        "Edit the things students see — community groups, emergency contacts, "
        "the welfare-services knowledge base, and the site-wide announcement."
    )
    sub = st.tabs(
        ["🌐 Community groups", "📞 Emergency contacts", "📚 Knowledge base", "📢 Announcement"]
    )
    with sub[0]:
        _community_groups()
    with sub[1]:
        _emergency_contacts()
    with sub[2]:
        _kb_editor()
    with sub[3]:
        _announcement_editor()


def _emergency_contacts() -> None:
    st.markdown("### 📞 Emergency contacts")
    st.caption(
        "These appear in every user's sidebar under '🚨 Emergency contacts'. "
        "Toggle inactive to hide a contact without deleting it."
    )

    with st.expander("➕ Add a contact"):
        with st.form("add_contact_form", clear_on_submit=True):
            ec_label = st.text_input("Label", key="ec_label", placeholder="e.g. Samaritans")
            ec_value = st.text_input("Value", key="ec_value", placeholder="e.g. 116 123 (24/7)")
            ec_active = st.checkbox("Active", value=True, key="ec_active")
            if st.form_submit_button("Add", type="primary"):
                _, err = create_contact(ec_label, ec_value, is_active=ec_active)
                if err:
                    st.error(err)
                else:
                    aid, aname = _current_admin()
                    audit.log(admin_user_id=aid, admin_username=aname,
                              action="emergency_contact.create",
                              target_type="emergency_contact",
                              details={"label": ec_label, "value": ec_value})
                    st.success("Added.")
                    st.rerun()

    contacts = list_contacts(active_only=False)
    if not contacts:
        st.info("No contacts yet.")
        return
    for c in contacts:
        with st.container(border=True):
            cols = st.columns([3, 4, 2, 2])
            cols[0].markdown(f"**{c['label']}**")
            cols[1].markdown(c["value"])
            cols[2].caption("✅ Active" if c["is_active"] else "🚫 Hidden")
            with cols[3].popover("Edit", use_container_width=True):
                with st.form(f"ec_edit_{c['id']}"):
                    new_label = st.text_input("Label", value=c["label"], key=f"ec_l_{c['id']}")
                    new_value = st.text_input("Value", value=c["value"], key=f"ec_v_{c['id']}")
                    new_order = st.number_input(
                        "Sort order", value=int(c["sort_order"]), step=10, key=f"ec_o_{c['id']}"
                    )
                    new_active = st.checkbox(
                        "Active", value=bool(c["is_active"]), key=f"ec_a_{c['id']}"
                    )
                    sv, dl = st.columns(2)
                    if sv.form_submit_button("💾 Save", type="primary", use_container_width=True):
                        ok, err = update_contact(
                            c["id"], label=new_label, value=new_value,
                            sort_order=int(new_order), is_active=new_active,
                        )
                        if err:
                            st.error(err)
                        else:
                            aid, aname = _current_admin()
                            audit.log(admin_user_id=aid, admin_username=aname,
                                      action="emergency_contact.update",
                                      target_type="emergency_contact", target_id=c["id"])
                            st.success("Saved.")
                            st.rerun()
                    if dl.form_submit_button("🗑 Delete", use_container_width=True):
                        delete_contact(c["id"])
                        aid, aname = _current_admin()
                        audit.log(admin_user_id=aid, admin_username=aname,
                                  action="emergency_contact.delete",
                                  target_type="emergency_contact", target_id=c["id"])
                        st.rerun()


def _kb_editor() -> None:
    import json as _json

    from core.recommendation import load_default_knowledge_base, load_knowledge_base

    st.markdown("### 📚 Welfare-services knowledge base")
    st.caption(
        "This JSON drives every recommendation the AI makes. Edit carefully — "
        "broken JSON falls back to the bundled default file."
    )

    has_override = get_kb_override() is not None
    st.caption(
        "📄 **Currently active:** " +
        ("**DB override** (this editor's last save)" if has_override else "**bundled default file**")
    )

    current = load_knowledge_base()
    text = st.text_area(
        "JSON",
        value=_json.dumps(current, indent=2, ensure_ascii=False),
        height=420,
        key="kb_editor_text",
    )

    cols = st.columns(3)
    if cols[0].button("💾 Save override", type="primary", use_container_width=True):
        try:
            parsed = _json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Top-level JSON must be an object.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Invalid JSON: {exc}")
        else:
            set_kb_override(parsed)
            aid, aname = _current_admin()
            audit.log(admin_user_id=aid, admin_username=aname,
                      action="kb.update", target_type="kb")
            st.success("Saved. New recommendations use this version.")
            st.rerun()

    if cols[1].button("🔄 Reload from DB", use_container_width=True):
        st.rerun()

    if cols[2].button("↩️ Reset to file default", use_container_width=True):
        set_kb_override(None)
        aid, aname = _current_admin()
        audit.log(admin_user_id=aid, admin_username=aname,
                  action="kb.reset", target_type="kb")
        st.success("Override cleared — back to the bundled file.")
        st.rerun()


def _announcement_editor() -> None:
    st.markdown("### 📢 Site-wide announcement banner")
    st.caption(
        "Shown to every logged-in user at the top of the page. Disable when "
        "no longer needed — it doesn't auto-expire."
    )
    current = get_announcement_full()
    with st.form("ann_form"):
        text = st.text_area("Message", value=current["text"], height=100)
        sev = st.selectbox(
            "Severity", ["info", "warning", "urgent"],
            index=["info", "warning", "urgent"].index(current["severity"]),
        )
        active = st.checkbox("Active (show to users)", value=current["active"])
        if st.form_submit_button("Save announcement", type="primary"):
            set_announcement(text, severity=sev, active=active)
            aid, aname = _current_admin()
            audit.log(admin_user_id=aid, admin_username=aname,
                      action="announcement.update", target_type="announcement",
                      details={"severity": sev, "active": active})
            st.success("Saved.")
            st.rerun()


def _insight() -> None:
    st.caption(
        "Numbers and history — daily activity charts, OpenAI cost tracking, "
        "and a record of every admin action."
    )
    sub = st.tabs(["📈 Analytics", "💰 Costs", "📋 Audit log"])
    with sub[0]:
        _analytics()
    with sub[1]:
        _costs()
    with sub[2]:
        _audit_log()


def _analytics() -> None:
    import pandas as pd

    st.markdown("### 📈 Activity")
    days = st.slider("Days", min_value=7, max_value=60, value=14, key="analytics_days")

    sd = signups_per_day(days=days)
    md = messages_per_day(days=days)

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Signups per day**")
        if sd:
            st.line_chart(pd.DataFrame(sd).set_index("day"))
        else:
            st.caption("No signups in this window.")
    with cols[1]:
        st.markdown("**Messages per day**")
        if md:
            st.line_chart(pd.DataFrame(md).set_index("day"))
        else:
            st.caption("No messages in this window.")

    st.markdown("---")
    st.markdown("**Category distribution (all-time)**")
    cat = category_distribution()
    if cat:
        df = pd.DataFrame(
            sorted(cat.items(), key=lambda kv: -kv[1]),
            columns=["category", "count"],
        ).set_index("category")
        st.bar_chart(df)
    else:
        st.caption("No classified turns yet.")


def _costs() -> None:
    import pandas as pd

    st.markdown("### 💰 OpenAI cost tracking")
    summary = usage_summary()
    cols = st.columns(4)
    cols[0].metric("Today", f"${summary['today']['cost_usd']:.4f}",
                   help=f"{summary['today']['total_tokens']:,} tokens · {summary['today']['calls']} calls")
    cols[1].metric("Past 7 days", f"${summary['week']['cost_usd']:.3f}",
                   help=f"{summary['week']['total_tokens']:,} tokens")
    cols[2].metric("Past 30 days", f"${summary['month']['cost_usd']:.2f}",
                   help=f"{summary['month']['total_tokens']:,} tokens")
    cols[3].metric("All time", f"${summary['all_time']['cost_usd']:.2f}",
                   help=f"{summary['all_time']['total_tokens']:,} tokens")

    st.markdown("---")
    st.markdown("**Tokens per day (last 14 days)**")
    daily = usage_per_day(days=14)
    if daily:
        st.line_chart(pd.DataFrame(daily).set_index("day"))
    else:
        st.caption("No API usage recorded yet.")
    st.caption(
        "Costs are estimated from the gpt-4o-mini price table baked into the "
        "code. Update `db/usage.py → PRICES` if rates change."
    )


def _audit_log() -> None:
    st.markdown("### 📋 Audit log (last 200 actions)")
    rows = audit.recent(limit=200)
    if not rows:
        st.caption("No admin actions logged yet.")
        return
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "When": _format_dt(r["created_at"]),
                "Admin": r["admin_username"] or "?",
                "Action": r["action"],
                "Target": (
                    f"{r['target_type']}#{r['target_id']}"
                    if r["target_type"] and r["target_id"] else
                    (r["target_type"] or "")
                ),
            }
            for r in rows
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
