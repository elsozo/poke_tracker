from __future__ import annotations

from pydantic import BaseModel

from poketracker.config import ProductConfig
from poketracker.filtering.product_matching import looks_like_pokemon, match_product


class ClassificationResult(BaseModel):
    canonical_product_id: str | None
    confidence: float  # 0-100
    is_pokemon: bool


def classify(
    title: str,
    products: list[ProductConfig],
    *,
    language_variants_enabled: bool = False,
    default_language: str = "default",
) -> ClassificationResult:
    """Default, always-available, zero-cost classifier: alias/keyword + fuzzy match.
    Used for the vast majority of listings; only low-confidence results should escalate to an LLM."""
    product, score = match_product(
        title,
        products,
        language_variants_enabled=language_variants_enabled,
        default_language=default_language,
    )
    return ClassificationResult(
        canonical_product_id=product.id if product else None,
        confidence=score,
        is_pokemon=looks_like_pokemon(title) or product is not None,
    )
