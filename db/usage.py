"""OpenAI token-usage tracking, with cost estimation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from db import SessionLocal
from db.models import ApiUsage

logger = logging.getLogger(__name__)


# Per-1M-token pricing (USD). Update these to match the OpenAI price list
# when the rates change. Defaults reflect gpt-4o-mini at the time of writing.
PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o":      {"input": 2.50, "output": 10.00},
    "gpt-4-turbo": {"input": 10.0, "output": 30.00},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Returns USD cost. Falls back to gpt-4o-mini pricing if model unknown."""
    rates = PRICES.get(model) or PRICES["gpt-4o-mini"]
    cost = (prompt_tokens / 1_000_000) * rates["input"] + (
        completion_tokens / 1_000_000
    ) * rates["output"]
    return round(cost, 6)


def log_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    *,
    user_id: int | None = None,
    purpose: str | None = None,
) -> None:
    try:
        with SessionLocal() as session:
            session.add(
                ApiUsage(
                    user_id=user_id,
                    model=model,
                    purpose=purpose,
                    prompt_tokens=int(prompt_tokens or 0),
                    completion_tokens=int(completion_tokens or 0),
                    total_tokens=int((prompt_tokens or 0) + (completion_tokens or 0)),
                )
            )
            session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("usage log failed for model=%s", model)


def usage_summary() -> dict:
    """Totals for today / this week / this month / all time, plus dollar costs."""
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    with SessionLocal() as session:
        def _window(after: datetime | None) -> dict:
            q = session.query(
                func.coalesce(func.sum(ApiUsage.prompt_tokens), 0),
                func.coalesce(func.sum(ApiUsage.completion_tokens), 0),
                func.count(ApiUsage.id),
            )
            if after is not None:
                q = q.filter(ApiUsage.created_at >= after)
            p, c, n = q.first() or (0, 0, 0)
            # Estimate cost using model breakdown for accuracy
            cost_q = session.query(
                ApiUsage.model,
                func.coalesce(func.sum(ApiUsage.prompt_tokens), 0),
                func.coalesce(func.sum(ApiUsage.completion_tokens), 0),
            )
            if after is not None:
                cost_q = cost_q.filter(ApiUsage.created_at >= after)
            cost = 0.0
            for model, mp, mc in cost_q.group_by(ApiUsage.model).all():
                cost += estimate_cost(model, int(mp or 0), int(mc or 0))
            return {
                "calls": int(n or 0),
                "prompt_tokens": int(p or 0),
                "completion_tokens": int(c or 0),
                "total_tokens": int((p or 0) + (c or 0)),
                "cost_usd": round(cost, 4),
            }

        return {
            "today": _window(day_ago),
            "week": _window(week_ago),
            "month": _window(month_ago),
            "all_time": _window(None),
        }


def usage_per_day(days: int = 14) -> list[dict]:
    """Daily token + call counts for the chart on the Insight tab."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    with SessionLocal() as session:
        rows = (
            session.query(
                func.date(ApiUsage.created_at).label("day"),
                func.count(ApiUsage.id).label("calls"),
                func.coalesce(func.sum(ApiUsage.total_tokens), 0).label("tokens"),
            )
            .filter(ApiUsage.created_at >= cutoff)
            .group_by("day")
            .order_by("day")
            .all()
        )
        return [
            {
                "day": str(r.day),
                "calls": int(r.calls or 0),
                "tokens": int(r.tokens or 0),
            }
            for r in rows
        ]
