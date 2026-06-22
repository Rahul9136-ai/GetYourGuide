"""
AI-generated forecast explanation using Claude (Anthropic API).

Takes the deterministic forecast summary (trend, inflate/deflate, drivers) and
asks Claude to turn it into a short, business-ready narrative for an operations
/ demand-planning audience.

Requires the `anthropic` package and an `ANTHROPIC_API_KEY` environment variable.
If either is missing, `generate_ai_summary` returns `{"ok": False, "reason": ...}`
so the caller can fall back to the rule-based narrative.
"""

from __future__ import annotations

import json
import os

MODEL = "claude-opus-4-8"

SYSTEM = (
    "You are a senior demand-planning and workforce analyst at GetYourGuide. "
    "You explain daily-demand forecasts to operations managers in clear, concise "
    "business language. Be specific and quote the numbers you are given. "
    "Structure the answer as: one headline sentence, then 3-4 short bullet points "
    "(trend, seasonality, capacity/staffing implication, one watch-out). "
    "No preamble, no markdown headers, under 160 words."
)


def generate_ai_summary(context: dict) -> dict:
    """Return {'ok': True, 'text', 'model'} or {'ok': False, 'reason'}."""
    try:
        import anthropic
    except ImportError:
        return {"ok": False, "reason": "The 'anthropic' package is not installed (pip install anthropic)."}

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"ok": False, "reason": "Set the ANTHROPIC_API_KEY environment variable to enable AI summaries."}

    prompt = (
        "Write an executive explanation of this demand forecast and what it means "
        "for capacity planning. Here is the data (JSON):\n\n"
        + json.dumps(context, indent=2)
    )

    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return {"ok": True, "text": text, "model": resp.model}
    except anthropic.AuthenticationError:
        return {"ok": False, "reason": "ANTHROPIC_API_KEY is invalid or revoked."}
    except anthropic.APIStatusError as e:
        return {"ok": False, "reason": f"Anthropic API error ({e.status_code})."}
    except Exception as e:  # network, etc.
        return {"ok": False, "reason": f"AI request failed: {e}"}
