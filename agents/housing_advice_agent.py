"""Housing Advice Sub-Agent — handles accommodation and housing concerns."""

from core.recommendation import get_external_resources, get_services_for_categories


class HousingAdviceAgent:
    """Sub-agent specialising in housing support and guidance."""

    def __init__(self):
        self.category = "housing"

    def get_empathy_message(self, user_input: str) -> str:
        """Select an appropriate empathetic opening based on housing concern."""
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["homeless", "nowhere to live", "kicked out", "evict"]):
            return (
                "I'm really sorry you're in this situation. Finding yourself without housing is incredibly stressful. "
                "There is emergency accommodation support available — let's get you help right away."
            )
        if any(w in text_lower for w in ["landlord", "dispute", "repair", "broken"]):
            return (
                "Dealing with housing issues can be very frustrating. "
                "Let me connect you with services that can advise you on your rights and next steps."
            )
        return (
            "Housing concerns can really affect your wellbeing and studies. "
            "Let's look at what support and resources are available to help."
        )

    def get_recommendations(self) -> list[dict]:
        """Retrieve housing support services."""
        return get_services_for_categories([self.category])

    def get_housing_platforms(self) -> list[dict]:
        """Retrieve external housing search platforms."""
        resources = get_external_resources([self.category])
        return resources.get("housing_platforms", [])

    def get_housing_tips(self) -> list[str]:
        """Provide practical housing advice for students."""
        return [
            "Always read your tenancy agreement carefully before signing.",
            "Take dated photos of the property when you move in to protect your deposit.",
            "Know your rights — landlords must provide a safe, habitable property.",
            "The Students' Union Advice Service offers free, independent housing advice.",
            "If you're looking for private housing, start your search early (Jan-Mar for September).",
        ]

    def process(self, user_input: str) -> dict:
        """Process a housing concern and return structured guidance."""
        return {
            "agent": "Housing Advice Sub-Agent",
            "empathy_message": self.get_empathy_message(user_input),
            "services": self.get_recommendations(),
            "housing_platforms": self.get_housing_platforms(),
            "housing_tips": self.get_housing_tips(),
        }
