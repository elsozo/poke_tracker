from poketracker.config import ProductConfig
from poketracker.filtering.product_matching import detect_language_marker, match_product


def _fr_and_en_variants() -> list[ProductConfig]:
    default = ProductConfig(
        id="30th-etb",
        label="30th Celebration Elite Trainer Box",
        match_keywords=[["30th", "celebration"], ["etb", "elite trainer"]],
        msrp_eur=54.99,
    )
    en = ProductConfig(
        id="30th-etb-en",
        label="30th Celebration Elite Trainer Box EN",
        match_keywords=[["30th", "celebration"], ["etb", "elite trainer"]],
        msrp_eur=54.99,
        language="EN",
    )
    return [default, en]


def test_detect_language_marker_english():
    assert detect_language_marker("Pokemon ETB - English version") == "EN"
    assert detect_language_marker("Pokemon ETB Engelse versie") == "EN"


def test_detect_language_marker_default():
    assert detect_language_marker("Pokemon ETB Française") == "default"
    assert detect_language_marker("Pokemon ETB (FR)") == "default"


def test_detect_language_marker_none_when_unmarked():
    assert detect_language_marker("Pokemon 30th Celebration ETB") is None


def test_explicit_english_marker_matches_en_product():
    products = _fr_and_en_variants()
    product, _ = match_product(
        "Pokemon 30th Celebration Elite Trainer Box - English",
        products,
        language_variants_enabled=True,
    )
    assert product is not None
    assert product.id == "30th-etb-en"


def test_explicit_french_marker_matches_default_product():
    products = _fr_and_en_variants()
    product, _ = match_product(
        "Pokemon 30th Celebration Elite Trainer Box Française",
        products,
        language_variants_enabled=True,
    )
    assert product is not None
    assert product.id == "30th-etb"


def test_ambiguous_title_falls_back_to_default_product():
    products = _fr_and_en_variants()
    product, _ = match_product(
        "Pokemon 30th Celebration Elite Trainer Box",
        products,
        language_variants_enabled=True,
    )
    assert product is not None
    assert product.id == "30th-etb"


def test_pokipair_style_site_defaults_unmarked_title_to_english():
    products = _fr_and_en_variants()
    product, _ = match_product(
        "Pokemon 30th Celebration Elite Trainer Box",
        products,
        language_variants_enabled=True,
        default_language="EN",
    )
    assert product is not None
    assert product.id == "30th-etb-en"


def test_english_marker_with_no_en_counterpart_still_matches_default_product():
    """Most products don't have an EN sibling configured yet - an English marker on a title
    for one of those must not cause a total match failure, it should fall back to the only
    (default-language) variant that exists."""
    only_default = [
        ProductConfig(
            id="30th-tech-sticker-lucario",
            label="30th Celebration Tech Sticker Collection: Lucario",
            match_keywords=[["tech sticker"], ["lucario"]],
            msrp_eur=9.99,
        )
    ]
    product, _ = match_product(
        "30th Celebration Tech Sticker Collection Lucario - English",
        only_default,
        language_variants_enabled=True,
    )
    assert product is not None
    assert product.id == "30th-tech-sticker-lucario"


def test_language_variants_disabled_never_matches_en_product():
    """Sites not confirmed to stock English print (language_variants_enabled=False, the
    default) must never match the EN variant, even if the title happens to say "English"."""
    products = _fr_and_en_variants()
    product, _ = match_product(
        "Pokemon 30th Celebration Elite Trainer Box - English",
        products,
        language_variants_enabled=False,
    )
    assert product is not None
    assert product.id == "30th-etb"
