"""Support Advisor Sub-Agent — handles general wellbeing and cross-cutting concerns."""

from core.recommendation import get_services_for_categories


class SupportAdvisorAgent:
    """Sub-agent for general wellbeing and cases that span multiple categories."""

    def __init__(self):
        self.category = "general_wellbeing"

    def get_empathy_message(self, user_input: str) -> str:
        """Select an appropriate empathetic opening based on the concern."""
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["international", "visa", "home country", "abroad"]):
            return (
                "Being an international student comes with unique challenges. "
                "The university has dedicated support to help you settle in and thrive."
            )
        if any(w in text_lower for w in ["discriminat", "harass", "bully", "racist", "hate"]):
            return (
                "I'm sorry you've experienced this. No one should face discrimination or harassment. "
                "There are confidential services available to support you and address what happened."
            )
        if any(w in text_lower for w in ["health", "ill", "doctor", "GP", "sick"]):
            return (
                "I hope you're okay. Your physical health is important, and the university has health services "
                "that can help. Let me share some options with you."
            )
        return (
            "Thank you for reaching out. Whatever you're going through, there are people and services "
            "here to support you. Let's find the right help together."
        )

    def get_recommendations(self) -> list[dict]:
        """Retrieve general wellbeing services."""
        return get_services_for_categories([self.category])

    def get_wellbeing_tips(self) -> list[str]:
        """Provide general wellbeing advice."""
        return [
            "Stay connected — reach out to friends, classmates, or student societies.",
            "Regular physical activity, even a short walk, can boost your mood.",
            "Maintain a routine with regular meals, sleep, and study patterns.",
            "Take breaks — stepping away from work helps you return more focused.",
            "Explore the university's clubs and societies to meet new people.",
        ]

    def process(self, user_input: str) -> dict:
        """Process a general wellbeing concern and return structured guidance."""
        return {
            "agent": "Support Advisor Sub-Agent",
            "empathy_message": self.get_empathy_message(user_input),
            "services": self.get_recommendations(),
            "wellbeing_tips": self.get_wellbeing_tips(),
        }
