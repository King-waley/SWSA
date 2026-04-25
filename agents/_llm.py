"""Shared OpenAI helpers used by sub-agents."""

import logging

from openai import OpenAI

import config
from config import OPENAI_RESPONSE_MODEL

logger = logging.getLogger(__name__)


def stream_openai_response(
    system_message: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tokens: int = 600,
    temperature: float = 0.7,
):
    """Stream a ChatGPT completion. Yields text chunks. Caller handles fallback."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    messages: list[dict] = [{"role": "system", "content": system_message}]
    if conversation_history:
        messages.extend(conversation_history[-20:])
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model=OPENAI_RESPONSE_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
