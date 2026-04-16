"""Issue detection module — classifies student concerns using OpenAI or keyword fallback."""

import json
import logging

from openai import OpenAI

from config import (
    CATEGORY_KEYWORDS,
    CLASSIFY_TOOLS,
    CLASSIFIER_SYSTEM_PROMPT,
    ISSUE_CATEGORIES,
    OPENAI_API_KEY,
    OPENAI_CLASSIFIER_MODEL,
)

logger = logging.getLogger(__name__)


# ── OpenAI-powered classification ──────────────────────────────────

def classify_issue_openai(user_input: str) -> dict:
    """
    Use OpenAI function calling to classify the student's concern.
    Returns a structured dict with categories, is_crisis, sentiment, and summary.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_CLASSIFIER_MODEL,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        tools=CLASSIFY_TOOLS,
        tool_choice={"type": "function", "function": {"name": "classify_student_concern"}},
        temperature=0.1,  # Low temperature for consistent classification
        max_tokens=200,
    )

    # Extract the function call arguments
    tool_call = response.choices[0].message.tool_calls[0]
    result = json.loads(tool_call.function.arguments)

    # Validate categories
    valid_categories = set(ISSUE_CATEGORIES)
    result["categories"] = [c for c in result["categories"] if c in valid_categories]
    if not result["categories"]:
        result["categories"] = ["general_wellbeing"]

    return result


# ── Keyword-based fallback classification ──────────────────────────

def detect_issues_keyword(user_input: str) -> dict[str, float]:
    """Score each category based on keyword matches. Returns {category: score}."""
    text_lower = user_input.lower()
    scores: dict[str, float] = {cat: 0.0 for cat in ISSUE_CATEGORIES}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                scores[category] += 1.0

    # Normalise so the highest score = 1.0
    max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0
    return {cat: round(score / max_score, 2) for cat, score in scores.items()}


def get_top_categories(scores: dict[str, float], threshold: float = 0.3) -> list[str]:
    """Return categories whose scores meet the threshold, sorted highest first."""
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [cat for cat, score in ranked if score >= threshold]
    if not top and ranked:
        top = [ranked[0][0]]
    return top


def classify_issue_keyword(user_input: str) -> dict:
    """Keyword-based classification fallback. Returns same structure as OpenAI version."""
    scores = detect_issues_keyword(user_input)
    categories = get_top_categories(scores)
    return {
        "categories": categories,
        "is_crisis": False,  # Crisis detection handled separately in input_handler
        "sentiment": "neutral",
        "summary": "",
    }


# ── Main entry point ───────────────────────────────────────────────

def classify_issue(user_input: str) -> dict:
    """
    Classify the student's message. Uses OpenAI if API key is set, else keywords.
    Returns: {"categories": [...], "is_crisis": bool, "sentiment": str, "summary": str}
    """
    if OPENAI_API_KEY:
        try:
            return classify_issue_openai(user_input)
        except Exception as e:
            logger.warning("OpenAI classification failed, using keyword fallback: %s", e)
    return classify_issue_keyword(user_input)
