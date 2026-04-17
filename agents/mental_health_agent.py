"""Mental health sub-agent."""

from core.recommendation import get_crisis_resources, get_services_for_categories


EMPATHY_RESPONSES = {
    "stress": "It's completely understandable to feel stressed, especially during demanding academic periods.",
    "anxiety": "Anxiety can feel overwhelming, but please know that many students experience this and support is available.",
    "depression": "I'm sorry you're feeling this way. Depression is a real and valid experience, and you deserve support.",
    "loneliness": "Feeling lonely can be really tough, especially if you're away from home. You're not alone in feeling this way.",
    "overwhelmed": "It sounds like you have a lot on your plate right now. Let's look at what support is available to help you manage.",
    "default": "Thank you for sharing how you're feeling. It takes courage to reach out, and I want to help you find the right support.",
}


class MentalHealthAgent:
    """Sub-agent specialising in mental health support and guidance."""

    def __init__(self):
        self.category = "mental_health"

    def get_empathy_message(self, user_input: str) -> str:
        """Select an appropriate empathetic opening based on keywords."""
        text_lower = user_input.lower()
        for keyword, message in EMPATHY_RESPONSES.items():
            if keyword in text_lower:
                return message
        return EMPATHY_RESPONSES["default"]

    def get_recommendations(self) -> list[dict]:
        """Retrieve mental health services."""
        return get_services_for_categories([self.category])

    def get_crisis_info(self) -> list[dict]:
        """Retrieve crisis resources for urgent situations."""
        return get_crisis_resources()

    def get_self_help_tips(self, concern: str) -> list[str]:
        """Provide general self-help suggestions based on the concern type."""
        tips = {
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
        text_lower = concern.lower()
        for key, advice in tips.items():
            if key in text_lower:
                return advice
        return tips["default"]

    def process(self, user_input: str) -> dict:
        """Process a mental health concern and return structured guidance."""
        return {
            "agent": "Mental Health Sub-Agent",
            "empathy_message": self.get_empathy_message(user_input),
            "services": self.get_recommendations(),
            "self_help_tips": self.get_self_help_tips(user_input),
        }
