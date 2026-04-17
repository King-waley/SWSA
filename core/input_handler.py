"""Input handling and validation."""

import re


def preprocess_input(user_input: str) -> str:
    """Clean and normalise user input text."""
    text = user_input.strip()
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def validate_input(user_input: str) -> tuple[bool, str]:
    """Check that input is usable. Returns (is_valid, error_message)."""
    if not user_input or not user_input.strip():
        return False, "Please type a message so I can help you."
    if len(user_input.strip()) < 2:
        return False, "Could you tell me a bit more about what you need help with?"
    if len(user_input.strip()) > 2000:
        return False, "Your message is quite long. Could you summarise your main concern?"
    return True, ""


def detect_crisis(user_input: str) -> bool:
    """Detect if the student's message indicates a potential crisis situation."""
    crisis_terms = [
        r"\bsuicid\w*\b",
        r"\bself[- ]?harm\w*\b",
        r"\bkill\s+(myself|me)\b",
        r"\bend\s+(my\s+)?life\b",
        r"\bdon'?t\s+want\s+to\s+live\b",
        r"\bwant\s+to\s+die\b",
        r"\bhurt\s+myself\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bgiving\s+up\b",
    ]
    text_lower = user_input.lower()
    for pattern in crisis_terms:
        if re.search(pattern, text_lower):
            return True
    return False
