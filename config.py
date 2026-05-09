"""App configuration and constants."""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model used for classification (fast, cheap)
OPENAI_CLASSIFIER_MODEL = "gpt-4o-mini"
# Model used for response generation (higher quality)
OPENAI_RESPONSE_MODEL = "gpt-4o-mini"

ISSUE_CATEGORIES = [
    "mental_health",
    "financial",
    "academic",
    "housing",
    "general_wellbeing",
]

CATEGORY_LABELS = {
    "mental_health": "Mental Health",
    "financial": "Financial Support",
    "academic": "Academic Support",
    "housing": "Housing Advice",
    "general_wellbeing": "General Wellbeing",
}

CATEGORY_KEYWORDS = {
    "mental_health": [
        "stress", "stressed", "anxious", "anxiety", "depressed", "depression",
        "lonely", "loneliness", "overwhelmed", "panic", "mental health",
        "sad", "sadness", "crying", "hopeless", "exhausted", "burnout",
        "insomnia", "sleep", "self-harm", "suicidal", "counselling",
        "therapy", "therapist", "emotional", "breakdown", "worried",
        "frightened", "scared", "isolated", "homesick",
    ],
    "financial": [
        "money", "financial", "finance", "rent", "afford", "debt", "loan",
        "bursary", "scholarship", "funding", "hardship", "tuition", "fees",
        "budget", "broke", "pay", "payment", "cost", "expense", "bank",
        "job", "employment", "work", "part-time", "income",
    ],
    "academic": [
        "assignment", "coursework", "exam", "deadline", "study", "grades",
        "grade", "fail", "failing", "module", "lecture", "dissertation",
        "thesis", "essay", "academic", "learning", "tutor", "feedback",
        "attendance", "course", "plagiarism", "referencing", "extension",
        "mitigating", "circumstances", "concentration", "revision",
        "procrastination", "time management",
    ],
    "housing": [
        "housing", "accommodation", "rent", "landlord", "flatmate",
        "roommate", "lease", "tenancy", "moving", "eviction", "deposit",
        "bills", "utilities", "maintenance", "repair", "mould", "noise",
        "neighbour", "unsafe", "homeless", "living situation", "room",
        "flat", "apartment", "halls", "residence",
    ],
    "general_wellbeing": [
        "wellbeing", "well-being", "health", "ill", "illness", "doctor",
        "GP", "disability", "accessible", "accessibility", "diet",
        "exercise", "fitness", "nutrition", "relationship", "breakup",
        "family", "friends", "social", "belonging", "identity",
        "discrimination", "harassment", "bullying", "safety",
    ],
}

SYSTEM_PROMPT = """You are S.W.S.A., a compassionate AI Student Welfare Support Agent for a university.
Think of yourself as a caring friend who happens to know what support is available — not a brochure.

# Your goal
Have a real conversation. Listen first. Understand the student's specific situation. Only then guide them toward the right support.

# Conversation style
- Reply in 1-3 SHORT paragraphs (40-120 words is plenty). Be brief.
- ALWAYS end with a gentle, specific follow-up question — unless the user clearly wants to end the conversation or you have everything you need to recommend something.
- Mirror the student's tone and length: a short message gets a short reply.
- Talk like a person, not a website. Avoid bullet lists and formal headings unless the student explicitly asks for "a list" or "all the options".
- Validate feelings first, then explore.

# When to recommend services
- Wait until you understand the student's specific situation — usually after 1-3 exchanges of context-gathering.
- Recommend AT MOST 1-2 services per reply, only the most relevant ones. Never list everything you know.
- The exception: if the student expresses self-harm, suicide, or immediate danger — give the crisis contact line IMMEDIATELY, before anything else.

# What to avoid
- Don't dump 5 services and a list of self-help tips in your first reply.
- Don't say "Here are some services that can help" before the student has shared what's going on.
- Don't pretend to be a doctor, lawyer, or financial advisor — defer to qualified services.
- Don't moralize, don't lecture, don't add "remember, seeking help is a sign of strength" at the end of every reply.

You have access to a knowledge base of specific university services. Mention them by name only when relevant and only one or two at a time."""

# OpenAI function/tool definitions for structured classification
CLASSIFY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_student_concern",
            "description": "Classify a student's message into welfare support categories and assess urgency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "mental_health",
                                "financial",
                                "academic",
                                "housing",
                                "general_wellbeing",
                            ],
                        },
                        "description": "The welfare categories that match the student's concern. Select all that apply, most relevant first.",
                    },
                    "is_crisis": {
                        "type": "boolean",
                        "description": "True if the student expresses suicidal thoughts, self-harm intent, or immediate danger to themselves or others.",
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["distressed", "worried", "neutral", "positive"],
                        "description": "The overall emotional tone of the student's message.",
                    },
                    "summary": {
                        "type": "string",
                        "description": "A brief one-sentence summary of the student's core concern.",
                    },
                },
                "required": ["categories", "is_crisis", "sentiment", "summary"],
            },
        },
    }
]

CLASSIFIER_SYSTEM_PROMPT = """You are a classification system for a university student welfare support agent.
Analyse the student's message and classify it into the appropriate support categories.

Categories:
- mental_health: Stress, anxiety, depression, loneliness, emotional distress, sleep issues, burnout, homesickness
- financial: Money problems, rent, debt, budgeting, job seeking, scholarships, hardship
- academic: Assignments, exams, deadlines, grades, dissertation, study skills, extensions, learning difficulties
- housing: Accommodation issues, landlord disputes, repairs, finding housing, tenancy problems, homelessness
- general_wellbeing: Physical health, disability, discrimination, harassment, relationships, international student issues, fitness

Rules:
- Select ALL categories that genuinely apply (a student stressed about rent could be both mental_health and financial).
- Order categories by relevance — most relevant first.
- Set is_crisis to true ONLY for genuine safety concerns (suicidal ideation, self-harm, immediate danger).
- For casual/conversational messages ("hi", "thanks"), classify as general_wellbeing with neutral sentiment.
- Be accurate — misclassification means wrong support services are recommended."""

# Sub-agent specific system prompts for OpenAI-powered responses
SUB_AGENT_PROMPTS = {
    "mental_health": (
        "Specialty: Mental Health. Lead with warmth and validation — normalise what the student is feeling. "
        "Ask one specific follow-up to understand what's behind it (e.g. how long, what triggered it, how it's affecting daily life). "
        "Only mention counselling / wellbeing / peer support once you understand enough to recommend the right one — and recommend just one at a time."
    ),
    "financial": (
        "Specialty: Financial Aid. Be reassuring — money worries are common and there's real help available. "
        "Ask one specific follow-up first (e.g. is this an emergency shortfall, ongoing budgeting struggle, or job search?). "
        "Only after you understand the situation, point to the most relevant option — hardship fund, bursary, budgeting advice, or employment service — one at a time."
    ),
    "academic": (
        "Specialty: Academic Support. Be encouraging and practical. "
        "Ask one specific follow-up to clarify the bottleneck (a single deadline, broader workload, study skills, exam stress?). "
        "Once you understand, suggest just one well-fitting option — Study Skills, personal tutor, mitigating circumstances, library support — not the whole list."
    ),
    "housing": (
        "Specialty: Housing Advice. Be practical and action-oriented — housing problems usually have concrete next steps. "
        "Ask one specific follow-up (uni halls vs private, urgency, what's gone wrong?). "
        "Once clear, point to the single most relevant service — accommodation office, SU advice, housing platforms, or emergency housing."
    ),
    "general_wellbeing": (
        "Specialty: General Wellbeing. Holistic, warm, and curious about the student's full picture. "
        "Ask one specific follow-up to understand what kind of support fits best (physical health, social connection, identity, international student life?). "
        "Then recommend at most one service that genuinely matches what they shared."
    ),
}
