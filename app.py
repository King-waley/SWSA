"""S.W.S.A. Streamlit web application."""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import config
from config import CATEGORY_LABELS
from agents.main_agent import MainAgent
from auth import change_password, update_profile
from auth.ui import render_auth_page
from db import init_db
from db.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_messages,
    list_conversations,
    update_title,
)
from study.ui import render_study_tools

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="S.W.S.A. — Student Welfare Support Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  PREMIUM CSS
st.markdown("""
<style>
/* ── Fonts ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ── Root Variables ────────────────────────────────────────── */
:root {
    --c1: #2D6A4F;   /* S — green  */
    --c1-light: #52B788;
    --c2: #1565C0;   /* W — blue   */
    --c2-light: #42A5F5;
    --c3: #7B1FA2;   /* S — purple */
    --c3-light: #BA68C8;
    --c4: #E65100;   /* A — orange */
    --c4-light: #FF9800;
    --dark:   #1B2A3D;
    --darker: #0F1923;
    --pale-green: #D8F3DC;
    --radius-lg: 20px;
    --radius-md: 14px;
    --radius-sm: 10px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.12);
}

/* ── Hide Streamlit chrome ─────────────────────────────────── */
#MainMenu, header, footer,
.stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] { display: none !important; }

/* ── Global ────────────────────────────────────────────────── */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
.stApp {
    background: linear-gradient(160deg, #F0F4F8 0%, #FAFBFD 40%, #F5F0FF 100%);
}

/* ── Sidebar ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--dark) 0%, var(--darker) 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] .stMarkdown h5,
section[data-testid="stSidebar"] .stMarkdown strong { color: #F1F5F9 !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }
section[data-testid="stSidebar"] .stTextInput > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: var(--radius-sm) !important;
}
section[data-testid="stSidebar"] .stTextInput input { color: #E2E8F0 !important; }
section[data-testid="stSidebar"] .stTextInput input::placeholder { color: #64748B !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #CBD5E1 !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.3s ease !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.20) !important;
    transform: translateY(-1px) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--c1), var(--c1-light)) !important;
    border: none !important; color: #fff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 20px rgba(45,106,79,0.4) !important;
}
section[data-testid="stSidebar"] div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04); border-radius: var(--radius-sm); padding: 0.6rem;
}
section[data-testid="stSidebar"] div[data-testid="stMetric"] label { color: #64748B !important; font-size: 0.7rem !important; }
section[data-testid="stSidebar"] div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #F1F5F9 !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: var(--radius-sm) !important;
}
section[data-testid="stSidebar"] .stAlert {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Main Container ────────────────────────────────────────── */
.block-container { max-width: 880px !important; padding-top: 1.5rem !important; }

/* ── SWSA Hero Logo ────────────────────────────────────────── */
.swsa-hero {
    text-align: center;
    padding: 2rem 0 1rem;
    animation: heroIn 1s ease-out;
}
@keyframes heroIn {
    from { opacity: 0; transform: translateY(-30px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.swsa-logo-row {
    display: inline-flex;
    gap: 8px;
    margin-bottom: 0.75rem;
    perspective: 800px;
}
.swsa-letter {
    width: 72px; height: 72px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 18px;
    font-size: 2.1rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.5px;
    box-shadow: var(--shadow-md);
    transition: transform 0.35s cubic-bezier(.34,1.56,.64,1), box-shadow 0.35s;
    cursor: default;
    position: relative;
}
.swsa-letter::after {
    content: '';
    position: absolute; inset: 0;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(255,255,255,0.25), rgba(255,255,255,0));
    pointer-events: none;
}
.swsa-letter:hover {
    transform: translateY(-8px) rotateX(-8deg) scale(1.06);
    box-shadow: var(--shadow-lg);
}
.l1 { background: linear-gradient(145deg, var(--c1), var(--c1-light)); }
.l2 { background: linear-gradient(145deg, var(--c2), var(--c2-light)); }
.l3 { background: linear-gradient(145deg, var(--c3), var(--c3-light)); }
.l4 { background: linear-gradient(145deg, var(--c4), var(--c4-light)); }

.swsa-full-name {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: 0.6rem;
}
.fn1 { color: var(--c1); }
.fn2 { color: var(--c2); }
.fn3 { color: var(--c3); }
.fn4 { color: var(--c4); }
.fn-dot { color: #94A3B8; }

.swsa-desc {
    font-size: 0.7rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #94A3B8;
    margin-top: 0.35rem;
    font-weight: 500;
}
.swsa-tagline {
    font-size: 1.15rem;
    color: #475569;
    margin-top: 1rem;
    font-weight: 400;
    line-height: 1.6;
    text-align: center;
    animation: fadeIn 1.2s ease-out 0.4s both;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ── Sidebar Mini Logo ─────────────────────────────────────── */
.sb-logo { text-align: center; padding: 0.6rem 0 0.2rem; }
.sb-logo-row { display: inline-flex; gap: 4px; }
.sb-letter {
    width: 34px; height: 34px;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 9px; font-size: 1rem; font-weight: 800; color: #fff;
}
.sb-tag {
    font-size: 0.55rem; letter-spacing: 2.5px; text-transform: uppercase;
    color: #64748B !important; margin-top: 0.35rem;
}

/* ── Glass Card ────────────────────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.85);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 1.8rem 2rem;
    margin-bottom: 1.2rem;
    transition: box-shadow 0.3s;
}
.glass-card:hover { box-shadow: var(--shadow-lg); }
.glass-card h4 { color: var(--dark) !important; font-weight: 700; margin-bottom: 1rem; font-size: 1.05rem; }

/* ── Main area buttons ─────────────────────────────────────── */
.stMainBlockContainer .stColumns div[data-testid="stVerticalBlock"] .stButton > button {
    border-radius: var(--radius-md) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(.34,1.56,.64,1) !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #fff !important;
    color: #334155 !important;
    padding: 0.8rem 0.5rem !important;
    box-shadow: var(--shadow-sm) !important;
}
.stMainBlockContainer .stColumns div[data-testid="stVerticalBlock"] .stButton > button:hover {
    border-color: var(--c1) !important;
    background: var(--pale-green) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 25px rgba(45,106,79,0.12) !important;
}

/* ── Info Banner ───────────────────────────────────────────── */
.info-banner {
    background: linear-gradient(135deg, var(--pale-green), #E8F5E9);
    border: 1px solid rgba(45,106,79,0.15);
    border-radius: var(--radius-md);
    padding: 1rem 1.2rem; font-size: 0.88rem; color: #1B4332;
    display: flex; align-items: center; gap: 0.7rem;
    margin-bottom: 1rem; animation: fadeIn 0.6s ease-out;
}
.info-banner-icon { font-size: 1.3rem; }

/* ── Category Badges ───────────────────────────────────────── */
.cat-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 0.5rem; }
.cat-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 0.3rem 0.8rem; border-radius: 50px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.2px;
    animation: badgePop 0.4s cubic-bezier(.34,1.56,.64,1);
}
@keyframes badgePop { from { opacity:0; transform:scale(0.5); } to { opacity:1; transform:scale(1); } }
.cb-mental_health     { background: #D8F3DC; color: #1B4332; }
.cb-financial         { background: #FFE0B2; color: #BF360C; }
.cb-academic          { background: #BBDEFB; color: #0D47A1; }
.cb-housing           { background: #E1BEE7; color: #4A148C; }
.cb-general_wellbeing { background: #FFF9C4; color: #F57F17; }

.sent-badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 0.25rem 0.65rem; border-radius: 50px;
    font-size: 0.68rem; font-weight: 600;
    animation: badgePop 0.4s cubic-bezier(.34,1.56,.64,1) 0.15s both;
}
.sb-distressed { background: #FFCDD2; color: #B71C1C; }
.sb-worried    { background: #FFE0B2; color: #E65100; }
.sb-neutral    { background: #ECEFF1; color: #546E7A; }
.sb-positive   { background: #C8E6C9; color: #1B5E20; }

/* ── Crisis Banner ─────────────────────────────────────────── */
.crisis-box {
    background: linear-gradient(135deg, #FFEBEE, #FFCDD2);
    border-left: 5px solid #D32F2F;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    padding: 1rem 1.4rem; margin-bottom: 0.8rem;
    font-size: 0.88rem; color: #B71C1C; font-weight: 600;
    display: flex; align-items: center; gap: 0.6rem;
    animation: crisisPulse 2s ease-in-out infinite;
}
@keyframes crisisPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(211,47,47,0.2); }
    50%     { box-shadow: 0 0 0 8px rgba(211,47,47,0); }
}

/* ── Chat Messages ─────────────────────────────────────────── */
div[data-testid="stChatMessage"] {
    border-radius: var(--radius-lg) !important;
    border: 1px solid rgba(0,0,0,0.04) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.6rem !important;
    animation: msgIn 0.4s ease-out;
    background: #fff !important;
    color: #1E293B !important;
}
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] span:not(.cat-badge):not(.sent-badge),
div[data-testid="stChatMessage"] strong,
div[data-testid="stChatMessage"] a {
    color: #1E293B !important;
}
@keyframes msgIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
div[data-testid="stChatMessage"]:has(.stMarkdown) { line-height: 1.65; }

/* ── Typing Indicator ──────────────────────────────────────── */
.typing-dots {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 2px;
}
.typing-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #94A3B8;
    border-radius: 50%;
    animation: typing-bounce 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing-bounce {
    0%, 80%, 100% { transform: scale(0.55); opacity: 0.4; }
    40%           { transform: scale(1.0);  opacity: 1; }
}
[data-theme="dark"] .typing-dots span { background: #64748B; }

/* ── API Error Banner ──────────────────────────────────────── */
.api-error {
    background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
    border-left: 4px solid #F57C00;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0 0.8rem;
    font-size: 0.82rem;
    color: #BF360C;
}
[data-theme="dark"] .api-error {
    background: linear-gradient(135deg, rgba(245,124,0,0.18), rgba(245,124,0,0.08));
    color: #FFCC80;
}

/* ── Chat Input ────────────────────────────────────────────── */
div[data-testid="stChatInput"] { border-radius: var(--radius-lg) !important; overflow: hidden; }
div[data-testid="stChatInput"] textarea {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.92rem !important;
    border-radius: var(--radius-lg) !important;
}

/* ── Expander ──────────────────────────────────────────────── */
.stMainBlockContainer div[data-testid="stExpander"] {
    background: rgba(248,250,252,0.8) !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Divider & Footer ──────────────────────────────────────── */
.sep { height:1px; background:linear-gradient(90deg,transparent,#CBD5E1 50%,transparent); margin:1.5rem 0; }
.swsa-footer {
    text-align:center; padding:1.5rem 0 0.5rem;
    font-size:0.7rem; color:#94A3B8; letter-spacing:0.5px;
}

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#CBD5E1; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#94A3B8; }

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width:768px) {
    .swsa-letter { width:52px; height:52px; font-size:1.5rem; border-radius:14px; }
    .swsa-tagline { font-size:1rem; }
    .glass-card { padding:1.2rem 1rem; }
    .block-container { padding-left:1rem !important; padding-right:1rem !important; }
}

/* ═══════════════════════════════════════════════════════════════
   DARK MODE — automatically follows the user's OS preference via
   `prefers-color-scheme`. No JavaScript required.
   ═══════════════════════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {

    /* Main background */
    .stApp {
        background: linear-gradient(160deg, #0F172A 0%, #1E293B 40%, #1A1530 100%) !important;
        color: #E2E8F0;
    }

    /* Glass cards */
    .glass-card {
        background: rgba(30,41,59,0.80) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    }
    .glass-card h4 { color: #E2E8F0 !important; }

    /* Chat messages */
    div[data-testid="stChatMessage"] {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        color: #E2E8F0 !important;
    }
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] span:not(.cat-badge):not(.sent-badge),
    div[data-testid="stChatMessage"] strong,
    div[data-testid="stChatMessage"] a {
        color: #E2E8F0 !important;
    }

    /* Hero text */
    .swsa-desc { color: #64748B !important; }
    .swsa-tagline { color: #94A3B8 !important; }
    .fn-dot { color: #475569 !important; }
    .fn1 { color: var(--c1-light) !important; }
    .fn2 { color: var(--c2-light) !important; }
    .fn3 { color: var(--c3-light) !important; }
    .fn4 { color: var(--c4-light) !important; }

    /* Info banner */
    .info-banner {
        background: linear-gradient(135deg, rgba(45,106,79,0.2), rgba(45,106,79,0.1)) !important;
        border-color: rgba(82,183,136,0.25) !important;
        color: #A7F3D0 !important;
    }

    /* Main-area buttons */
    .stMainBlockContainer .stColumns div[data-testid="stVerticalBlock"] .stButton > button {
        background: rgba(30,41,59,0.70) !important;
        border: 1.5px solid rgba(255,255,255,0.10) !important;
        color: #E2E8F0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    }
    .stMainBlockContainer .stColumns div[data-testid="stVerticalBlock"] .stButton > button:hover {
        background: rgba(45,106,79,0.25) !important;
        border-color: var(--c1-light) !important;
        box-shadow: 0 8px 25px rgba(45,106,79,0.2) !important;
    }

    /* Category badges */
    .cb-mental_health     { background: rgba(45,106,79,0.3); color: #A7F3D0; }
    .cb-financial         { background: rgba(230,81,0,0.25);  color: #FFCC80; }
    .cb-academic          { background: rgba(21,101,192,0.3); color: #90CAF9; }
    .cb-housing           { background: rgba(123,31,162,0.3); color: #CE93D8; }
    .cb-general_wellbeing { background: rgba(245,127,23,0.25);color: #FFF176; }

    /* Sentiment badges */
    .sb-distressed { background: rgba(211,47,47,0.25); color: #EF9A9A; }
    .sb-worried    { background: rgba(230,81,0,0.25);  color: #FFCC80; }
    .sb-neutral    { background: rgba(255,255,255,0.08); color: #90A4AE; }
    .sb-positive   { background: rgba(45,106,79,0.25); color: #A5D6A7; }

    /* Crisis banner */
    .crisis-box {
        background: linear-gradient(135deg, rgba(211,47,47,0.15), rgba(211,47,47,0.08)) !important;
        border-left-color: #EF5350 !important;
        color: #EF9A9A !important;
    }

    /* Expander */
    .stMainBlockContainer div[data-testid="stExpander"] {
        background: rgba(30,41,59,0.5) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* Divider */
    .sep {
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1) 50%, transparent) !important;
    }

    /* Footer */
    .swsa-footer { color: #475569 !important; }

    /* Feature-row markdown */
    .stMainBlockContainer .stMarkdown p { color: #CBD5E1 !important; }
    .stMainBlockContainer .stMarkdown strong { color: #F1F5F9 !important; }

    /* Chat input */
    div[data-testid="stChatInput"] textarea {
        background: rgba(30,41,59,0.7) !important;
        color: #E2E8F0 !important;
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar-thumb { background: #334155; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
}
</style>
""", unsafe_allow_html=True)


#  DATABASE — bootstrap schema once per process
@st.cache_resource
def _bootstrap_db():
    try:
        init_db()
        return None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Database initialisation failed")
        return f"{type(exc).__name__}: {exc}"


_db_error = _bootstrap_db()
if _db_error:
    st.error(
        "We couldn't connect to the database. "
        "Sign-in and accounts won't work until this is fixed.\n\n"
        f"`{_db_error}`"
    )
    st.stop()


#  AUTH GATE — render login/signup screen until the user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    render_auth_page()
    st.stop()


#  SESSION STATE
if "agent" not in st.session_state:
    st.session_state.agent = MainAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started = False
if "mood" not in st.session_state:
    st.session_state.mood = None
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "categories_helped" not in st.session_state:
    st.session_state.categories_helped = set()
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = set()
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "mode" not in st.session_state:
    st.session_state.mode = "chat"  # 'chat' | 'study'


def _start_new_chat() -> None:
    """Reset session state to a blank chat (landing-page) view."""
    st.session_state.mode = "chat"
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.started = False
    st.session_state.mood = None
    st.session_state.interaction_count = 0
    st.session_state.categories_helped = set()
    st.session_state.feedback_given = set()
    st.session_state.agent = MainAgent()


def _load_conversation(conversation_id: int) -> None:
    """Replace session state with the messages from a saved conversation."""
    db_messages = get_messages(conversation_id)
    st.session_state.mode = "chat"
    st.session_state.conversation_id = conversation_id
    st.session_state.messages = db_messages
    st.session_state.started = True
    st.session_state.mood = None
    st.session_state.feedback_given = set()
    # Recompute the per-session metrics from the loaded history.
    st.session_state.interaction_count = sum(
        1 for m in db_messages if m["role"] == "user"
    )
    cats: set[str] = set()
    for m in db_messages:
        meta = m.get("metadata") or {}
        for c in meta.get("categories", []) or []:
            cats.add(c)
    st.session_state.categories_helped = cats
    # Replay history into a fresh agent so the LLM has context for the next turn.
    new_agent = MainAgent()
    for m in db_messages:
        if m["role"] in ("user", "assistant"):
            new_agent.conversation_history.append(
                {"role": m["role"], "content": m["content"]}
            )
    st.session_state.agent = new_agent


#  SIDEBAR
with st.sidebar:
    # Mini SWSA logo
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-row">
            <span class="sb-letter l1">S</span>
            <span class="sb-letter l2">W</span>
            <span class="sb-letter l3">S</span>
            <span class="sb-letter l4">A</span>
        </div>
        <div class="sb-tag">Student Welfare Support Agent</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    _user = st.session_state.user
    _display_name = _user.full_name or _user.username
    st.markdown(f"##### 👤 Signed in")
    st.markdown(f"**{_display_name}**  \n`@{_user.username}`")
    if st.button("🚪 Log out", use_container_width=True, key="logout_btn"):
        for _k in (
            "user",
            "agent",
            "messages",
            "started",
            "mood",
            "interaction_count",
            "categories_helped",
            "feedback_given",
            "conversation_id",
        ):
            st.session_state.pop(_k, None)
        st.rerun()

    # ── Study Tools ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📚 Study Tools")
    st.caption("Upload notes/PDFs → summary, key concepts, or quiz.")
    if st.button(
        "Open Study Tools",
        use_container_width=True,
        type="primary" if st.session_state.mode == "study" else "secondary",
        key="open_study_btn",
        disabled=st.session_state.mode == "study",
    ):
        st.session_state.mode = "study"
        st.rerun()

    # ── Conversations ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 💬 Conversations")
    if st.button(
        "➕ New chat", use_container_width=True, type="primary", key="new_chat_btn"
    ):
        _start_new_chat()
        st.rerun()

    _conversations = list_conversations(_user.id)
    if not _conversations:
        st.caption("No past conversations yet — start one below!")
    else:
        for _conv in _conversations:
            _is_active = _conv["id"] == st.session_state.conversation_id
            _bullet = "▸ " if _is_active else ""
            _col_open, _col_del = st.columns([5, 1])
            with _col_open:
                if st.button(
                    f"{_bullet}{_conv['title']}",
                    key=f"open_conv_{_conv['id']}",
                    use_container_width=True,
                    disabled=_is_active,
                ):
                    _load_conversation(_conv["id"])
                    st.rerun()
            with _col_del:
                if st.button(
                    "🗑",
                    key=f"del_conv_{_conv['id']}",
                    help="Delete this conversation",
                ):
                    delete_conversation(_conv["id"], _user.id)
                    if st.session_state.conversation_id == _conv["id"]:
                        _start_new_chat()
                    st.rerun()

    # ── Account settings ───────────────────────────────────────
    st.markdown("---")
    with st.expander("⚙️ Account settings"):
        with st.form("profile_form"):
            st.markdown("**Profile**")
            _new_full_name = st.text_input(
                "Full name", value=_user.full_name or "", key="settings_fullname"
            )
            _new_email = st.text_input(
                "Email", value=_user.email or "", key="settings_email"
            )
            if st.form_submit_button("Save profile"):
                _updated, _err = update_profile(
                    _user.id, full_name=_new_full_name, email=_new_email
                )
                if _err:
                    st.error(_err)
                else:
                    st.session_state.user = _updated
                    st.success("Profile updated.")
                    st.rerun()

        with st.form("password_form"):
            st.markdown("**Change password**")
            _curr_pw = st.text_input(
                "Current password", type="password", key="settings_curr_pw"
            )
            _new_pw = st.text_input(
                "New password", type="password", key="settings_new_pw"
            )
            _new_pw2 = st.text_input(
                "Confirm new password", type="password", key="settings_new_pw2"
            )
            if st.form_submit_button("Change password"):
                if _new_pw != _new_pw2:
                    st.error("New passwords don't match.")
                else:
                    _ok, _err = change_password(_user.id, _curr_pw, _new_pw)
                    if _err:
                        st.error(_err)
                    else:
                        st.success("Password updated.")

    st.markdown("---")

    st.markdown("##### 🔑 OpenAI API Key")
    api_key_input = st.text_input(
        "key", type="password",
        placeholder="Paste your API key here",
        help="Enables AI-powered responses. Without it, template mode is used.",
        label_visibility="collapsed",
        key="api_key_field",
    )
    if st.button("Activate AI ✅", use_container_width=True, type="primary", key="activate_btn"):
        if api_key_input and api_key_input.strip():
            config.OPENAI_API_KEY = api_key_input.strip()
            os.environ["OPENAI_API_KEY"] = api_key_input.strip()
            st.session_state.agent = MainAgent()
            st.rerun()
        else:
            st.warning("Please paste a key first.", icon="⚠️")
    # Also handle if key was already set previously
    if not config.OPENAI_API_KEY and api_key_input and api_key_input != config.OPENAI_API_KEY:
        config.OPENAI_API_KEY = api_key_input.strip()
        os.environ["OPENAI_API_KEY"] = api_key_input.strip()
        st.session_state.agent = MainAgent()
    if config.OPENAI_API_KEY:
        st.success("AI Mode Active", icon="✅")
    else:
        st.caption("Paste your key and click **Activate AI** to enable.")

    st.markdown("---")
    st.markdown("##### 📊 Your Session")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Messages", st.session_state.interaction_count)
    with c2:
        st.metric("Topics", len(st.session_state.categories_helped))

    st.markdown("---")
    st.markdown("##### 🏷️ Support Areas")
    cat_icons = {"mental_health": "💚", "financial": "💰", "academic": "📚", "housing": "🏠", "general_wellbeing": "🌟"}
    for key, label in CATEGORY_LABELS.items():
        mark = " ✓" if key in st.session_state.categories_helped else ""
        st.markdown(f"{cat_icons[key]}  {label}{mark}")

    st.markdown("---")
    with st.expander("🚨 Emergency Contacts"):
        st.markdown("""
**Samaritans** — 116 123 (24/7)\n
**Crisis Text** — Text SHOUT to 85258\n
**NHS Emergency** — 999\n
**NHS Non-Emergency** — 111\n
**Campus Security** — 0191 227 4500
""")

    st.markdown("---")
    st.caption("⚠️ S.W.S.A. provides guidance only. Not a substitute for professional help. In emergencies call 999.")


#  HELPERS
CAT_BADGE_ICONS = {
    "mental_health": "💚", "financial": "💰",
    "academic": "📚", "housing": "🏠", "general_wellbeing": "🌟",
}

def render_badges(metadata):
    if not metadata:
        return
    cats = metadata.get("categories", [])
    sentiment = metadata.get("sentiment", "")
    if not cats and not sentiment:
        return
    parts = []
    for c in cats:
        label = CATEGORY_LABELS.get(c, c)
        icon = CAT_BADGE_ICONS.get(c, "")
        parts.append(f'<span class="cat-badge cb-{c}">{icon} {label}</span>')
    if sentiment and sentiment != "neutral":
        slabel = {"distressed": "😟 Distressed", "worried": "😰 Worried", "positive": "😊 Positive"}.get(sentiment, sentiment)
        parts.append(f'<span class="sent-badge sb-{sentiment}">{slabel}</span>')
    st.markdown(f'<div class="cat-badges">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_crisis():
    st.markdown(
        '<div class="crisis-box">'
        '<span style="font-size:1.3rem">⚠️</span>'
        "I've noticed you may be in distress. Your safety is the top priority. "
        "Please reach out to a crisis service immediately."
        "</div>",
        unsafe_allow_html=True,
    )


st.markdown(
    '<div id="swsa-top"></div>'
    '<img src="" onerror="'
    "var t=document.getElementById(\'swsa-top\');"
    "if(t){t.scrollIntoView({behavior:\'instant\'});}"
    "setTimeout(function(){if(t){t.scrollIntoView({behavior:\'instant\'});}},150);"
    "setTimeout(function(){if(t){t.scrollIntoView({behavior:\'instant\'});}},400);"
    '" style="display:none">',
    unsafe_allow_html=True,
)

#  HERO LOGO — S.W.S.A.
st.markdown("""
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
    <div class="swsa-desc">AI-Powered Student Welfare Support</div>
</div>
""", unsafe_allow_html=True)


#  STUDY TOOLS MODE — render the document-upload page instead of the chat
if st.session_state.mode == "study":
    render_study_tools()
    st.stop()


#  LANDING PAGE
if not st.session_state.started:

    st.markdown(
        '<div class="swsa-tagline">Your well-being matters. Tell us how you\'re feeling '
        '— we\'ll help you find the right support.</div>',
        unsafe_allow_html=True,
    )

    # ── Step 1: Mood Check-In (only if not answered yet) ────
    if not st.session_state.mood:
        st.markdown('<div class="glass-card"><h4>How are you feeling right now?</h4>', unsafe_allow_html=True)
        mood_cols = st.columns(5)
        moods = [("😊", "Good"), ("😐", "Okay"), ("😟", "Worried"), ("😢", "Upset"), ("😰", "Struggling")]
        for i, (emoji, label) in enumerate(moods):
            with mood_cols[i]:
                if st.button(f"{emoji}\n{label}", key=f"mood_{label}", use_container_width=True):
                    st.session_state.mood = label
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Step 2: Show mood response + topic cards (after mood selected) ──
    if st.session_state.mood:
        mood_msgs = {
            "Good":      ("😊", "Great to hear! Feel free to explore services or ask anything."),
            "Okay":      ("👋", "Thanks for checking in. I'm here if anything's on your mind."),
            "Worried":   ("💛", "I'm sorry you're worried. Let me help you find the right support."),
            "Upset":     ("💙", "I'm sorry you're having a tough time. You've come to the right place."),
            "Struggling": ("🤝", "I'm glad you reached out. Let's find help together — you're not alone."),
        }
        icon, msg = mood_msgs.get(st.session_state.mood, ("💬", "Thanks for sharing."))
        st.markdown(
            f'<div class="info-banner"><span class="info-banner-icon">{icon}</span>{msg}</div>',
            unsafe_allow_html=True,
        )

        # ── Quick Action Cards (only after mood is selected) ──
        st.markdown('<div class="glass-card"><h4>What do you need help with?</h4>', unsafe_allow_html=True)

        actions = [
            ("💚", "Mental Health",    "Stress, anxiety, loneliness, burnout",    "I'm feeling really stressed and anxious lately"),
            ("💰", "Money Worries",    "Rent, debt, budgeting, jobs",            "I'm struggling financially and can't afford my expenses"),
            ("📚", "Academic Help",    "Exams, deadlines, essays, extensions",   "I'm falling behind on my coursework and need help"),
            ("🏠", "Housing Issues",   "Landlord, repairs, finding a flat",      "I'm having problems with my accommodation"),
            ("🌟", "General Wellbeing","Health, relationships, fitting in",      "I feel isolated and need someone to talk to"),
            ("🆘", "Urgent Support",   "Crisis help, immediate assistance",      "I need urgent help right now"),
        ]

        r1 = st.columns(3)
        r2 = st.columns(3)
        cols = r1 + r2
        for i, (icon, title, desc, prompt) in enumerate(actions):
            with cols[i]:
                if st.button(f"{icon}\n**{title}**\n{desc}", key=f"qa_{title}", use_container_width=True):
                    st.session_state.started = True
                    st.session_state.pending_input = prompt
                    st.session_state.messages = []
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat input on landing page
        user_input_landing = st.chat_input("Or just type what's on your mind...")
        if user_input_landing:
            st.session_state.started = True
            st.session_state.messages = []
            st.session_state.pending_input = user_input_landing
            st.rerun()

    # ── Features Strip (always visible) ─────────────────────
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("**🔒 Confidential**\n\nYour conversations are private and secure.")
    with f2:
        st.markdown("**🤖 AI-Powered**\n\nSmart classification and personalised guidance.")
    with f3:
        st.markdown("**⚡ Instant**\n\nGet recommendations in seconds, 24/7.")
    with f4:
        st.markdown("**🎯 Accurate**\n\nMatched to real university services and resources.")

    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="swsa-footer">Built with care for students, by students. '
        '<strong>S.W.S.A.</strong> — Student Welfare Support Agent</div>',
        unsafe_allow_html=True,
    )


#  CHAT MODE
else:

    # ── Render history ──────────────────────────────────────
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🛡️"):
                metadata = msg.get("metadata")
                render_badges(metadata)
                if metadata and metadata.get("is_crisis"):
                    render_crisis()
                st.markdown(msg["content"])
                if metadata and metadata.get("api_error"):
                    st.markdown(
                        f'<div class="api-error">⚠️ <strong>AI mode unavailable</strong> — '
                        f'showing template response. Reason: {metadata["api_error"]}</div>',
                        unsafe_allow_html=True,
                    )

                # Feedback row
                if metadata and metadata.get("categories"):
                    fb_key = f"fb_{idx}"
                    if fb_key not in st.session_state.feedback_given:
                        fc1, fc2, fc3, _ = st.columns([2.5, 0.8, 0.8, 3])
                        with fc1:
                            st.caption("Was this helpful?")
                        with fc2:
                            if st.button("👍", key=f"up_{idx}"):
                                st.session_state.feedback_given.add(fb_key)
                                st.rerun()
                        with fc3:
                            if st.button("👎", key=f"dn_{idx}"):
                                st.session_state.feedback_given.add(fb_key)
                                st.session_state.pending_input = "I'd like different recommendations please."
                                st.rerun()
                    else:
                        st.caption("✅ Thank you for your feedback!")

                if metadata and metadata.get("sub_agents_used"):
                    with st.expander("🔍 Sub-agents consulted"):
                        for a in metadata["sub_agents_used"]:
                            st.markdown(f"• {a}")
        else:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(msg["content"])

    # ── Input handling ──────────────────────────────────────
    pending = st.session_state.pop("pending_input", None)
    user_input = st.chat_input("Tell S.W.S.A. what's on your mind...")
    active_input = user_input or pending

    if active_input:
        # Create a conversation row on the user's first message of this chat,
        # and use that message as the auto-title.
        if st.session_state.conversation_id is None:
            st.session_state.conversation_id = create_conversation(
                user_id=st.session_state.user.id,
                first_user_message=active_input,
            )
        elif not st.session_state.messages:
            # Defensive: conversation exists but has no messages yet (e.g. created
            # then session resumed). Use this message as the title.
            update_title(st.session_state.conversation_id, active_input)

        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(active_input)
        st.session_state.messages.append({"role": "user", "content": active_input, "metadata": None})
        add_message(st.session_state.conversation_id, "user", active_input)

        with st.chat_message("assistant", avatar="🛡️"):
            stream = st.session_state.agent.process_message_stream(active_input)

            # Typing indicator while the classifier OpenAI call runs
            classify_typing = st.empty()
            classify_typing.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            metadata = next(stream)
            classify_typing.empty()

            render_badges(metadata)
            if metadata.get("is_crisis"):
                render_crisis()

            # Typing indicator while the sub-agent waits for first token
            response_typing = st.empty()
            response_typing.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )

            def _clear_typing_on_first_chunk(src, ph):
                cleared = False
                for chunk in src:
                    if not cleared:
                        ph.empty()
                        cleared = True
                    yield chunk
                if not cleared:
                    ph.empty()

            full_response = st.write_stream(_clear_typing_on_first_chunk(stream, response_typing))

            # If any sub-agent fell back to its template, show a warning
            api_error = getattr(st.session_state.agent, "last_api_error", None)
            if api_error:
                st.markdown(
                    f'<div class="api-error">⚠️ <strong>AI mode unavailable</strong> — '
                    f'showing template response. Reason: {api_error}</div>',
                    unsafe_allow_html=True,
                )

            st.session_state.interaction_count += 1
            for c in metadata.get("categories", []):
                st.session_state.categories_helped.add(c)

            if metadata.get("sub_agents_used"):
                with st.expander("🔍 Sub-agents consulted"):
                    for a in metadata["sub_agents_used"]:
                        st.markdown(f"• {a}")

        # Persist API-error state into the saved message so it survives reruns
        msg_metadata = dict(metadata)
        if api_error:
            msg_metadata["api_error"] = api_error
        st.session_state.messages.append({
            "role": "assistant", "content": full_response, "metadata": msg_metadata,
        })
        add_message(
            st.session_state.conversation_id,
            "assistant",
            full_response,
            msg_metadata,
        )
        st.rerun()
