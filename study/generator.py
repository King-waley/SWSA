"""ChatGPT-powered study tools: summary, key concepts, MCQ quiz."""

from __future__ import annotations

import json

from openai import OpenAI

import config
from config import OPENAI_RESPONSE_MODEL


# Cap input so we don't blow past the model's context window. ~60K chars
# is roughly 15K tokens, leaving plenty of room for the response.
MAX_DOC_CHARS = 60_000


def _truncate(text: str) -> str:
    if len(text) <= MAX_DOC_CHARS:
        return text
    return text[:MAX_DOC_CHARS] + "\n\n[…document truncated for length…]"


def _client() -> OpenAI:
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _log_usage(response, purpose: str) -> None:
    """Best-effort token accounting."""
    try:
        from db.usage import log_usage

        usage = getattr(response, "usage", None)
        if usage is not None:
            log_usage(
                model=OPENAI_RESPONSE_MODEL,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                purpose=purpose,
            )
    except Exception:  # noqa: BLE001
        pass


# ── Summary ────────────────────────────────────────────────────────────


def generate_summary(document_text: str) -> str:
    """Return a 200-300 word summary of the document."""
    text = _truncate(document_text)
    response = _client().chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic tutor helping a university student understand "
                    "their study material. Write clear, accurate summaries that highlight "
                    "the main ideas without losing important detail."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Summarise the following document in 200-300 words. Focus on the "
                    "main argument or thesis, the key supporting points, and the "
                    "important conclusions. Use plain prose — no headings, no bullet "
                    "lists.\n\n"
                    "DOCUMENT:\n"
                    f"{text}"
                ),
            },
        ],
        temperature=0.3,
        max_tokens=600,
    )
    _log_usage(response, purpose="study_summary")
    return (response.choices[0].message.content or "").strip()


# ── Key concepts ───────────────────────────────────────────────────────


_KEY_POINTS_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "extract_key_concepts",
            "description": "Extract the most important concepts from a study document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "concepts": {
                        "type": "array",
                        "minItems": 5,
                        "maxItems": 10,
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Short label for the concept (3-7 words).",
                                },
                                "explanation": {
                                    "type": "string",
                                    "description": "1-2 sentence explanation in plain language.",
                                },
                            },
                            "required": ["title", "explanation"],
                        },
                    }
                },
                "required": ["concepts"],
            },
        },
    }
]


def generate_key_concepts(document_text: str) -> list[dict]:
    """Return a list of {'title': str, 'explanation': str}."""
    text = _truncate(document_text)
    response = _client().chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic tutor. From the student's document, extract the "
                    "most important concepts they need to understand. Prefer ideas that "
                    "would appear on an exam over surface-level facts."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Extract 5-10 key concepts from the document below. For each, give a "
                    "short title and a 1-2 sentence explanation in plain language.\n\n"
                    "DOCUMENT:\n"
                    f"{text}"
                ),
            },
        ],
        tools=_KEY_POINTS_TOOL,
        tool_choice={"type": "function", "function": {"name": "extract_key_concepts"}},
        temperature=0.3,
        max_tokens=900,
    )
    _log_usage(response, purpose="study_keypoints")
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return args.get("concepts", []) or []


# ── Quiz (multiple-choice) ─────────────────────────────────────────────


def _quiz_tool(num_questions: int) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "build_quiz",
                "description": "Build a multiple-choice quiz from a study document.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "minItems": num_questions,
                            "maxItems": num_questions,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {"type": "string"},
                                    "options": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 4,
                                        "maxItems": 4,
                                        "description": "Exactly four answer choices.",
                                    },
                                    "correct_index": {
                                        "type": "integer",
                                        "minimum": 0,
                                        "maximum": 3,
                                        "description": "Index (0-3) of the correct option in `options`.",
                                    },
                                    "explanation": {
                                        "type": "string",
                                        "description": "1-2 sentence explanation of why the correct answer is right.",
                                    },
                                },
                                "required": ["question", "options", "correct_index", "explanation"],
                            },
                        }
                    },
                    "required": ["questions"],
                },
            },
        }
    ]


def generate_quiz(document_text: str, num_questions: int = 5) -> list[dict]:
    """Return [{'question', 'options', 'correct_index', 'explanation'}, ...]."""
    text = _truncate(document_text)
    response = _client().chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic tutor. You write exam-quality multiple-choice "
                    "questions that test understanding, not rote memorisation. Distractors "
                    "should be plausible but clearly wrong on careful reading."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write {num_questions} multiple-choice questions based on the document "
                    "below. Each question must have exactly four options with exactly one "
                    "correct answer, plus a brief explanation. Avoid trivia; aim for "
                    "concept-checking questions a tutor would set.\n\n"
                    "DOCUMENT:\n"
                    f"{text}"
                ),
            },
        ],
        tools=_quiz_tool(num_questions),
        tool_choice={"type": "function", "function": {"name": "build_quiz"}},
        temperature=0.5,
        max_tokens=1500,
    )
    _log_usage(response, purpose="study_quiz")
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return args.get("questions", []) or []
