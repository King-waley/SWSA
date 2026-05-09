"""Account settings page — full screen, replaces the old sidebar expander."""

from __future__ import annotations

import streamlit as st

from auth import change_password, update_profile


def render_account_page() -> None:
    user = st.session_state.user

    col_title, col_back = st.columns([6, 2])
    with col_title:
        st.markdown("## ⚙️ Account settings")
    with col_back:
        if st.button(
            "← Back to chat", use_container_width=True, key="settings_back_btn"
        ):
            st.session_state.mode = "chat"
            st.rerun()

    st.caption(
        f"Signed in as **{user.full_name or user.username}** · `@{user.username}`"
    )

    st.markdown("---")

    # ── Profile ─────────────────────────────────────────────
    st.markdown("### 👤 Profile")
    st.caption("Your name and email — visible only to you.")

    with st.form("settings_profile_form"):
        new_full_name = st.text_input(
            "Full name", value=user.full_name or "", key="settings_full_name"
        )
        new_email = st.text_input(
            "Email", value=user.email or "", key="settings_email"
        )
        submitted = st.form_submit_button("Save profile", type="primary")
        if submitted:
            updated, err = update_profile(
                user.id, full_name=new_full_name, email=new_email
            )
            if err:
                st.error(err)
            else:
                st.session_state.user = updated
                st.success("Profile updated.")
                st.rerun()

    st.markdown("---")

    # ── Password ────────────────────────────────────────────
    st.markdown("### 🔒 Change password")
    st.caption("At least 6 characters. Don't reuse your username as the password.")

    with st.form("settings_password_form"):
        curr_pw = st.text_input(
            "Current password", type="password", key="settings_curr_pw"
        )
        new_pw = st.text_input(
            "New password", type="password", key="settings_new_pw"
        )
        new_pw2 = st.text_input(
            "Confirm new password", type="password", key="settings_new_pw2"
        )
        submitted = st.form_submit_button("Change password", type="primary")
        if submitted:
            if new_pw != new_pw2:
                st.error("New passwords don't match.")
            elif new_pw and new_pw == user.username:
                st.error("Password can't be the same as your username.")
            else:
                ok, err = change_password(user.id, curr_pw, new_pw)
                if err:
                    st.error(err)
                else:
                    st.success("Password updated. You're still signed in here.")

    st.markdown("---")

    # ── Account stats ───────────────────────────────────────
    from db.conversations import list_conversations

    convs = list_conversations(user.id, limit=1000)
    st.markdown("### 📊 Your activity")
    cols = st.columns(3)
    cols[0].metric("Conversations", len(convs))
    cols[1].metric(
        "Last active",
        convs[0]["updated_at"].strftime("%b %d, %Y") if convs else "—",
    )
    cols[2].metric("Username", f"@{user.username}")
