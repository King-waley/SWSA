"""Main Orchestrator Agent — routes student concerns to appropriate sub-agents."""

from agents.academic_support_agent import AcademicSupportAgent
from agents.financial_aid_agent import FinancialAidAgent
from agents.housing_advice_agent import HousingAdviceAgent
from agents.mental_health_agent import MentalHealthAgent
from agents.support_advisor_agent import SupportAdvisorAgent
from core.input_handler import detect_crisis, preprocess_input, validate_input
from core.issue_detector import classify_issue
from core.response_generator import generate_response, generate_response_stream


class MainAgent:
    """Orchestrator that coordinates sub-agents to handle student welfare queries."""

    def __init__(self):
        self.sub_agents = {
            "mental_health": MentalHealthAgent(),
            "financial": FinancialAidAgent(),
            "academic": AcademicSupportAgent(),
            "housing": HousingAdviceAgent(),
            "general_wellbeing": SupportAdvisorAgent(),
        }
        self.conversation_history: list[dict] = []

    def reset_conversation(self):
        """Clear conversation history for a new session."""
        self.conversation_history = []

    def _classify_and_route(self, cleaned_input: str) -> dict:
        """Classify the issue and route to sub-agents. Returns classification + sub-agent results."""
        # Classify using OpenAI (with function calling) or keyword fallback
        classification = classify_issue(cleaned_input)

        categories = classification["categories"]
        is_crisis = classification["is_crisis"]
        sentiment = classification.get("sentiment", "neutral")
        summary = classification.get("summary", "")

        # Also check crisis via keyword regex (safety net on top of OpenAI)
        if detect_crisis(cleaned_input):
            is_crisis = True

        # If crisis detected, ensure mental_health is in categories
        if is_crisis and "mental_health" not in categories:
            categories.insert(0, "mental_health")

        # Route to sub-agents and collect their outputs
        sub_agent_results = []
        for category in categories:
            agent = self.sub_agents.get(category)
            if agent:
                result = agent.process(cleaned_input)
                sub_agent_results.append(result)

        return {
            "categories": categories,
            "is_crisis": is_crisis,
            "sentiment": sentiment,
            "summary": summary,
            "sub_agent_results": sub_agent_results,
        }

    def process_message(self, user_input: str) -> dict:
        """
        Process a student's message through the full pipeline (non-streaming).
        Returns a dict with the response and metadata.
        """
        # Validate
        is_valid, error_msg = validate_input(user_input)
        if not is_valid:
            return {
                "response": error_msg,
                "categories": [],
                "is_crisis": False,
                "sentiment": "neutral",
                "sub_agents_used": [],
            }

        cleaned_input = preprocess_input(user_input)
        routing = self._classify_and_route(cleaned_input)

        # Generate final response
        response = generate_response(
            cleaned_input,
            routing["categories"],
            routing["is_crisis"],
            self.conversation_history,
            sentiment=routing["sentiment"],
            summary=routing["summary"],
        )

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})

        return {
            "response": response,
            "categories": routing["categories"],
            "is_crisis": routing["is_crisis"],
            "sentiment": routing["sentiment"],
            "sub_agents_used": [r["agent"] for r in routing["sub_agent_results"]],
            "sub_agent_details": routing["sub_agent_results"],
        }

    def process_message_stream(self, user_input: str):
        """
        Process a student's message and return a streaming generator.
        Yields: first a metadata dict, then text chunks.

        Usage:
            gen = agent.process_message_stream(msg)
            metadata = next(gen)    # dict with categories, is_crisis, etc.
            for chunk in gen:       # text chunks for streaming display
                display(chunk)
        """
        # Validate
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
        routing = self._classify_and_route(cleaned_input)

        # Yield metadata first so the UI can render badges/banners before streaming
        yield {
            "categories": routing["categories"],
            "is_crisis": routing["is_crisis"],
            "sentiment": routing["sentiment"],
            "sub_agents_used": [r["agent"] for r in routing["sub_agent_results"]],
        }

        # Stream the response chunks
        full_response_parts = []
        for chunk in generate_response_stream(
            cleaned_input,
            routing["categories"],
            routing["is_crisis"],
            self.conversation_history,
            sentiment=routing["sentiment"],
            summary=routing["summary"],
        ):
            full_response_parts.append(chunk)
            yield chunk

        # Update conversation history with the complete response
        full_response = "".join(full_response_parts)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": full_response})
