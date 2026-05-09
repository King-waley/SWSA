"""Shared OpenAI helpers used by sub-agents."""

import logging

from openai import OpenAI

import config
from config import OPENAI_RESPONSE_MODEL

logger = logging.getLogger(__name__)


def _record_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    purpose: str,
    user_id: int | None = None,
) -> None:
    """Best-effort token accounting. Imported lazily so the agent module
    can be used without the DB being initialised (in tests etc.)."""
    try:
        from db.usage import log_usage

        log_usage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            user_id=user_id,
            purpose=purpose,
        )
    except Exception:  # noqa: BLE001
        logger.debug("usage logging skipped", exc_info=True)


def stream_openai_response(
    system_message: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tokens: int = 350,
    temperature: float = 0.7,
    purpose: str = "chat",
    user_id: int | None = None,
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
        stream_options={"include_usage": True},
    )

    for chunk in stream:
        # Final usage chunk has no choices but carries .usage.
        if getattr(chunk, "usage", None) is not None:
            usage = chunk.usage
            _record_usage(
                model=OPENAI_RESPONSE_MODEL,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                purpose=purpose,
                user_id=user_id,
            )
            continue
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
