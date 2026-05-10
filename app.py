"""S.W.S.A. Streamlit web application."""

import logging
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx

import config
from config import CATEGORY_LABELS
from agents.main_agent import MainAgent
from auth import (
    SESSION_COOKIE_NAME,
    SESSION_DAYS,
    create_session,
    delete_session,
    get_session_user,
)
from auth.admin import is_admin
from auth.ui import render_auth_page
from admin.ui import render_admin_panel
from account.ui import render_account_page
from showcase.ui import render_showcase
from db import init_db, is_persistent_db, is_running_on_railway
from db.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_messages,
    list_conversations,
    update_title,
)
from community.ui import render_community_page
from study.extractor import build_augmented_message, extract_attachments
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

/* ── Hide Streamlit chrome (but KEEP the header — it holds the
       sidebar collapse/expand chevron) ─────────────────────────── */
#MainMenu, footer,
.stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] { display: none !important; }

/* Make the header itself transparent so it doesn't visually intrude,
   but the sidebar toggle button inside it stays clickable. */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: auto !important;
}

/* ── Native sidebar — let Streamlit handle collapse/expand itself.
   We only style what's INSIDE the sidebar, never hide it or override
   the toggle. Streamlit'''s built-in chevron is the toggle. */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    background: linear-gradient(180deg, #1B2A3D 0%, #0F1923 100%) !important;
}

/* Restore a visible header bar so the native chevron has contrast */
header[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.92) !important;
    height: 3rem !important;
    min-height: 3rem !important;
    z-index: 99 !important;
    backdrop-filter: saturate(180%) blur(10px) !important;
    border-bottom: 1px solid rgba(15, 23, 42, 0.08) !important;
}
@media (prefers-color-scheme: dark) {
    header[data-testid="stHeader"] {
        background: rgba(15, 23, 42, 0.92) !important;
        border-bottom-color: rgba(255, 255, 255, 0.08) !important;
    }
}

/* Hide Streamlit's native sidebar chevron + collapsed-control entirely.
   Our own Streamlit-button toggle (rendered in Python) is the only
   way to hide / show the sidebar. */
button[kind="header"],
button[kind="headerNoPadding"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="baseButton-headerNoPadding"] {
    display: none !important;
    visibility: hidden !important;
}

/* Style the "Show sidebar" button when it's the only widget at top
   of main area (when sidebar is hidden). */
.st-key-swsa-show-sb-wrap button {
    background: #ffffff !important;
    color: #1B2A3D !important;
    border: 1px solid rgba(15, 23, 42, 0.14) !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.9rem !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    width: auto !important;
    min-width: 130px !important;
}
.st-key-swsa-show-sb-wrap button:hover {
    background: #F8FAFC !important;
    border-color: rgba(15, 23, 42, 0.22) !important;
}
@media (prefers-color-scheme: dark) {
    .st-key-swsa-show-sb-wrap button {
        background: #1E293B !important;
        color: #F1F5F9 !important;
        border-color: rgba(255, 255, 255, 0.10) !important;
    }
}

section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] strong { color: #F1F5F9 !important; }

section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #CBD5E1 !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 9px !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.12) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
    color: #F1F5F9 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button:disabled {
    background: linear-gradient(135deg, #2D6A4F, #52B788) !important;
    color: #ffffff !important;
    border: none !important;
    opacity: 1 !important;
}

/* ── Sub-nav for chat mode (conversations dropdown + new chat) ── */
.st-key-swsa-chat-subnav {
    margin: 0 0 1rem 0 !important;
    padding: 0.5rem 0 !important;
}
.st-key-swsa-chat-subnav [data-testid="stSelectbox"] label { display: none; }

/* ── Mobile (< 768px) ──────────────────────────────────────────
   Don't fight Streamlit's native mobile sidebar — it already
   works as a slide-in drawer. We only need to make the toggle
   button visible (the rest of our CSS makes the header transparent
   which hides it) and shrink the hero a bit for small screens. */
@media (max-width: 767px) {
    /* Sidebar toggle is handled by our universal floating button —
       no header bar / native-toggle CSS needed here. Just shrink the
       hero typography so the page fits a phone. */
    .swsa-letter { width: 48px !important; height: 48px !important; font-size: 1.4rem !important; border-radius: 12px !important; }
    .swsa-full-name { font-size: 0.65rem !important; gap: 0.3rem !important; letter-spacing: 1.5px !important; }
    .swsa-tagline { font-size: 0.95rem !important; }
    .glass-card { padding: 1rem !important; border-radius: 14px !important; }
    div[data-testid="stChatMessage"] { padding: 0.8rem 1rem !important; }

    /* Showcase hero typography fits a phone */
    .sc-headline { font-size: 1.9rem !important; line-height: 1.1 !important; }
    .sc-subhead { font-size: 0.95rem !important; }
    .sc-section-h { font-size: 1.4rem !important; }
}

/* (mobile dark-mode header tweak removed; no longer needed since the
   header isn't being styled per-mobile any more) */

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

/* Sidebar greeting line — sits between logo and nav buttons */
.sb-greeting {
    color: #E2E8F0 !important;
    font-size: 0.9rem;
    padding: 0.35rem 0 0.6rem;
    text-align: center;
}
.sb-greeting strong { color: #F1F5F9 !important; font-weight: 600; }

/* Tighten sidebar spacing — Streamlit's defaults leave huge gaps */
section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem; }
section[data-testid="stSidebar"] hr {
    margin: 0.9rem 0 !important;
    border-color: rgba(255,255,255,0.07) !important;
}
section[data-testid="stSidebar"] .stButton { margin-bottom: 0.3rem; }

/* Make sure zero-size component iframes (used for scroll-to-top etc.)
   never visibly flash. Streamlit normally wraps them in a full-width
   block; force the wrapper to collapse too. */
iframe[height="0"], iframe[width="0"] {
    border: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
}
div[data-testid="stIFrame"]:has(iframe[height="0"]),
div.stCustomComponentV1:has(iframe[height="0"]) {
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Hide Streamlit's "Press Enter to submit form" / "Press Enter to apply"
   helper text that auto-appears under text_inputs. Visual noise that
   nobody asked for. */
[data-testid="InputInstructions"],
[data-testid="stWidgetInstructions"],
.stTextInput div[data-testid="stTextInput"] + div small,
.stTextInput small[data-testid*="Instructions"] {
    display: none !important;
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


#  SCROLL-TO-TOP — invisible iframe whose body content is forced to 0×0
components.html(
    """<!doctype html><html><head><style>
html,body{margin:0;padding:0;height:0;width:0;border:0;overflow:hidden;background:transparent;}
</style></head><body>
<script>
(function() {
  try {
    var win = window.parent || window;
    var doc = win.document;
    var scroller = doc.scrollingElement || doc.documentElement || doc.body;
    var go = function() {
      try { win.scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
      if (scroller && typeof scroller.scrollTo === 'function') {
        try { scroller.scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
      }
    };
    go();
    setTimeout(go, 80);
    setTimeout(go, 250);
  } catch(e) {}
})();
</script>
</body></html>""",
    height=0,
    width=0,
)


# (Sidebar toggle removed — replaced by the top nav bar below.)


#  DATABASE — bootstrap schema once per process
@st.cache_resource
def _bootstrap_db():
    try:
        init_db()
        from auth.admin import bootstrap_admin_from_env
        from db.emergency import seed_defaults_if_empty as seed_emergency
        from db.groups import seed_from_config_if_empty

        bootstrap_admin_from_env()
        seed_from_config_if_empty()
        seed_emergency()
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

# Loud warning if running on Railway with an ephemeral SQLite fallback —
# every account / message will be wiped on the next redeploy. This catches
# the "Postgres add-on exists but isn't linked to the web service" case.
if is_running_on_railway() and not is_persistent_db():
    st.error(
        "⚠️ **Ephemeral storage warning** — this service is running on "
        "Railway but no `DATABASE_URL` is set, so it's using a local "
        "SQLite file that will be **wiped on every redeploy**. "
        "All accounts, conversations, and quiz history will be lost.\n\n"
        "**Fix:** in Railway → your web service → Variables → "
        "**Add Reference** → pick the Postgres service → `DATABASE_URL`."
    )


#  COOKIE-BACKED SESSION — keep the user logged in across page refreshes.
# CookieManager is itself a Streamlit component, so it must NOT be wrapped
# in @st.cache_resource. The `key` argument handles dedup across reruns.
cookies = stx.CookieManager(key="swsa_cookie_mgr")
_session_token = cookies.get(SESSION_COOKIE_NAME)

# extra-streamlit-components loads cookies asynchronously: on the very
# first render after a page refresh (F5), .get(...) returns None even
# if the cookie exists, then a few hundred ms later the component
# triggers a rerun with the real value. Without bridging this gap the
# user briefly sees the auth/showcase screen on every refresh — looks
# like a forced logout. Show a branded splash instead and wait for the
# next rerun, where cookies will be loaded.
if (
    "user" not in st.session_state or st.session_state.user is None
) and not _session_token and not st.session_state.get(
    "_cookie_load_attempted", False
):
    st.session_state._cookie_load_attempted = True
    st.markdown(
        """
        <div style="
            display:flex;align-items:center;justify-content:center;
            min-height:70vh;flex-direction:column;color:#64748B;
            font-family:'Plus Jakarta Sans',sans-serif;">
            <div style="display:inline-flex;gap:8px;margin-bottom:1rem;">
                <span style="width:48px;height:48px;border-radius:14px;
                    background:linear-gradient(145deg,#2D6A4F,#52B788);
                    display:inline-flex;align-items:center;justify-content:center;
                    color:white;font-weight:800;font-size:1.4rem;">S</span>
                <span style="width:48px;height:48px;border-radius:14px;
                    background:linear-gradient(145deg,#1565C0,#42A5F5);
                    display:inline-flex;align-items:center;justify-content:center;
                    color:white;font-weight:800;font-size:1.4rem;">W</span>
                <span style="width:48px;height:48px;border-radius:14px;
                    background:linear-gradient(145deg,#7B1FA2,#BA68C8);
                    display:inline-flex;align-items:center;justify-content:center;
                    color:white;font-weight:800;font-size:1.4rem;">S</span>
                <span style="width:48px;height:48px;border-radius:14px;
                    background:linear-gradient(145deg,#E65100,#FF9800);
                    display:inline-flex;align-items:center;justify-content:center;
                    color:white;font-weight:800;font-size:1.4rem;">A</span>
            </div>
            <div style="font-size:0.9rem;letter-spacing:0.5px;">Loading your space…</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# Now session_state.user might be None (no cookie OR cookie invalid).
# If a cookie exists, restore the user from the DB.
if (
    "user" not in st.session_state or st.session_state.user is None
) and _session_token:
    _restored = get_session_user(_session_token)
    if _restored is not None:
        st.session_state.user = _restored


#  AUTH GATE — render login/signup screen until the user is logged in.
# Unauthenticated visitors see a marketing showcase first; clicking
# "Get Started" sets `showcase_dismissed=True` so they fall through to
# the actual auth form.
if "user" not in st.session_state or st.session_state.user is None:
    if not st.session_state.get("showcase_dismissed", False):
        render_showcase()
        st.stop()
    render_auth_page()
    st.stop()


# User is logged in. If the browser doesn't have a session cookie yet
# (fresh login flow), issue one and store the token in the cookie.
if not _session_token:
    _new_token = create_session(st.session_state.user.id)
    cookies.set(
        SESSION_COOKIE_NAME,
        _new_token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    )
    _session_token = _new_token


#  MAINTENANCE MODE — admins always pass, everyone else sees a splash.
from db.settings import get_announcement, is_maintenance_mode  # noqa: E402

if is_maintenance_mode() and not is_admin(st.session_state.user):
    st.markdown(
        """
<div style="text-align:center;padding:6rem 2rem">
    <h1 style="font-size:3rem">🛠️ Just a moment…</h1>
    <p style="font-size:1.2rem;color:#475569;max-width:540px;margin:1rem auto">
        S.W.S.A. is temporarily offline for maintenance. We'll be back
        very soon — please try again in a few minutes.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()


#  ANNOUNCEMENT BANNER — admin-controlled, shown to everyone.
_announcement = get_announcement()
if _announcement:
    _sev = _announcement["severity"]
    _palette = {
        "info":    ("#DBEAFE", "#1E3A8A", "#60A5FA", "ℹ️"),
        "warning": ("#FEF3C7", "#92400E", "#F59E0B", "⚠️"),
        "urgent":  ("#FEE2E2", "#991B1B", "#EF4444", "🚨"),
    }.get(_sev, ("#DBEAFE", "#1E3A8A", "#60A5FA", "ℹ️"))
    _bg, _fg, _border, _emoji = _palette
    st.markdown(
        f"""
<div style="
    background: {_bg};
    color: {_fg};
    border-left: 4px solid {_border};
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0 0 0.75rem 0;
    font-size: 0.92rem;
    line-height: 1.5;
">
    <strong>{_emoji} Announcement:</strong> {_announcement['text']}
</div>
""",
        unsafe_allow_html=True,
    )


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
    st.session_state.mode = "chat"  # 'chat' | 'study' | 'admin' | 'settings' | 'community'


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


#  SIDEBAR — toggled by our own Streamlit buttons (Streamlit's
#  native chevron is hidden via CSS because it was unreliable).
#  State lives in st.session_state.sb_hidden.
_user = st.session_state.user
_display_name = _user.full_name or _user.username
_mode = st.session_state.mode

from db.settings import is_feature_enabled  # noqa: E402
from db.emergency import list_contacts as _list_emergency  # noqa: E402

if "sb_hidden" not in st.session_state:
    st.session_state.sb_hidden = False

# When hidden, force the native sidebar off-screen and render a
# "☰ Show sidebar" button at the top of the main area.
if st.session_state.sb_hidden:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="swsa-show-sb-wrap"):
        if st.button("☰ Show sidebar", key="swsa_show_sb_btn"):
            st.session_state.sb_hidden = False
            st.rerun()

with st.sidebar:
    # Hide-sidebar button at the very top of the sidebar
    if st.button(
        "× Hide sidebar",
        key="swsa_hide_sb_btn",
        use_container_width=True,
    ):
        st.session_state.sb_hidden = True
        st.rerun()

    st.markdown(
        """
        <div style="display:inline-flex;gap:5px;align-items:center;
                    padding:0.4rem 0 0.6rem;justify-content:center;width:100%;">
            <span style="width:36px;height:36px;border-radius:9px;
                background:linear-gradient(145deg,#2D6A4F,#52B788);
                display:inline-flex;align-items:center;justify-content:center;
                color:#fff;font-weight:800;font-size:1.05rem;">S</span>
            <span style="width:36px;height:36px;border-radius:9px;
                background:linear-gradient(145deg,#1565C0,#42A5F5);
                display:inline-flex;align-items:center;justify-content:center;
                color:#fff;font-weight:800;font-size:1.05rem;">W</span>
            <span style="width:36px;height:36px;border-radius:9px;
                background:linear-gradient(145deg,#7B1FA2,#BA68C8);
                display:inline-flex;align-items:center;justify-content:center;
                color:#fff;font-weight:800;font-size:1.05rem;">S</span>
            <span style="width:36px;height:36px;border-radius:9px;
                background:linear-gradient(145deg,#E65100,#FF9800);
                display:inline-flex;align-items:center;justify-content:center;
                color:#fff;font-weight:800;font-size:1.05rem;">A</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='text-align:center;padding-bottom:0.5rem;font-size:0.88rem;'>"
        f"👋 Hi, <strong>{_display_name}</strong></div>",
        unsafe_allow_html=True,
    )

    _items: list[tuple[str, str, str]] = [("chat", "💬", "Chat")]
    if is_feature_enabled("study_tools"):
        _items.append(("study", "📚", "Study Tools"))
    if is_feature_enabled("community"):
        _items.append(("community", "🌐", "Community"))
    _items.append(("settings", "⚙️", "Account"))
    if is_admin(_user):
        _items.append(("admin", "🛠️", "Admin"))

    for _target_mode, _icon, _label in _items:
        if st.button(
            f"{_icon}  {_label}",
            use_container_width=True,
            type="primary" if _mode == _target_mode else "secondary",
            key=f"nav_link_{_target_mode}",
            disabled=_mode == _target_mode,
        ):
            st.session_state.mode = _target_mode
            st.rerun()

    st.markdown("---")

    with st.expander("🚨 Emergency contacts"):
        _contacts = _list_emergency(active_only=True)
        if _contacts:
            st.markdown(
                "  \n".join(
                    f"**{c['label']}** — {c['value']}" for c in _contacts
                )
            )
        else:
            st.caption("No emergency contacts configured.")

    if st.button("🚪 Log out", key="logout_btn", use_container_width=True):
        delete_session(_session_token)
        try:
            cookies.delete(SESSION_COOKIE_NAME)
        except Exception:
            pass
        for _k in (
            "user", "agent", "messages", "started", "mood",
            "interaction_count", "categories_helped", "feedback_given",
            "conversation_id", "mode", "study", "sb_collapsed",
        ):
            st.session_state.pop(_k, None)
        st.rerun()

    st.caption(
        "⚠️ Guidance only — not a substitute for professional help. "
        "In emergencies call 999."
    )

#  CHAT-MODE SUB-NAV: + New chat button + Conversations dropdown
if _mode == "chat":
    with st.container(key="swsa-chat-subnav"):
        _conv_col, _new_col = st.columns([5, 2])
        with _conv_col:
            _conversations = list_conversations(_user.id)
            if _conversations:
                _options = [("__none__", "— Pick a past conversation —")] + [
                    (str(c["id"]), c["title"]) for c in _conversations
                ]
                _option_keys = [k for k, _ in _options]
                _option_labels = {k: v for k, v in _options}
                _current_id = (
                    str(st.session_state.conversation_id)
                    if st.session_state.conversation_id
                    else "__none__"
                )
                _current_idx = (
                    _option_keys.index(_current_id)
                    if _current_id in _option_keys
                    else 0
                )
                _picked = st.selectbox(
                    "Conversations",
                    _option_keys,
                    index=_current_idx,
                    format_func=lambda k: _option_labels[k],
                    label_visibility="collapsed",
                    key="conv_picker",
                )
                if _picked != "__none__" and _picked != _current_id:
                    _load_conversation(int(_picked))
                    st.rerun()
            else:
                st.caption("No past conversations yet.")
        with _new_col:
            if st.button(
                "➕ New chat",
                use_container_width=True,
                key="new_chat_btn",
                type="primary",
            ):
                _start_new_chat()
                st.rerun()

        # Delete-current-conversation control (small, only when a
        # conversation is loaded)
        if st.session_state.conversation_id is not None:
            _del_col_l, _del_col_r = st.columns([6, 1])
            with _del_col_r:
                if st.button(
                    "🗑",
                    key="del_current_conv_btn",
                    help="Delete this conversation",
                ):
                    delete_conversation(
                        st.session_state.conversation_id, _user.id
                    )
                    _start_new_chat()
                    st.rerun()


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


#  HERO LOGO — S.W.S.A.
# Only render the hero in chat mode. Admin / Study / Community / Settings
# pages all have their own headings, so the hero just wastes vertical space.
if st.session_state.mode == "chat":
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


#  ADMIN MODE — render the admin panel (gated server-side, not just by sidebar)
if st.session_state.mode == "admin":
    if not is_admin(st.session_state.user):
        st.error("You don't have admin access.")
        st.session_state.mode = "chat"
        st.stop()
    render_admin_panel()
    st.stop()


#  ACCOUNT SETTINGS MODE — full-page profile + password page
if st.session_state.mode == "settings":
    render_account_page()
    st.stop()


#  COMMUNITY MODE — student-run WhatsApp support groups
if st.session_state.mode == "community":
    render_community_page()
    st.stop()


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

        # Chat input on landing page
        user_input_landing = st.chat_input("Tell S.W.S.A. what's on your mind…")
        if user_input_landing:
            st.session_state.started = True
            st.session_state.messages = []
            st.session_state.pending_input = user_input_landing
            st.rerun()

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
                _user_meta = msg.get("metadata") or {}
                _attachments = _user_meta.get("attachments") or []
                if _attachments:
                    st.caption(" ".join(f"📎 `{n}`" for n in _attachments))

    # ── Input handling ──────────────────────────────────────
    pending = st.session_state.pop("pending_input", None)
    from db.settings import is_feature_enabled as _ff_enabled  # noqa: E402

    if _ff_enabled("file_upload"):
        chat_value = st.chat_input(
            "Tell S.W.S.A. what's on your mind…",
            accept_file="multiple",
            file_type=["pdf", "docx", "txt", "md"],
        )
    else:
        chat_value = st.chat_input("Tell S.W.S.A. what's on your mind…")

    # chat_input with accept_file returns None or a ChatInputValue
    # (with .text and .files). Pending strings (from feedback buttons /
    # the landing page) don't carry files.
    text_in = ""
    files_in: list = []
    if chat_value is not None:
        text_in = (getattr(chat_value, "text", "") or "").strip()
        files_in = list(getattr(chat_value, "files", []) or [])
    if not text_in and not files_in and pending:
        text_in = str(pending).strip()

    if text_in or files_in:
        # Pull readable text out of any attached files
        extracted_docs, doc_errors = extract_attachments(files_in)
        for err in doc_errors:
            st.warning(f"📎 {err}")

        # What the user sees in their bubble (+ filename chips)
        display_text = text_in or "(see attached document)"
        attachment_names = [name for name, _ in extracted_docs]

        # What the AI actually receives (display_text + extracted doc text)
        ai_input = build_augmented_message(text_in, extracted_docs)

        user_metadata: dict | None = None
        if attachment_names:
            user_metadata = {"attachments": attachment_names}

        # Create a conversation row on the user's first message of this chat,
        # and use that message as the auto-title.
        title_seed = text_in or (
            f"Document: {attachment_names[0]}" if attachment_names else "New conversation"
        )
        if st.session_state.conversation_id is None:
            st.session_state.conversation_id = create_conversation(
                user_id=st.session_state.user.id,
                first_user_message=title_seed,
            )
        elif not st.session_state.messages:
            update_title(st.session_state.conversation_id, title_seed)

        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(display_text)
            if attachment_names:
                chips = " ".join(f"📎 `{n}`" for n in attachment_names)
                st.caption(chips)
        st.session_state.messages.append(
            {"role": "user", "content": display_text, "metadata": user_metadata}
        )
        add_message(
            st.session_state.conversation_id,
            "user",
            display_text,
            user_metadata,
        )

        with st.chat_message("assistant", avatar="🛡️"):
            stream = st.session_state.agent.process_message_stream(ai_input)

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
