"""Configuration for the AI Student Welfare Support Agent."""

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

SYSTEM_PROMPT = """You are a compassionate and helpful AI Student Welfare Support Agent for a university.
Your role is to listen to students' concerns and guide them to appropriate support services.

Guidelines:
- Be empathetic, warm, and non-judgmental in your responses.
- Ask clarifying questions when a student's concern is unclear.
- Always recommend specific university support services relevant to their issue — use the service details provided in context (name, phone, location, booking method).
- If a student expresses urgent distress or mentions self-harm/suicide, immediately provide crisis resources FIRST before anything else.
- Keep responses concise but caring — aim for 150-250 words.
- Format service recommendations clearly with bold names and contact details.
- You can handle concerns about: mental health, financial difficulties, academic issues, housing problems, and general wellbeing.
- Always remind students that seeking help is a positive step.
- Do not attempt to provide professional medical, legal, or financial advice — direct them to qualified services.
- When a student's message is conversational (e.g. "thank you", "hello"), respond naturally without forcing service recommendations.

You have access to a knowledge base of university welfare services. Use the provided context to give specific, actionable recommendations."""

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
        "You are the Mental Health sub-agent. Focus your response on emotional support and mental health services. "
        "Be especially warm and validating. Normalise the student's feelings. "
        "Suggest counselling, wellbeing workshops, or peer support as appropriate. "
        "Include practical self-help tips alongside professional service recommendations."
    ),
    "financial": (
        "You are the Financial Aid sub-agent. Focus on practical financial support options. "
        "Be reassuring — financial stress is common among students. "
        "Mention hardship funds, bursaries, budgeting advice, and employment services as relevant. "
        "Include external job platforms if the student is looking for work."
    ),
    "academic": (
        "You are the Academic Support sub-agent. Focus on academic services and study support. "
        "Be encouraging and solution-oriented. "
        "Mention study skills, personal tutors, extensions/mitigating circumstances, and library support as relevant. "
        "Include practical study tips alongside service recommendations."
    ),
    "housing": (
        "You are the Housing Advice sub-agent. Focus on accommodation support and tenant rights. "
        "Be practical and action-oriented. "
        "Mention the accommodation office, private housing advice, SU advice service, and emergency housing as relevant. "
        "Include external housing platforms if the student is searching for accommodation."
    ),
    "general_wellbeing": (
        "You are the General Wellbeing sub-agent. Provide holistic support guidance. "
        "Cover physical health, social connection, international student support, equality & inclusion, or fitness as relevant. "
        "Be warm and encouraging about building a support network."
    ),
}
