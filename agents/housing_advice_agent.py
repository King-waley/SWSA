"""Housing advice sub-agent — calls ChatGPT directly."""

import logging

import config
from config import SUB_AGENT_PROMPTS, SYSTEM_PROMPT
from core.recommendation import (
    format_external_context,
    format_services_context,
    get_external_resources,
    get_services_for_categories,
)

from agents._llm import stream_openai_response

logger = logging.getLogger(__name__)


HOUSING_TIPS = [
    "Always read your tenancy agreement carefully before signing.",
    "Take dated photos of the property when you move in to protect your deposit.",
    "Know your rights — landlords must provide a safe, habitable property.",
    "The Students' Union Advice Service offers free, independent housing advice.",
    "If you're looking for private housing, start your search early (Jan-Mar for September).",
]


class HousingAdviceAgent:
    """Sub-agent that calls ChatGPT for housing concerns."""

    category = "housing"
    label = "Housing Advice Sub-Agent"

    def _build_system_message(self, sentiment: str, summary: str) -> str:
        sub_prompt = SUB_AGENT_PROMPTS[self.category]
        services_ctx = format_services_context(get_services_for_categories([self.category]))
        external_ctx = format_external_context(get_external_resources([self.category]))

        sentiment_hint = ""
        if sentiment == "distressed":
            sentiment_hint = "\nThe student appears emotionally distressed about housing — acknowledge feelings before practical steps."
        elif sentiment == "worried":
            sentiment_hint = "\nThe student seems worried — be reassuring and action-oriented."

        summary_hint = f"\nCore concern identified: {summary}" if summary else ""

        sections = [
            f"{SYSTEM_PROMPT}",
            "",
            f"--- Your Role ---\n{sub_prompt}{sentiment_hint}{summary_hint}",
            "",
            f"--- Housing Services Available ---\n{services_ctx}",
        ]
        if external_ctx:
            sections.extend(["", external_ctx])

        return "\n".join(sections)

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
                logger.warning("Housing advice sub-agent OpenAI call failed: %s", e)
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
            "Housing concerns can really affect your wellbeing and studies. "
            "Let's look at what support and resources are available to help.",
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

        external = get_external_resources([self.category])
        platforms = external.get("housing_platforms", [])
        if platforms:
            parts.append("**Housing platforms:**")
            for p in platforms:
                parts.append(f"- [{p['name']}]({p['url']}) — {p.get('description', '')}")
            parts.append("")

        parts.append("**Housing tips:**")
        for t in HOUSING_TIPS:
            parts.append(f"- {t}")

        return "\n".join(parts)
