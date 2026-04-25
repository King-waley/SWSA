"""Mental health sub-agent — calls ChatGPT directly."""

import logging

import config
from config import SUB_AGENT_PROMPTS, SYSTEM_PROMPT
from core.recommendation import (
    format_crisis_context,
    format_services_context,
    get_crisis_resources,
    get_services_for_categories,
)

from agents._llm import stream_openai_response

logger = logging.getLogger(__name__)


EMPATHY_RESPONSES = {
    "stress": "It's completely understandable to feel stressed, especially during demanding academic periods.",
    "anxiety": "Anxiety can feel overwhelming, but please know that many students experience this and support is available.",
    "depression": "I'm sorry you're feeling this way. Depression is a real and valid experience, and you deserve support.",
    "loneliness": "Feeling lonely can be really tough, especially if you're away from home. You're not alone in feeling this way.",
    "overwhelmed": "It sounds like you have a lot on your plate right now. Let's look at what support is available to help you manage.",
    "default": "Thank you for sharing how you're feeling. It takes courage to reach out, and I want to help you find the right support.",
}

SELF_HELP_TIPS = {
    "stress": [
        "Try breaking large tasks into smaller, manageable steps.",
        "Practice deep breathing exercises — even 5 minutes can help.",
        "Make time for activities you enjoy, even briefly.",
        "Consider attending a university wellbeing workshop on stress management.",
    ],
    "anxiety": [
        "Grounding techniques (5-4-3-2-1 senses exercise) can help in anxious moments.",
        "Limit caffeine intake, which can heighten anxiety symptoms.",
        "Try to maintain a regular sleep schedule.",
        "Write down your worries — sometimes getting them on paper helps reduce their power.",
    ],
    "sleep": [
        "Try to keep a consistent bedtime and wake time.",
        "Avoid screens for 30 minutes before bed.",
        "Create a calming bedtime routine.",
        "The university health centre can help if sleep problems persist.",
    ],
    "default": [
        "Regular physical activity can significantly improve mental wellbeing.",
        "Stay connected with friends, family, or support groups.",
        "The university's Togetherall platform offers free 24/7 peer support.",
        "Remember that seeking professional help is a positive step.",
    ],
}


class MentalHealthAgent:
    """Sub-agent that calls ChatGPT for mental-health concerns."""

    category = "mental_health"
    label = "Mental Health Sub-Agent"

    def _build_system_message(self, is_crisis: bool, sentiment: str, summary: str) -> str:
        sub_prompt = SUB_AGENT_PROMPTS[self.category]
        services_ctx = format_services_context(get_services_for_categories([self.category]))

        crisis_section = ""
        if is_crisis:
            crisis_section = (
                "\n\n⚠️ CRISIS DETECTED — IMMEDIATELY provide these crisis contacts FIRST, "
                "before any other recommendations. Express genuine concern for the student's safety:\n"
                + format_crisis_context(get_crisis_resources())
            )

        sentiment_hint = ""
        if sentiment == "distressed":
            sentiment_hint = "\nThe student appears emotionally distressed — lead with empathy and validation."
        elif sentiment == "worried":
            sentiment_hint = "\nThe student seems worried — be reassuring and solution-oriented."

        summary_hint = f"\nCore concern identified: {summary}" if summary else ""

        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- Your Role ---\n{sub_prompt}"
            f"{sentiment_hint}{summary_hint}{crisis_section}\n\n"
            f"--- Mental Health Services Available ---\n{services_ctx}"
        )

    def process_stream(
        self,
        user_input: str,
        conversation_history: list[dict] | None = None,
        is_crisis: bool = False,
        sentiment: str = "neutral",
        summary: str = "",
    ):
        """Stream a ChatGPT response. Falls back to canned content if no API key / API fails."""
        if config.OPENAI_API_KEY:
            try:
                system_message = self._build_system_message(is_crisis, sentiment, summary)
                yield from stream_openai_response(system_message, user_input, conversation_history)
                return
            except Exception as e:
                logger.warning("Mental health sub-agent OpenAI call failed: %s", e)
        yield self._fallback_response(user_input, is_crisis)

    def process(
        self,
        user_input: str,
        conversation_history: list[dict] | None = None,
        is_crisis: bool = False,
        sentiment: str = "neutral",
        summary: str = "",
    ) -> dict:
        """Non-streaming wrapper. Collects the full streamed response."""
        chunks = list(
            self.process_stream(
                user_input,
                conversation_history=conversation_history,
                is_crisis=is_crisis,
                sentiment=sentiment,
                summary=summary,
            )
        )
        return {"agent": self.label, "response": "".join(chunks)}

    def _fallback_response(self, user_input: str, is_crisis: bool) -> str:
        """Template response used when ChatGPT is unavailable."""
        text_lower = user_input.lower()

        empathy = EMPATHY_RESPONSES["default"]
        for keyword, message in EMPATHY_RESPONSES.items():
            if keyword in text_lower:
                empathy = message
                break

        tips = SELF_HELP_TIPS["default"]
        for key, advice in SELF_HELP_TIPS.items():
            if key in text_lower:
                tips = advice
                break

        parts = []
        if is_crisis:
            parts.append("**Please reach out to one of these services right now:**")
            for r in get_crisis_resources():
                parts.append(f"- **{r['name']}** — {r['phone']} ({r['available']})")
            parts.append("")

        parts.append(empathy)
        parts.append("")

        services = get_services_for_categories([self.category])
        if services:
            parts.append("**Services that can help:**")
            for s in services[:3]:
                parts.append(f"- **{s['name']}** — {s.get('description', '')}")
                if s.get("phone"):
                    parts.append(f"  Phone: {s['phone']}")
            parts.append("")

        parts.append("**Self-help tips:**")
        for t in tips:
            parts.append(f"- {t}")

        return "\n".join(parts)
