"""Academic Support Sub-Agent — handles academic concerns and study issues."""

from core.recommendation import get_services_for_categories


class AcademicSupportAgent:
    """Sub-agent specialising in academic support and guidance."""

    def __init__(self):
        self.category = "academic"

    def get_empathy_message(self, user_input: str) -> str:
        """Select an appropriate empathetic opening based on academic concern."""
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["fail", "failing", "failed"]):
            return (
                "I understand you're worried about your academic performance. "
                "Many students face challenges, and there are support systems to help you get back on track."
            )
        if any(w in text_lower for w in ["deadline", "extension", "late"]):
            return (
                "Deadline pressure can feel intense. Let's look at what options are available to you, "
                "including extensions and mitigating circumstances."
            )
        if any(w in text_lower for w in ["dissertation", "thesis"]):
            return (
                "Working on a dissertation can feel overwhelming. "
                "Let's find the right support to help you through this important piece of work."
            )
        return (
            "Academic challenges are a normal part of university life. "
            "Let me help you find the support that suits your situation."
        )

    def get_recommendations(self) -> list[dict]:
        """Retrieve academic support services."""
        return get_services_for_categories([self.category])

    def get_study_tips(self, concern: str) -> list[str]:
        """Provide study advice based on the specific academic concern."""
        tips = {
            "time_management": [
                "Use a weekly planner to block out study time, breaks, and deadlines.",
                "Try the Pomodoro Technique — 25 minutes focused study, 5 minutes break.",
                "Prioritise tasks using the Eisenhower Matrix (urgent vs. important).",
                "Set realistic daily goals rather than overwhelming to-do lists.",
            ],
            "exam": [
                "Start revision early using spaced repetition techniques.",
                "Practice with past exam papers under timed conditions.",
                "Form study groups to discuss and test each other on key topics.",
                "Attend the Study Skills team's exam preparation workshops.",
            ],
            "writing": [
                "Start with an outline before writing — structure helps clarity.",
                "Use the university's referencing guide for your citation style.",
                "Book a session with Study Skills for feedback on your academic writing.",
                "Write first, edit later — don't aim for perfection in the first draft.",
            ],
            "default": [
                "Speak to your Academic Personal Tutor for personalised guidance.",
                "The Study Skills team offers one-to-one and group support sessions.",
                "Use the library's research support for finding and evaluating sources.",
                "Check if you're eligible for mitigating circumstances or extensions.",
            ],
        }
        text_lower = concern.lower()
        if any(w in text_lower for w in ["time", "manage", "organis", "procrastinat"]):
            return tips["time_management"]
        if any(w in text_lower for w in ["exam", "revision", "test"]):
            return tips["exam"]
        if any(w in text_lower for w in ["essay", "writing", "assignment", "coursework", "referenc"]):
            return tips["writing"]
        return tips["default"]

    def process(self, user_input: str) -> dict:
        """Process an academic concern and return structured guidance."""
        return {
            "agent": "Academic Support Sub-Agent",
            "empathy_message": self.get_empathy_message(user_input),
            "services": self.get_recommendations(),
            "study_tips": self.get_study_tips(user_input),
        }
