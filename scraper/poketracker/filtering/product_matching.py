from __future__ import annotations

import re

from rapidfuzz import fuzz, process

from poketracker.config import ProductConfig

POKEMON_KEYWORDS = ("pokemon", "pokémon", "pikachu", "mewtwo", "mew ")


def _candidate_strings(product: ProductConfig) -> list[str]:
    return [product.label, *product.aliases]


def _has_keyword(title: str, product: ProductConfig) -> bool:
    """A title is only eligible to match a product if one of its distinctive keywords is
    present as a whole word. Generic words shared by every Pokemon box ("coffret", "pokemon",
    "collection"...) are deliberately NOT enough — fuzzy scoring alone scores those far too
    high against short aliases and misclassifies unrelated boxes (see products.yaml keywords)."""
    if not product.match_keywords:
        return True  # no keywords configured: fall back to pure fuzzy matching
    lowered = title.lower()
    return any(re.search(rf"\b{re.escape(kw.lower())}\b", lowered) for kw in product.match_keywords)


def match_product(
    title: str, products: list[ProductConfig], score_cutoff: float = 60.0
) -> tuple[ProductConfig | None, float]:
    """Match a raw listing title against the canonical product catalog: a product is only a
    candidate if a distinctive keyword is present, then fuzzy score ranks among candidates.
    Returns (best matching ProductConfig or None, confidence 0-100)."""
    candidates = [p for p in products if _has_keyword(title, p)]
    if not candidates:
        return None, 0.0

    best_product: ProductConfig | None = None
    best_score = 0.0
    for product in candidates:
        result = process.extractOne(
            title, _candidate_strings(product), scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff
        )
        if result is not None and result[1] > best_score:
            best_score = result[1]
            best_product = product

    return best_product, best_score


def looks_like_pokemon(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in POKEMON_KEYWORDS)
