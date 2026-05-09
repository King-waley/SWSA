"""Streamlit page for the Study Tools feature."""

from __future__ import annotations

import logging

import streamlit as st

import config
from study.extractor import extract_text
from study.generator import (
    generate_key_concepts,
    generate_quiz,
    generate_summary,
)

logger = logging.getLogger(__name__)


# Default initial state for st.session_state.study
def _empty_state() -> dict:
    return {
        "document_name": None,
        "document_text": None,
        "active_tool": None,  # 'summary' | 'key_points' | 'quiz'
        "summary": None,
        "key_points": None,
        "quiz": None,
        "quiz_answers": {},
        "quiz_submitted": False,
        "error": None,
    }


def _reset_outputs(state: dict) -> None:
    """Clear generated outputs (called when a new document is uploaded)."""
    state["active_tool"] = None
    state["summary"] = None
    state["key_points"] = None
    state["quiz"] = None
    state["quiz_answers"] = {}
    state["quiz_submitted"] = False
    state["error"] = None


def _render_quiz(state: dict) -> None:
    quiz = state["quiz"] or []
    if not quiz:
        st.warning("Couldn't generate a quiz from this document. Try a longer file.")
        return

    if not state["quiz_submitted"]:
        st.markdown(f"### 🧠 Quiz — {len(quiz)} questions")
        st.caption("Pick the best answer for each, then submit at the bottom.")

        for idx, q in enumerate(quiz):
            st.markdown(f"**Q{idx + 1}. {q['question']}**")
            current = state["quiz_answers"].get(idx)
            choice = st.radio(
                f"q_{idx}",
                options=list(range(len(q["options"]))),
                format_func=lambda i, opts=q["options"]: opts[i],
                index=current if current is not None else None,
                key=f"quiz_q_{idx}",
                label_visibility="collapsed",
            )
            state["quiz_answers"][idx] = choice
            st.markdown("")  # spacing

        all_answered = all(state["quiz_answers"].get(i) is not None for i in range(len(quiz)))
        if st.button(
            "Submit answers",
            type="primary",
            use_container_width=True,
            disabled=not all_answered,
            help=None if all_answered else "Answer every question first.",
        ):
            state["quiz_submitted"] = True
            st.rerun()
        return

    # Submitted — show score + per-question breakdown
    correct = sum(
        1 for i, q in enumerate(quiz)
        if state["quiz_answers"].get(i) == q["correct_index"]
    )
    total = len(quiz)
    pct = correct / total * 100 if total else 0

    if pct >= 80:
        verdict = "🎉 Excellent — you've really got this."
    elif pct >= 60:
        verdict = "💪 Solid — a few gaps to revise."
    elif pct >= 40:
        verdict = "📚 Worth re-reading the parts you missed."
    else:
        verdict = "👀 This needs another pass — check the explanations below."

    st.markdown(f"### Score: {correct} / {total} ({pct:.0f}%)")
    st.markdown(verdict)
    st.markdown("---")

    for idx, q in enumerate(quiz):
        user_idx = state["quiz_answers"].get(idx)
        correct_idx = q["correct_index"]
        is_right = user_idx == correct_idx
        emoji = "✅" if is_right else "❌"

        st.markdown(f"{emoji} **Q{idx + 1}. {q['question']}**")
        for opt_idx, opt in enumerate(q["options"]):
            if opt_idx == correct_idx:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✓ **{opt}** *(correct answer)*")
            elif opt_idx == user_idx:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✗ ~~{opt}~~ *(your answer)*")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;○ {opt}")
        st.caption(f"💡 {q['explanation']}")
        st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔁 Retake this quiz", use_container_width=True):
            state["quiz_answers"] = {}
            state["quiz_submitted"] = False
            st.rerun()
    with col_b:
        if st.button("🆕 Generate a new quiz", use_container_width=True):
            with st.spinner("Generating new questions…"):
                try:
                    state["quiz"] = generate_quiz(state["document_text"], num_questions=5)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Quiz regenerate failed")
                    state["error"] = f"Couldn't generate a new quiz: {exc}"
            state["quiz_answers"] = {}
            state["quiz_submitted"] = False
            st.rerun()


def render_study_tools() -> None:
    """Render the Study Tools page in the main area."""
    if "study" not in st.session_state:
        st.session_state.study = _empty_state()
    state = st.session_state.study

    # Header + back-to-chat button
    col_title, col_back = st.columns([6, 2])
    with col_title:
        st.markdown("## 📚 Study Tools")
    with col_back:
        if st.button("← Back to chat", use_container_width=True, key="study_back_btn"):
            st.session_state.mode = "chat"
            st.rerun()

    st.caption(
        "Upload a PDF, DOCX, or TXT file and choose how you'd like to study it — "
        "summary, key concepts, or an interactive quiz."
    )

    if not config.OPENAI_API_KEY:
        st.warning(
            "⚠️ Study Tools need an OpenAI API key. Add yours in the sidebar or "
            "set `OPENAI_API_KEY` on the deployment to enable AI generation."
        )

    # Upload widget
    uploaded = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=False,
        key="study_uploader",
        help="Max 200 MB. Text-based files only.",
    )

    if uploaded is not None and uploaded.name != state.get("document_name"):
        with st.spinner(f"Reading {uploaded.name}…"):
            text, error = extract_text(uploaded)
        if error:
            st.error(error)
            return
        if not text or not text.strip():
            st.error(
                "Couldn't extract any readable text from this file. "
                "If it's a scanned PDF, you'll need an OCR'd version."
            )
            return
        state["document_name"] = uploaded.name
        state["document_text"] = text
        _reset_outputs(state)
        st.success(f"Loaded **{uploaded.name}** — {len(text):,} characters")

    if state["document_text"] is None:
        st.markdown("---")
        st.markdown("### What you can do")
        cols = st.columns(3)
        with cols[0]:
            st.markdown("#### 📝 Summary")
            st.caption("A 200-300 word overview of the main ideas, in plain prose.")
        with cols[1]:
            st.markdown("#### 🔑 Key Concepts")
            st.caption("5-10 important ideas extracted, each with a short explanation.")
        with cols[2]:
            st.markdown("#### 🧠 Quiz")
            st.caption("Five exam-style multiple-choice questions with instant feedback.")
        st.info("👆 Upload a document above to get started.")
        return

    # Document loaded — show tools
    char_count = len(state["document_text"])
    st.markdown(
        f"**Document:** `{state['document_name']}` &nbsp;·&nbsp; "
        f"{char_count:,} chars"
    )

    tool_cols = st.columns(3)
    with tool_cols[0]:
        if st.button(
            "📝 Summary",
            use_container_width=True,
            type="primary" if state["active_tool"] == "summary" else "secondary",
            key="tool_summary",
            disabled=not config.OPENAI_API_KEY,
        ):
            state["active_tool"] = "summary"
            if state["summary"] is None:
                with st.spinner("Summarising…"):
                    try:
                        state["summary"] = generate_summary(state["document_text"])
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Summary failed")
                        state["error"] = f"Couldn't generate summary: {exc}"
            st.rerun()
    with tool_cols[1]:
        if st.button(
            "🔑 Key Concepts",
            use_container_width=True,
            type="primary" if state["active_tool"] == "key_points" else "secondary",
            key="tool_keypoints",
            disabled=not config.OPENAI_API_KEY,
        ):
            state["active_tool"] = "key_points"
            if state["key_points"] is None:
                with st.spinner("Extracting key concepts…"):
                    try:
                        state["key_points"] = generate_key_concepts(state["document_text"])
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Key concepts failed")
                        state["error"] = f"Couldn't extract concepts: {exc}"
            st.rerun()
    with tool_cols[2]:
        if st.button(
            "🧠 Quiz me",
            use_container_width=True,
            type="primary" if state["active_tool"] == "quiz" else "secondary",
            key="tool_quiz",
            disabled=not config.OPENAI_API_KEY,
        ):
            state["active_tool"] = "quiz"
            if state["quiz"] is None:
                with st.spinner("Writing quiz questions…"):
                    try:
                        state["quiz"] = generate_quiz(state["document_text"], num_questions=5)
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Quiz failed")
                        state["error"] = f"Couldn't generate quiz: {exc}"
            state["quiz_answers"] = {}
            state["quiz_submitted"] = False
            st.rerun()

    if state.get("error"):
        st.error(state["error"])

    st.markdown("---")

    if state["active_tool"] == "summary" and state["summary"]:
        st.markdown("### 📝 Summary")
        st.markdown(state["summary"])
    elif state["active_tool"] == "key_points" and state["key_points"]:
        st.markdown("### 🔑 Key Concepts")
        for i, concept in enumerate(state["key_points"], 1):
            st.markdown(f"**{i}. {concept.get('title', '')}**")
            st.markdown(concept.get("explanation", ""))
            st.markdown("")
    elif state["active_tool"] == "quiz" and state["quiz"] is not None:
        _render_quiz(state)
    elif state["active_tool"] is None:
        st.info("Pick a tool above — Summary, Key Concepts, or Quiz.")
