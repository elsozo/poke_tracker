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


def test_amazon_marketplace_seller_is_dropped_when_filter_enabled():
    listing = _listing(seller="Vendeur Tiers SARL")
    cfg = _site_cfg(seller_filter="sold_by_amazon_only")
    assert should_track(listing, cfg, is_pokemon=True) is False


def test_amazon_own_seller_is_kept_when_filter_enabled():
    listing = _listing(seller="Amazon.fr")
    cfg = _site_cfg(seller_filter="sold_by_amazon_only")
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
