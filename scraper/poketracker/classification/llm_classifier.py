from __future__ import annotations

import json
import os

from poketracker.config import ProductConfig, Settings
from poketracker.classification.heuristic_classifier import ClassificationResult

_SYSTEM_PROMPT = (
    "You classify French Pokemon TCG retail listing titles against a fixed product catalog. "
    "Reply with strict JSON: {\"canonical_product_id\": <id-or-null>, \"confidence\": <0-100>, "
    "\"is_pokemon\": <bool>}. Use null when the title doesn't match any candidate."
)


def is_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def classify(title: str, products: list[ProductConfig], settings: Settings) -> ClassificationResult | None:
    """Only called for titles the heuristic classifier couldn't confidently place. Returns None
    (never raises) if the API key is absent or the call fails, so this is never a hard dependency."""
    if not is_available():
        return None

    try:
        from openai import OpenAI  # lazy import: package may not even be installed

        client = OpenAI()
        candidates = [{"id": p.id, "label": p.label, "aliases": p.aliases} for p in products]
        response = client.chat.completions.create(
            model=settings.classification.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({"title": title, "candidates": candidates})},
            ],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        return ClassificationResult(**parsed)
    except Exception:
        return None
