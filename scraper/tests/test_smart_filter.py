from poketracker.config import ProductConfig, SiteConfig
from poketracker.core.models import Event, EventType, RawListing
from poketracker.filtering.smart_filter import should_notify, should_track


def _listing(**overrides) -> RawListing:
    defaults = dict(
        site_id="ludifolie",
        title="Pokemon 30th Celebration ETB",
        url="https://example.com/etb",
        price=49.99,
        in_stock=True,
    )
    defaults.update(overrides)
    return RawListing(**defaults)


def _site_cfg(**overrides) -> SiteConfig:
    defaults = dict(site_id="ludifolie", base_url="https://example.com")
    defaults.update(overrides)
    return SiteConfig(**defaults)


def test_non_pokemon_listing_is_dropped():
    listing = _listing(title="Yu-Gi-Oh Display de boosters")
    assert should_track(listing, _site_cfg(), is_pokemon=False) is False


def test_pokemon_listing_is_kept_by_default():
    listing = _listing()
    assert should_track(listing, _site_cfg(), is_pokemon=True) is True


def test_amazon_marketplace_seller_is_dropped_when_only_seller_set():
    listing = _listing(seller="Vendeur Tiers SARL")
    cfg = _site_cfg(only_seller="Amazon")
    assert should_track(listing, cfg, is_pokemon=True) is False


def test_amazon_own_seller_is_kept_when_only_seller_set():
    listing = _listing(seller="Amazon.fr")
    cfg = _site_cfg(only_seller="Amazon")
    assert should_track(listing, cfg, is_pokemon=True) is True


def test_marketplace_filter_generalizes_to_a_new_site_with_zero_code_changes():
    """Regression test: only_seller is a plain config value, not a hardcoded per-site rule -
    a brand-new marketplace site (e.g. Bol.com) works purely from its own config, same code path
    as Amazon. This is what makes "add a third marketplace site" a config-only change."""
    third_party_listing = _listing(site_id="bolcom", seller="Verkocht door: SomeReseller BV")
    first_party_listing = _listing(site_id="bolcom", seller="Verkocht door bol.com")
    cfg = _site_cfg(site_id="bolcom", only_seller="bol.com")

    assert should_track(third_party_listing, cfg, is_pokemon=True) is False
    assert should_track(first_party_listing, cfg, is_pokemon=True) is True


def test_no_only_seller_configured_keeps_any_seller():
    listing = _listing(seller="Anyone At All")
    cfg = _site_cfg()  # only_seller unset
    assert should_track(listing, cfg, is_pokemon=True) is True


def test_scalper_keyword_in_seller_name_is_dropped():
    listing = _listing(seller="Boutique Occasion Reconditionné")
    assert should_track(listing, _site_cfg(), is_pokemon=True) is False


def _event(**overrides) -> Event:
    defaults = dict(
        event_type=EventType.RESTOCK,
        product_key="k1",
        site_id="ludifolie",
        canonical_product_id="30th-etb",
        url="https://example.com/etb",
        price=49.99,
        message="restocked",
        event_hash="h1",
    )
    defaults.update(overrides)
    return Event(**defaults)


def _product_cfg(**overrides) -> ProductConfig:
    defaults = dict(id="30th-etb", label="30th ETB", msrp_eur=49.99, tolerance_pct=20)
    defaults.update(overrides)
    return ProductConfig(**defaults)


def test_out_of_stock_event_is_not_notified():
    event = _event()
    assert should_notify(event, current_in_stock=False, product_cfg=_product_cfg()) is False


def test_in_stock_within_price_ceiling_is_notified():
    event = _event(price=49.99)
    assert should_notify(event, current_in_stock=True, product_cfg=_product_cfg()) is True


def test_price_above_ceiling_is_not_notified():
    event = _event(price=200.0)
    assert should_notify(event, current_in_stock=True, product_cfg=_product_cfg()) is False


def test_no_product_cfg_skips_price_ceiling_check():
    event = _event(price=200.0)
    assert should_notify(event, current_in_stock=True, product_cfg=None) is True


def _single_card_cfg(**overrides) -> ProductConfig:
    from poketracker.core.models import ProductCategory

    defaults = dict(
        id="mew-ex-sir-psa10",
        label="Mew ex SIR PSA 10",
        msrp_eur=150.0,
        tolerance_pct=50,
        category=ProductCategory.SINGLE_CARD,
    )
    defaults.update(overrides)
    return ProductConfig(**defaults)


def test_blocked_keyword_drops_listing_with_no_matched_product():
    listing = _listing(title="Pikachu carte à l'unité EB01")
    dropped = should_track(
        listing, _site_cfg(), is_pokemon=True, matched_product=None, blocked_keywords=("carte à l'unité",)
    )
    assert dropped is False


def test_blocked_keyword_does_not_drop_a_configured_single_card():
    listing = _listing(title="Mew ex SIR PSA 10 carte à l'unité")
    kept = should_track(
        listing,
        _site_cfg(),
        is_pokemon=True,
        matched_product=_single_card_cfg(),
        blocked_keywords=("carte à l'unité",),
    )
    assert kept is True


def test_blocked_keyword_still_drops_sealed_product_match():
    """A sealed-product match doesn't exempt the listing from the blocked-keyword filter -
    only a configured SINGLE_CARD category product does."""
    listing = _listing(title="Pokemon 30th Celebration ETB carte à l'unité")
    dropped = should_track(
        listing,
        _site_cfg(),
        is_pokemon=True,
        matched_product=_product_cfg(),  # category defaults to SEALED
        blocked_keywords=("carte à l'unité",),
    )
    assert dropped is False
