"""Response generation module — produces responses using OpenAI (streaming) or fallback."""

import logging

from openai import OpenAI

import config
from config import (
    CATEGORY_LABELS,
    OPENAI_RESPONSE_MODEL,
    SUB_AGENT_PROMPTS,
    SYSTEM_PROMPT,
)
from core.recommendation import (
    format_crisis_context,
    format_external_context,
    format_services_context,
    get_crisis_resources,
    get_external_resources,
    get_services_for_categories,
)

logger = logging.getLogger(__name__)


def build_context(categories: list[str], is_crisis: bool) -> str:
    """Build the knowledge-base context to inject into the prompt."""
    parts = []

    if is_crisis:
        crisis = get_crisis_resources()
        parts.append(format_crisis_context(crisis))

    services = get_services_for_categories(categories)
    parts.append(format_services_context(services))

    external = get_external_resources(categories)
    ext_text = format_external_context(external)
    if ext_text:
        parts.append(ext_text)

    return "\n".join(parts)


def _build_system_message(
    categories: list[str],
    is_crisis: bool,
    sentiment: str,
    summary: str,
) -> str:
    """Build a rich system message incorporating sub-agent prompts and context."""
    category_names = ", ".join(CATEGORY_LABELS.get(c, c) for c in categories)
    context = build_context(categories, is_crisis)

    # Combine relevant sub-agent instructions
    sub_agent_instructions = []
    for cat in categories:
        prompt = SUB_AGENT_PROMPTS.get(cat)
        if prompt:
            sub_agent_instructions.append(f"[{CATEGORY_LABELS.get(cat, cat)}]: {prompt}")

    sub_agent_block = "\n".join(sub_agent_instructions)

    crisis_directive = ""
    if is_crisis:
        crisis_directive = (
            "\n\n⚠️ CRISIS DETECTED — This student may be at risk. "
            "IMMEDIATELY provide the crisis/emergency contact numbers listed below FIRST, "
            "before any other recommendations. Express genuine concern for their safety. "
            "Encourage them to contact a crisis service right now.\n"
        )

    sentiment_hint = ""
    if sentiment == "distressed":
        sentiment_hint = "\nThe student appears emotionally distressed — lead with empathy and validation before recommendations."
    elif sentiment == "worried":
        sentiment_hint = "\nThe student seems worried — be reassuring and solution-oriented."

    summary_hint = ""
    if summary:
        summary_hint = f"\nCore concern identified: {summary}"

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- Classification ---\n"
        f"Categories: {category_names}\n"
        f"Sentiment: {sentiment}{sentiment_hint}{summary_hint}"
        f"{crisis_directive}\n\n"
        f"--- Sub-Agent Instructions ---\n"
        f"{sub_agent_block}\n\n"
        f"--- Available Services & Resources ---\n"
        f"{context}"
    )


# ── OpenAI streaming response ─────────────────────────────────────

def generate_response_openai_stream(
    user_message: str,
    categories: list[str],
    is_crisis: bool,
    sentiment: str,
    summary: str,
    conversation_history: list[dict],
):
    """
    Generate a streaming response using OpenAI. Yields text chunks.
    Use this with Streamlit's st.write_stream() for real-time output.
    """
    system_message = _build_system_message(categories, is_crisis, sentiment, summary)

    messages = [{"role": "system", "content": system_message}]
    messages.extend(conversation_history[-20:])
    messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    stream = client.chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ── OpenAI non-streaming response ─────────────────────────────────

def generate_response_openai(
    user_message: str,
    categories: list[str],
    is_crisis: bool,
    sentiment: str,
    summary: str,
    conversation_history: list[dict],
) -> str:
    """Generate a complete response using OpenAI (non-streaming)."""
    system_message = _build_system_message(categories, is_crisis, sentiment, summary)

    messages = [{"role": "system", "content": system_message}]
    messages.extend(conversation_history[-20:])
    messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
    )
    return response.choices[0].message.content


# ── Template-based fallback ────────────────────────────────────────

def generate_response_fallback(
    user_message: str,
    categories: list[str],
    is_crisis: bool,
) -> str:
    """Generate a response without an API — uses template-based approach."""
    parts = []

    if is_crisis:
        parts.append(
            "I can see you're going through a really difficult time, and I want you to know "
            "that help is available right now.\n\n"
            "**Please reach out to one of these services immediately:**\n"
        )
        crisis = get_crisis_resources()
        for r in crisis:
            parts.append(f"- **{r['name']}** — {r['phone']} ({r['available']})")
        parts.append(
            "\n\nYou are not alone, and speaking to someone can make a real difference. "
            "These services are free, confidential, and available right now."
        )
        parts.append("\n\n---\n")

    category_names = [CATEGORY_LABELS.get(c, c) for c in categories]
    parts.append(
        f"Based on what you've shared, it sounds like you may benefit from support in: "
        f"**{', '.join(category_names)}**.\n\n"
        f"Here are some services that can help:\n"
    )

    services = get_services_for_categories(categories)
    for s in services[:5]:
        parts.append(f"\n**{s['name']}**")
        parts.append(f"{s['description']}")
        if s.get("phone"):
            parts.append(f"Phone: {s['phone']}")
        if s.get("booking"):
            parts.append(f"How to access: {s['booking']}")

    external = get_external_resources(categories)
    if external:
        parts.append("\n\n**You might also find these helpful:**")
        for key, items in external.items():
            for item in items:
                parts.append(f"- [{item['name']}]({item['url']}): {item['description']}")

    parts.append(
        "\n\nRemember, seeking help is a sign of strength. "
        "Would you like more details about any of these services?"
    )

    return "\n".join(parts)


# ── Main entry points ─────────────────────────────────────────────

def generate_response(
    user_message: str,
    categories: list[str],
    is_crisis: bool,
    conversation_history: list[dict],
    sentiment: str = "neutral",
    summary: str = "",
) -> str:
    """Generate a complete response (non-streaming). Falls back to templates if no API key."""
    if config.OPENAI_API_KEY:
        try:
            return generate_response_openai(
                user_message, categories, is_crisis, sentiment, summary, conversation_history
            )
        except Exception as e:
            logger.warning("OpenAI response failed, using fallback: %s", e)
    return generate_response_fallback(user_message, categories, is_crisis)


def generate_response_stream(
    user_message: str,
    categories: list[str],
    is_crisis: bool,
    conversation_history: list[dict],
    sentiment: str = "neutral",
    summary: str = "",
):
    """
    Generate a streaming response. Yields text chunks when OpenAI is available,
    otherwise yields the full fallback response as a single chunk.
    """
    if config.OPENAI_API_KEY:
        try:
            yield from generate_response_openai_stream(
                user_message, categories, is_crisis, sentiment, summary, conversation_history
            )
            return
        except Exception as e:
            logger.warning("OpenAI stream failed, using fallback: %s", e)
    # Fallback: yield full response as one chunk
    yield generate_response_fallback(user_message, categories, is_crisis)
# Response Generation Module
