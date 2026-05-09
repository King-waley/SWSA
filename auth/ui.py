"""Streamlit login / signup screen."""

import streamlit as st

from auth import login as auth_login
from auth import signup as auth_signup


def _signups_enabled() -> bool:
    try:
        from db.settings import is_feature_enabled

        return is_feature_enabled("signups")
    except Exception:  # noqa: BLE001
        return True


def render_auth_page() -> None:
    """Render the login/signup page. Sets st.session_state.user on success."""
    # Hero (matches the main app's branding)
    st.markdown(
        """
<div class="swsa-hero">
    <div class="swsa-logo-row">
        <span class="swsa-letter l1">S</span>
        <span class="swsa-letter l2">W</span>
        <span class="swsa-letter l3">S</span>
        <span class="swsa-letter l4">A</span>
    </div>
    <div class="swsa-full-name">
        <span class="fn1">Student</span>
        <span class="fn-dot">•</span>
        <span class="fn2">Welfare</span>
        <span class="fn-dot">•</span>
        <span class="fn3">Support</span>
        <span class="fn-dot">•</span>
        <span class="fn4">Agent</span>
    </div>
    <div class="swsa-desc">Sign in to access your wellbeing space</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Centred two-column layout: tabs on the left, value prop on the right.
    left, _, right = st.columns([5, 1, 4])

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if _signups_enabled():
            login_tab, signup_tab = st.tabs(["🔐 Log in", "✨ Sign up"])
        else:
            login_tab = st.container()
            signup_tab = None
            st.info(
                "🔒 New sign-ups are temporarily disabled. "
                "Existing users can still log in below."
            )

        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Username", key="login_username", placeholder="your.username"
                )
                password = st.text_input(
                    "Password", type="password", key="login_password"
                )
                submitted = st.form_submit_button(
                    "Log in", type="primary", use_container_width=True
                )
                if submitted:
                    user, error = auth_login(username, password)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.user = user
                        st.rerun()

        if signup_tab is not None:
            with signup_tab:
                with st.form("signup_form", clear_on_submit=False):
                    username = st.text_input(
                        "Choose a username",
                        key="signup_username",
                        help="3-50 characters: letters, numbers, '.', '_', '-'",
                    )
                    full_name = st.text_input(
                        "Full name (optional)", key="signup_fullname"
                    )
                    email = st.text_input("Email (optional)", key="signup_email")
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="signup_password",
                        help="At least 6 characters",
                    )
                    password_confirm = st.text_input(
                        "Confirm password",
                        type="password",
                        key="signup_password_confirm",
                    )
                    submitted = st.form_submit_button(
                        "Create account", type="primary", use_container_width=True
                    )
                    if submitted:
                        if password != password_confirm:
                            st.error("Passwords don't match.")
                        else:
                            user, error = auth_signup(
                                username, password, full_name=full_name, email=email
                            )
                            if error:
                                st.error(error)
                            else:
                                st.session_state.user = user
                                st.success(
                                    f"Welcome, {user.full_name or user.username}!"
                                )
                                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            """
<div class="glass-card">
<h4>Why an account?</h4>
<p style="color:#475569;line-height:1.7;font-size:0.95rem">
Your account lets S.W.S.A. keep your conversations private to you and
saves your progress across sessions — including quiz history and
recommended services. We never share your data.
</p>
<p style="color:#475569;line-height:1.7;font-size:0.9rem;margin-top:1rem">
🔒 Passwords are stored hashed (bcrypt). Email is optional.
</p>
</div>
""",
            unsafe_allow_html=True,
        )
