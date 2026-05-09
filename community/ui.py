"""Community / WhatsApp support groups page.

Groups are managed by admins via Admin Panel → Community tab. The page
reads the active groups from the DB so changes go live without a deploy.
"""

from __future__ import annotations

import streamlit as st

from db.groups import list_groups


def render_community_page() -> None:
    col_title, col_back = st.columns([6, 2])
    with col_title:
        st.markdown("## 💬 Community")
    with col_back:
        if st.button(
            "← Back to chat", use_container_width=True, key="community_back_btn"
        ):
            st.session_state.mode = "chat"
            st.rerun()

    st.caption(
        "Join a student-run WhatsApp group to chat with peers — totally optional. "
        "Groups are run by students, not S.W.S.A. staff."
    )

    groups = list_groups(active_only=True)
    if not groups:
        st.info(
            "No groups have been published yet. An admin can add them via "
            "Admin Panel → Community."
        )
        return

    st.markdown("---")

    # Render groups as cards in a responsive 2-column grid.
    for i in range(0, len(groups), 2):
        cols = st.columns(2, gap="medium")
        for j, group in enumerate(groups[i : i + 2]):
            with cols[j]:
                with st.container(border=True):
                    st.markdown(
                        f"### {group.get('icon') or '💬'} {group.get('name') or 'Group'}"
                    )
                    description = group.get("description") or ""
                    if description:
                        st.markdown(description)
                    url = (group.get("url") or "").strip()
                    if url:
                        st.link_button(
                            "Open in WhatsApp →",
                            url,
                            type="primary",
                            use_container_width=True,
                        )
                    else:
                        st.caption("(No invite link configured)")

    st.markdown("---")
    st.caption(
        "🔒 **A note on privacy:** when you tap a link, you leave S.W.S.A. and "
        "join WhatsApp directly — your university account isn't linked to the "
        "group. If a group ever stops feeling safe or supportive, you can "
        "leave at any time."
    )
