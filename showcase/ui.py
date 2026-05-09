"""Marketing landing page — the first thing a new visitor sees.

Unauthenticated visitors land here. Authenticated visitors (cookie
restored OR just logged in) bypass it entirely and go straight to the
chat. The "Get started" button on this page sets a session-state flag
that pushes the visitor through to the existing auth screen.
"""

from __future__ import annotations

import streamlit as st


# ── Page-specific CSS ────────────────────────────────────────────────


_SHOWCASE_CSS = """
<style>
/* Hide Streamlit's main top padding so the hero starts from the top */
.swsa-showcase + div [data-testid="stMainBlockContainer"] { padding-top: 0 !important; }

/* ── Wrapper ─────────────────────────────────────────────────── */
.swsa-showcase {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0F172A;
    margin: -1rem 0 0;
}

/* ── Hero ────────────────────────────────────────────────────── */
.sc-hero {
    text-align: center;
    padding: 4rem 1rem 3rem;
    background:
        radial-gradient(900px 500px at 20% 10%, rgba(82,183,136,0.18), transparent 60%),
        radial-gradient(900px 500px at 80% 10%, rgba(123,31,162,0.16), transparent 60%),
        radial-gradient(700px 400px at 50% 90%, rgba(21,101,192,0.16), transparent 60%);
    border-radius: 28px;
    margin-bottom: 2rem;
}

.sc-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(45,106,79,0.08);
    color: #1B4332;
    border: 1px solid rgba(45,106,79,0.20);
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    margin-bottom: 1.6rem;
    animation: scFadeIn 0.6s ease-out;
}

.sc-headline {
    font-size: clamp(2.2rem, 5vw, 3.6rem);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -1.5px;
    margin: 0 auto 1.2rem;
    max-width: 920px;
    background: linear-gradient(135deg, #0F172A 0%, #2D6A4F 50%, #1565C0 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: scFadeUp 0.8s ease-out;
}

.sc-subhead {
    font-size: clamp(1rem, 1.6vw, 1.18rem);
    color: #475569;
    max-width: 720px;
    margin: 0 auto 2.2rem;
    line-height: 1.6;
    animation: scFadeUp 0.9s ease-out 0.1s both;
}

.sc-cta-row {
    display: inline-flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
    animation: scFadeUp 1s ease-out 0.2s both;
}

@keyframes scFadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scFadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Stats strip ─────────────────────────────────────────────── */
.sc-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.8rem;
    max-width: 1080px;
    margin: 0 auto 3.2rem;
    padding: 0 1rem;
}
.sc-stat {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.4rem 1rem;
    text-align: center;
    box-shadow: 0 4px 18px rgba(15,23,42,0.04);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.sc-stat:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(15,23,42,0.08); }
.sc-stat-num {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #2D6A4F, #1565C0);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1;
}
.sc-stat-lab {
    font-size: 0.82rem;
    color: #64748B;
    margin-top: 0.4rem;
    font-weight: 500;
}

/* ── Section headings ────────────────────────────────────────── */
.sc-section-title {
    text-align: center;
    margin: 1rem auto 2rem;
}
.sc-section-eyebrow {
    display: inline-block;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #2D6A4F;
    margin-bottom: 0.6rem;
}
.sc-section-h {
    font-size: clamp(1.6rem, 3.2vw, 2.4rem);
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.8px;
    margin: 0 auto;
    max-width: 720px;
    line-height: 1.2;
}
.sc-section-sub {
    font-size: 1rem;
    color: #64748B;
    max-width: 640px;
    margin: 0.6rem auto 0;
    line-height: 1.6;
}

/* ── Feature grid ────────────────────────────────────────────── */
.sc-features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1.1rem;
    max-width: 1080px;
    margin: 0 auto 3.4rem;
    padding: 0 1rem;
}
.sc-feature {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 1.5rem 1.4rem;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    position: relative;
    overflow: hidden;
}
.sc-feature::before {
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: linear-gradient(90deg, var(--c1, #2D6A4F), var(--c2, #1565C0));
    opacity: 0;
    transition: opacity 0.25s ease;
}
.sc-feature:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 32px rgba(15,23,42,0.08);
    border-color: rgba(45,106,79,0.30);
}
.sc-feature:hover::before { opacity: 1; }
.sc-feature-icon {
    font-size: 2rem;
    margin-bottom: 0.6rem;
    line-height: 1;
}
.sc-feature-h {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 0.4rem;
    letter-spacing: -0.2px;
}
.sc-feature-p {
    font-size: 0.92rem;
    color: #475569;
    line-height: 1.55;
    margin: 0;
}

/* ── How it works ────────────────────────────────────────────── */
.sc-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.2rem;
    max-width: 1080px;
    margin: 0 auto 3.4rem;
    padding: 0 1rem;
}
.sc-step {
    text-align: center;
    padding: 1rem;
}
.sc-step-num {
    display: inline-flex;
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #2D6A4F, #52B788);
    color: white;
    border-radius: 50%;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 6px 18px rgba(45,106,79,0.30);
}
.sc-step-h { font-weight: 700; margin-bottom: 0.4rem; color: #0F172A; }
.sc-step-p { font-size: 0.92rem; color: #64748B; line-height: 1.5; max-width: 280px; margin: 0 auto; }

/* ── Team ────────────────────────────────────────────────────── */
.sc-team {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.9rem;
    max-width: 1100px;
    margin: 0 auto 3rem;
    padding: 0 1rem;
}
.sc-member {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.3rem 1rem;
    text-align: center;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.sc-member:hover { transform: translateY(-3px); box-shadow: 0 8px 22px rgba(15,23,42,0.08); }
.sc-member-avatar {
    width: 60px; height: 60px;
    border-radius: 50%;
    margin: 0 auto 0.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1.3rem;
    letter-spacing: -0.5px;
}
.sc-member-name { font-weight: 700; font-size: 0.95rem; color: #0F172A; }
.sc-member-role { font-size: 0.78rem; color: #64748B; margin-top: 0.25rem; line-height: 1.4; }

.sc-av-1 { background: linear-gradient(135deg, #2D6A4F, #52B788); }
.sc-av-2 { background: linear-gradient(135deg, #1565C0, #42A5F5); }
.sc-av-3 { background: linear-gradient(135deg, #7B1FA2, #BA68C8); }
.sc-av-4 { background: linear-gradient(135deg, #E65100, #FF9800); }
.sc-av-5 { background: linear-gradient(135deg, #C2185B, #F06292); }

/* ── Final CTA ───────────────────────────────────────────────── */
.sc-final-cta {
    background:
        linear-gradient(135deg, rgba(45,106,79,0.95), rgba(21,101,192,0.95)),
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.20), transparent 50%);
    color: white;
    border-radius: 28px;
    padding: 3.5rem 2rem;
    text-align: center;
    margin: 2rem auto 1rem;
    max-width: 1080px;
    box-shadow: 0 20px 50px rgba(45,106,79,0.25);
}
.sc-final-cta h2 {
    font-size: clamp(1.6rem, 3vw, 2.2rem);
    font-weight: 800;
    margin: 0 0 0.6rem;
    color: white;
    letter-spacing: -0.5px;
}
.sc-final-cta p {
    color: rgba(255,255,255,0.88);
    margin: 0 auto 1.6rem;
    max-width: 560px;
    line-height: 1.55;
}

/* ── Footer ──────────────────────────────────────────────────── */
.sc-foot {
    text-align: center;
    color: #94A3B8;
    font-size: 0.82rem;
    padding: 1.5rem 1rem 0.5rem;
    line-height: 1.5;
}

/* ── Dark-mode tweaks ─────────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
    .swsa-showcase { color: #E2E8F0; }
    .sc-headline { background: linear-gradient(135deg, #F1F5F9 0%, #52B788 50%, #42A5F5 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .sc-subhead, .sc-section-sub, .sc-feature-p, .sc-step-p { color: #94A3B8; }
    .sc-stat, .sc-feature, .sc-member { background: rgba(30,41,59,0.7); border-color: rgba(255,255,255,0.08); }
    .sc-stat-lab { color: #94A3B8; }
    .sc-feature-h, .sc-step-h, .sc-member-name, .sc-section-h { color: #F1F5F9; }
    .sc-pill { background: rgba(82,183,136,0.16); color: #A7F3D0; border-color: rgba(82,183,136,0.30); }
    .sc-foot { color: #64748B; }
}

/* ── Responsive button row ───────────────────────────────────── */
.sc-cta-row .stButton { display: inline-block; }

</style>
"""


def render_showcase() -> None:
    st.markdown(_SHOWCASE_CSS, unsafe_allow_html=True)
    st.markdown('<div class="swsa-showcase">', unsafe_allow_html=True)

    # ── Hero (uses the existing SWSA logo, not a gradient headline) ──
    st.markdown(
        """
<section class="sc-hero">
    <div class="swsa-logo-row" style="margin-bottom: 0.9rem">
        <span class="swsa-letter l1">S</span>
        <span class="swsa-letter l2">W</span>
        <span class="swsa-letter l3">S</span>
        <span class="swsa-letter l4">A</span>
    </div>
    <div class="swsa-full-name" style="margin-bottom: 1.4rem">
        <span class="fn1">Student</span>
        <span class="fn-dot">•</span>
        <span class="fn2">Welfare</span>
        <span class="fn-dot">•</span>
        <span class="fn3">Support</span>
        <span class="fn-dot">•</span>
        <span class="fn4">Agent</span>
    </div>
    <span class="sc-pill">🛡️ AI-powered student welfare</span>
    <p class="sc-subhead" style="font-size: clamp(1.05rem, 1.7vw, 1.25rem); max-width: 780px; margin-top: 0.6rem">
        A private, conversational AI tutor that listens to what you're going
        through, points you at the right university service, and turns your
        study materials into summaries and quizzes — all in one place, 24/7.
    </p>
    <div class="sc-cta-row" id="sc-cta-anchor"></div>
</section>
""",
        unsafe_allow_html=True,
    )

    # Real Streamlit buttons (they have to live outside the raw HTML)
    cta_l, cta_c, cta_r = st.columns([1, 2, 1])
    with cta_c:
        b1, b2 = st.columns(2)
        with b1:
            if st.button(
                "🚀  Get started — it's free",
                use_container_width=True,
                type="primary",
                key="sc_get_started",
            ):
                st.session_state.showcase_dismissed = True
                st.rerun()
        with b2:
            if st.button(
                "📖  See features",
                use_container_width=True,
                key="sc_see_features",
            ):
                st.markdown(
                    "<script>window.scrollTo({top:600,behavior:'smooth'})</script>",
                    unsafe_allow_html=True,
                )

    # ── Stats strip ───────────────────────────────────────────
    st.markdown(
        """
<div class="sc-stats">
    <div class="sc-stat"><div class="sc-stat-num">5</div><div class="sc-stat-lab">Specialist sub-agents</div></div>
    <div class="sc-stat"><div class="sc-stat-num">23</div><div class="sc-stat-lab">University services</div></div>
    <div class="sc-stat"><div class="sc-stat-num">5</div><div class="sc-stat-lab">Crisis resources</div></div>
    <div class="sc-stat"><div class="sc-stat-num">24/7</div><div class="sc-stat-lab">Available</div></div>
    <div class="sc-stat"><div class="sc-stat-num">100%</div><div class="sc-stat-lab">Private &amp; confidential</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Features ──────────────────────────────────────────────
    st.markdown(
        """
<div class="sc-section-title">
    <span class="sc-section-eyebrow">What it does</span>
    <h2 class="sc-section-h">Built for the moments students actually need help</h2>
    <p class="sc-section-sub">
        Not a chatbot bolted onto a university website. A tool that listens,
        asks the right follow-up, and points to a real human service.
    </p>
</div>
<div class="sc-features">
    <div class="sc-feature">
        <div class="sc-feature-icon">💬</div>
        <h3 class="sc-feature-h">Conversational AI tutor</h3>
        <p class="sc-feature-p">Talks like a friend who happens to know what support is available — short replies, real follow-up questions, no brochure dumps.</p>
    </div>
    <div class="sc-feature">
        <div class="sc-feature-icon">🚨</div>
        <h3 class="sc-feature-h">Crisis-aware safety net</h3>
        <p class="sc-feature-p">Defence-in-depth detection: a regex layer plus an LLM classifier. If either flags self-harm, crisis contacts surface immediately.</p>
    </div>
    <div class="sc-feature">
        <div class="sc-feature-icon">📚</div>
        <h3 class="sc-feature-h">Document → quiz study tools</h3>
        <p class="sc-feature-p">Drop a PDF, DOCX, or notes file in chat to get a summary, key concepts, or a 5-question quiz with instant scoring.</p>
    </div>
    <div class="sc-feature">
        <div class="sc-feature-icon">🌐</div>
        <h3 class="sc-feature-h">Community support groups</h3>
        <p class="sc-feature-p">Join curated student-run WhatsApp groups — Adaba (Nigerian community), academic support, and more. All optional.</p>
    </div>
    <div class="sc-feature">
        <div class="sc-feature-icon">🏥</div>
        <h3 class="sc-feature-h">NHS &amp; GP guidance</h3>
        <p class="sc-feature-p">Asks about your GP and IHS like a careful friend — and tells you exactly how to register if you haven't yet.</p>
    </div>
    <div class="sc-feature">
        <div class="sc-feature-icon">🔒</div>
        <h3 class="sc-feature-h">Privacy-first by design</h3>
        <p class="sc-feature-p">Bcrypt-hashed passwords. Opaque session tokens. No third-party trackers. Conversations visible only to you.</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── How it works ──────────────────────────────────────────
    st.markdown(
        """
<div class="sc-section-title">
    <span class="sc-section-eyebrow">How it works</span>
    <h2 class="sc-section-h">From "I don't know where to start" to "I know what to do" in three steps</h2>
</div>
<div class="sc-steps">
    <div class="sc-step">
        <div class="sc-step-num">1</div>
        <div class="sc-step-h">Sign up</div>
        <p class="sc-step-p">Create a private account in seconds. Username and password — that's it.</p>
    </div>
    <div class="sc-step">
        <div class="sc-step-num">2</div>
        <div class="sc-step-h">Tell us what's going on</div>
        <p class="sc-step-p">Type, voice your concern, or even attach a file. The AI listens and asks the right follow-up.</p>
    </div>
    <div class="sc-step">
        <div class="sc-step-num">3</div>
        <div class="sc-step-h">Get matched, not lectured</div>
        <p class="sc-step-p">Real services with names, phone numbers, and emails — not a generic "speak to your tutor".</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Team ───────────────────────────────────────────────────
    st.markdown(
        """
<div class="sc-section-title">
    <span class="sc-section-eyebrow">The team</span>
    <h2 class="sc-section-h">Built by 5 MSc students, for the LD7237 Hackathon</h2>
    <p class="sc-section-sub">
        Northumbria University — Contemporary Computing &amp; Digital Technologies.
    </p>
</div>
<div class="sc-team">
    <div class="sc-member">
        <div class="sc-member-avatar sc-av-1">AA</div>
        <div class="sc-member-name">Adedamola Akano</div>
        <div class="sc-member-role">Project Manager &amp; Documentation</div>
    </div>
    <div class="sc-member">
        <div class="sc-member-avatar sc-av-2">AA</div>
        <div class="sc-member-name">Adewale Adeyemi</div>
        <div class="sc-member-role">AI Model Integration &amp; Backend</div>
    </div>
    <div class="sc-member">
        <div class="sc-member-avatar sc-av-3">DM</div>
        <div class="sc-member-name">David Makinde</div>
        <div class="sc-member-role">Frontend Interface &amp; UX Design</div>
    </div>
    <div class="sc-member">
        <div class="sc-member-avatar sc-av-4">BF</div>
        <div class="sc-member-name">Boluwatife Fatoba</div>
        <div class="sc-member-role">Knowledge Base &amp; Testing</div>
    </div>
    <div class="sc-member">
        <div class="sc-member-avatar sc-av-5">AJ</div>
        <div class="sc-member-name">Adefunke Jayesimi</div>
        <div class="sc-member-role">Research &amp; Ethical Review</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Final CTA ─────────────────────────────────────────────
    st.markdown(
        """
<div class="sc-final-cta">
    <h2>Your wellbeing matters. Let's make it easier.</h2>
    <p>Free for students. No tracking. No long forms. Just sign in and start a conversation.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    fcl, fcc, fcr = st.columns([1, 2, 1])
    with fcc:
        if st.button(
            "🚀  Sign in / Sign up to continue",
            use_container_width=True,
            type="primary",
            key="sc_final_cta",
        ):
            st.session_state.showcase_dismissed = True
            st.rerun()

    # ── Footer ────────────────────────────────────────────────
    st.markdown(
        """
<div class="sc-foot">
    ⚠️ S.W.S.A. provides guidance only. Not a substitute for professional medical, legal, or financial advice. In emergencies call <strong>999</strong>.
    <br/>
    Built for the LD7237 Hackathon · 2026
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
