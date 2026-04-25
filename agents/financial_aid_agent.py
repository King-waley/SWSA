"""Financial aid sub-agent — calls ChatGPT directly."""

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


BUDGETING_TIPS = [
    "Track your spending for a week to understand where your money goes.",
    "Check if you're eligible for student discounts (NUS/TOTUM card, UNiDAYS).",
    "Look into student bank accounts with interest-free overdrafts.",
    "The university's financial support team can do a full benefits check for you.",
    "Check eligibility for the university Hardship Fund for emergency costs.",
]


class FinancialAidAgent:
    """Sub-agent that calls ChatGPT for financial concerns."""

    category = "financial"
    label = "Financial Aid Sub-Agent"

    def _build_system_message(self, sentiment: str, summary: str) -> str:
        sub_prompt = SUB_AGENT_PROMPTS[self.category]
        services_ctx = format_services_context(get_services_for_categories([self.category]))
        external_ctx = format_external_context(get_external_resources([self.category]))

        sentiment_hint = ""
        if sentiment == "distressed":
            sentiment_hint = "\nThe student appears emotionally distressed about money — be reassuring."
        elif sentiment == "worried":
            sentiment_hint = "\nThe student seems worried — emphasise that financial stress is common and help is available."

        summary_hint = f"\nCore concern identified: {summary}" if summary else ""

        sections = [
            f"{SYSTEM_PROMPT}",
            "",
            f"--- Your Role ---\n{sub_prompt}{sentiment_hint}{summary_hint}",
            "",
            f"--- Financial Services Available ---\n{services_ctx}",
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
        """Stream a ChatGPT response. Falls back to template if no API key / API fails."""
        if config.OPENAI_API_KEY:
            try:
                system_message = self._build_system_message(sentiment, summary)
                yield from stream_openai_response(system_message, user_input, conversation_history)
                return
            except Exception as e:
                logger.warning("Financial aid sub-agent OpenAI call failed: %s", e)
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
            "Financial worries are very common among students, and there's no shame in seeking support. "
            "Let's explore what help is available to you.",
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
        job_platforms = external.get("job_platforms", [])
        if job_platforms:
            parts.append("**Job platforms:**")
            for j in job_platforms:
                parts.append(f"- [{j['name']}]({j['url']}) — {j.get('description', '')}")
            parts.append("")

        parts.append("**Budgeting tips:**")
        for t in BUDGETING_TIPS:
            parts.append(f"- {t}")

        return "\n".join(parts)
