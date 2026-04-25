"""Academic support sub-agent — calls ChatGPT directly."""

import logging

import config
from config import SUB_AGENT_PROMPTS, SYSTEM_PROMPT
from core.recommendation import format_services_context, get_services_for_categories

from agents._llm import stream_openai_response

logger = logging.getLogger(__name__)


GENERAL_STUDY_TIPS = [
    "Speak to your Academic Personal Tutor for personalised guidance.",
    "The Study Skills team offers one-to-one and group support sessions.",
    "Use the library's research support for finding and evaluating sources.",
    "Check if you're eligible for mitigating circumstances or extensions.",
]


class AcademicSupportAgent:
    """Sub-agent that calls ChatGPT for academic concerns."""

    category = "academic"
    label = "Academic Support Sub-Agent"

    def _build_system_message(self, sentiment: str, summary: str) -> str:
        sub_prompt = SUB_AGENT_PROMPTS[self.category]
        services_ctx = format_services_context(get_services_for_categories([self.category]))

        sentiment_hint = ""
        if sentiment == "distressed":
            sentiment_hint = "\nThe student appears emotionally distressed about academics — acknowledge feelings before practical advice."
        elif sentiment == "worried":
            sentiment_hint = "\nThe student seems worried — be encouraging and solution-oriented."

        summary_hint = f"\nCore concern identified: {summary}" if summary else ""

        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- Your Role ---\n{sub_prompt}{sentiment_hint}{summary_hint}\n\n"
            f"--- Academic Services Available ---\n{services_ctx}"
        )

    def process_stream(
        self,
        user_input: str,
        conversation_history: list[dict] | None = None,
        is_crisis: bool = False,
        sentiment: str = "neutral",
        summary: str = "",
    ):
        if config.OPENAI_API_KEY:
            try:
                system_message = self._build_system_message(sentiment, summary)
                yield from stream_openai_response(system_message, user_input, conversation_history)
                return
            except Exception as e:
                logger.warning("Academic support sub-agent OpenAI call failed: %s", e)
        yield self._fallback_response()

    def process(
        self,
        user_input: str,
        conversation_history: list[dict] | None = None,
        is_crisis: bool = False,
        sentiment: str = "neutral",
        summary: str = "",
    ) -> dict:
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

    def _fallback_response(self) -> str:
        parts = [
            "Academic challenges are a normal part of university life. "
            "Let me help you find the support that suits your situation.",
            "",
        ]

        services = get_services_for_categories([self.category])
        if services:
            parts.append("**Services that can help:**")
            for s in services[:3]:
                parts.append(f"- **{s['name']}** — {s.get('description', '')}")
                if s.get("phone"):
                    parts.append(f"  Phone: {s['phone']}")
            parts.append("")

        parts.append("**Study tips:**")
        for t in GENERAL_STUDY_TIPS:
            parts.append(f"- {t}")

        return "\n".join(parts)
