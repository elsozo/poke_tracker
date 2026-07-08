from __future__ import annotations

import re

from rapidfuzz import fuzz, process

from poketracker.config import ProductConfig

POKEMON_KEYWORDS = ("pokemon", "pokémon", "pikachu", "mewtwo", "mew ")

# Explicit print-language markers sites use in titles. Substring match (not word-boundary):
# these are distinctive enough phrases/codes that partial-word false positives aren't a concern,
# and "(en)"/"(fr)" contain punctuation that word-boundary regex handles awkwardly.
EN_LANGUAGE_MARKERS = ("english", "engelse versie", "en anglais", "version anglaise", "(en)", "eng. version")
DEFAULT_LANGUAGE_MARKERS = ("française", "francaise", "french", "néerlandaise", "nederlandse", "(fr)", "(nl)")


def detect_language_marker(title: str) -> str | None:
    """Returns 'EN' or 'default' if the title explicitly says so, else None (unmarked)."""
    lowered = title.lower()
    if any(marker in lowered for marker in EN_LANGUAGE_MARKERS):
        return "EN"
    if any(marker in lowered for marker in DEFAULT_LANGUAGE_MARKERS):
        return "default"
    return None


def _candidate_strings(product: ProductConfig) -> list[str]:
    return [product.label, *product.aliases]


def _contains_word(lowered_title: str, keyword: str) -> bool:
    return re.search(rf"\b{re.escape(keyword.lower())}\b", lowered_title) is not None


def _has_keyword(title: str, product: ProductConfig) -> bool:
    """A title is only eligible to match a product if it satisfies every configured keyword
    group. Generic words shared by every Pokemon box ("coffret", "pokemon", "collection"...)
    are deliberately NOT enough on their own — fuzzy scoring alone scores those far too high
    against short aliases and misclassifies unrelated boxes. A generic product type like "ETB"
    is only meaningful once scoped to a set, e.g. groups=[["etb"], ["héros transcendants", "me2.5"]]."""
    if not product.match_keywords:
        return True  # no keywords configured: fall back to pure fuzzy matching
    lowered = title.lower()
    for group in product.match_keywords:
        keywords = [group] if isinstance(group, str) else group
        if not any(_contains_word(lowered, kw) for kw in keywords):
            return False
    return True


def match_product(
    title: str,
    products: list[ProductConfig],
    score_cutoff: float = 60.0,
    *,
    language_variants_enabled: bool = False,
    default_language: str = "default",
) -> tuple[ProductConfig | None, float]:
    """Match a raw listing title against the canonical product catalog: a product is only a
    candidate if a distinctive keyword is present, then fuzzy score ranks among candidates.
    Returns (best matching ProductConfig or None, confidence 0-100).

    When `language_variants_enabled` (only true for sites confirmed to stock English print),
    an explicit language marker in the title picks EN vs default-language candidates; with no
    marker, `default_language` decides ("default" for most sites, "EN" for an English-only
    catalog like PokiPair). Sites without this enabled never match an EN-tagged product at all,
    so a stray "English" in an unrelated title can't misfire on a site that doesn't stock it.

    Most products don't have an EN sibling configured yet (rolled out "to start" for a subset) -
    when the language filter would eliminate every candidate because no counterpart exists for
    this product family, it's skipped rather than losing the match entirely."""
    candidates = [p for p in products if _has_keyword(title, p)]

    if language_variants_enabled:
        wanted_en = (detect_language_marker(title) or default_language) == "EN"
        language_filtered = [p for p in candidates if (p.language == "EN") == wanted_en]
        if language_filtered:
            candidates = language_filtered
        # else: no default/EN counterpart exists for this family - keep the unfiltered set so a
        # single-language product still matches regardless of a marker with nothing to compare to.
    else:
        candidates = [p for p in candidates if p.language != "EN"]

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
