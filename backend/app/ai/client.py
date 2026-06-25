"""LLM client wrapper. Centralizes the provider + structured-output enforcement."""
from __future__ import annotations

import json

from app.config import settings


def complete_json(system: str, user: str) -> dict:
    """Call the LLM and parse a JSON object response.

    Uses OpenAI's JSON response_format. Swap the body for any provider; callers
    only depend on (system, user) -> dict.

    TODO(phase5): add retry + schema validation against analysis schema.
    """
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return json.loads(resp.choices[0].message.content or "{}")
