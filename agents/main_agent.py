"""Main agent that routes queries to sub-agents (each calls ChatGPT directly)."""

from agents.academic_support_agent import AcademicSupportAgent
from agents.financial_aid_agent import FinancialAidAgent
from agents.housing_advice_agent import HousingAdviceAgent
from agents.mental_health_agent import MentalHealthAgent
from agents.support_advisor_agent import SupportAdvisorAgent
from config import CATEGORY_LABELS
from core.input_handler import detect_crisis, preprocess_input, validate_input
from core.issue_detector import classify_issue


# Cap how many sub-agents respond per turn to keep replies focused.
MAX_SUB_AGENTS_PER_TURN = 2


class MainAgent:
    """Orchestrator that delegates response generation to sub-agents."""

    def __init__(self):
        self.sub_agents = {
            "mental_health": MentalHealthAgent(),
            "financial": FinancialAidAgent(),
            "academic": AcademicSupportAgent(),
            "housing": HousingAdviceAgent(),
            "general_wellbeing": SupportAdvisorAgent(),
        }
        self.conversation_history: list[dict] = []
        self.last_api_error: str | None = None

    def reset_conversation(self):
        self.conversation_history = []
        self.last_api_error = None

    def _classify(self, cleaned_input: str) -> dict:
        """Run classification + crisis detection. Returns routing info."""
        classification = classify_issue(cleaned_input)
        categories = classification["categories"]
        is_crisis = classification["is_crisis"]

        if detect_crisis(cleaned_input):
            is_crisis = True

        if is_crisis and "mental_health" not in categories:
            categories.insert(0, "mental_health")

        return {
            "categories": categories,
            "is_crisis": is_crisis,
            "sentiment": classification.get("sentiment", "neutral"),
            "summary": classification.get("summary", ""),
        }

    def _select_sub_agents(self, categories: list[str]):
        """Return the (capped) list of (category, sub_agent) pairs to invoke."""
        selected = []
        for category in categories:
            agent = self.sub_agents.get(category)
            if agent:
                selected.append((category, agent))
            if len(selected) >= MAX_SUB_AGENTS_PER_TURN:
                break
        return selected

    def process_message_stream(self, user_input: str):
        """
        Process a student's message and stream the response.

        Yields: first a metadata dict, then text chunks from each sub-agent in turn.
        """
        is_valid, error_msg = validate_input(user_input)
        if not is_valid:
            yield {
                "categories": [],
                "is_crisis": False,
                "sentiment": "neutral",
                "sub_agents_used": [],
            }
            yield error_msg
            return

        cleaned_input = preprocess_input(user_input)
        self.last_api_error = None
        routing = self._classify(cleaned_input)
        selected = self._select_sub_agents(routing["categories"])

        yield {
            "categories": routing["categories"],
            "is_crisis": routing["is_crisis"],
            "sentiment": routing["sentiment"],
            "sub_agents_used": [agent.label for _, agent in selected],
        }

        full_response_parts: list[str] = []
        errors: list[str] = []
        for i, (category, agent) in enumerate(selected):
            if i > 0:
                separator = (
                    f"\n\n---\n\n### {CATEGORY_LABELS.get(category, category)}\n\n"
                )
                full_response_parts.append(separator)
                yield separator

            for chunk in agent.process_stream(
                cleaned_input,
                conversation_history=self.conversation_history,
                is_crisis=routing["is_crisis"],
                sentiment=routing["sentiment"],
                summary=routing["summary"],
            ):
                full_response_parts.append(chunk)
                yield chunk

            if agent.last_error:
                errors.append(f"{agent.label}: {agent.last_error}")

        if errors:
            self.last_api_error = " | ".join(errors)

        full_response = "".join(full_response_parts)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": full_response})

    def process_message(self, user_input: str) -> dict:
        """Non-streaming wrapper. Collects the full streamed response."""
        gen = self.process_message_stream(user_input)
        metadata = next(gen)
        response = "".join(gen)

        return {
            "response": response,
            "categories": metadata["categories"],
            "is_crisis": metadata["is_crisis"],
            "sentiment": metadata["sentiment"],
            "sub_agents_used": metadata["sub_agents_used"],
        }
