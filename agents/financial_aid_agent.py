"""Financial Aid Sub-Agent — handles financial concerns and support."""

from core.recommendation import get_external_resources, get_services_for_categories


class FinancialAidAgent:
    """Sub-agent specialising in financial support and guidance."""

    def __init__(self):
        self.category = "financial"

    def get_empathy_message(self, user_input: str) -> str:
        """Select an appropriate empathetic opening based on financial concern."""
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["urgent", "emergency", "desperate", "can't pay"]):
            return (
                "I understand you're in a difficult financial situation right now. "
                "There are emergency support options available — let's look at what can help immediately."
            )
        if any(w in text_lower for w in ["job", "work", "employment", "part-time"]):
            return (
                "Finding the right job alongside your studies can be challenging. "
                "Let me point you to some useful resources."
            )
        return (
            "Financial worries are very common among students, and there's no shame in seeking support. "
            "Let's explore what help is available to you."
        )

    def get_recommendations(self) -> list[dict]:
        """Retrieve financial support services."""
        return get_services_for_categories([self.category])

    def get_job_platforms(self) -> list[dict]:
        """Retrieve external job search platforms."""
        resources = get_external_resources([self.category])
        return resources.get("job_platforms", [])

    def get_budgeting_tips(self) -> list[str]:
        """Provide practical budgeting advice for students."""
        return [
            "Track your spending for a week to understand where your money goes.",
            "Check if you're eligible for student discounts (NUS/TOTUM card, UNiDAYS).",
            "Look into student bank accounts with interest-free overdrafts.",
            "The university's financial support team can do a full benefits check for you.",
            "Check eligibility for the university Hardship Fund for emergency costs.",
        ]

    def process(self, user_input: str) -> dict:
        """Process a financial concern and return structured guidance."""
        return {
            "agent": "Financial Aid Sub-Agent",
            "empathy_message": self.get_empathy_message(user_input),
            "services": self.get_recommendations(),
            "job_platforms": self.get_job_platforms(),
            "budgeting_tips": self.get_budgeting_tips(),
        }
