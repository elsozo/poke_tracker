from datetime import datetime, timezone

from poketracker.config import Settings
from poketracker.core.models import EventType, Offer
from poketracker.diffing.event_detector import diff_offer

NOW = datetime(2026, 7, 8, tzinfo=timezone.utc)


def _offer(**overrides) -> Offer:
    defaults = dict(
        product_key="abc123",
        site_id="ludifolie",
        canonical_product_id="30th-etb",
        url="https://example.com/etb",
        price=49.99,
        in_stock=True,
        is_preorder=False,
        seller=None,
        content_hash="hash1",
        first_seen=NOW,
        last_seen=NOW,
    )
    defaults.update(overrides)
    return Offer(**defaults)


def _settings() -> Settings:
    return Settings()


def test_first_time_seen_is_new_product():
    events = diff_offer(None, _offer(), _settings())
    types = {e.event_type for e in events}
    assert types == {EventType.NEW_PRODUCT}


def test_first_time_seen_preorder_also_emits_new_preorder():
    events = diff_offer(None, _offer(is_preorder=True), _settings())
    types = {e.event_type for e in events}
    assert types == {EventType.NEW_PRODUCT, EventType.NEW_PREORDER}


def test_out_of_stock_to_in_stock_is_restock():
    previous = _offer(in_stock=False)
    current = _offer(in_stock=True)
    events = diff_offer(previous, current, _settings())
    assert EventType.RESTOCK in {e.event_type for e in events}
    assert EventType.STOCK_CHANGE not in {e.event_type for e in events}


def test_in_stock_to_out_of_stock_is_plain_stock_change_not_restock():
    previous = _offer(in_stock=True)
    current = _offer(in_stock=False)
    events = diff_offer(previous, current, _settings())
    types = {e.event_type for e in events}
    assert EventType.STOCK_CHANGE in types
    assert EventType.RESTOCK not in types


def test_preorder_flip_emits_new_preorder():
    previous = _offer(is_preorder=False)
    current = _offer(is_preorder=True)
    events = diff_offer(previous, current, _settings())
    assert EventType.NEW_PREORDER in {e.event_type for e in events}


def test_small_price_change_is_not_significant_drop():
    previous = _offer(price=50.0)
    current = _offer(price=48.0)  # 4% drop, below the 10% default threshold
    events = diff_offer(previous, current, _settings())
    types = {e.event_type for e in events}
    assert EventType.PRICE_CHANGE in types
    assert EventType.PRICE_DROP_SIGNIFICANT not in types


def test_large_price_drop_is_significant():
    previous = _offer(price=50.0)
    current = _offer(price=40.0)  # 20% drop
    events = diff_offer(previous, current, _settings())
    types = {e.event_type for e in events}
    assert EventType.PRICE_CHANGE in types
    assert EventType.PRICE_DROP_SIGNIFICANT in types


def test_price_increase_is_not_a_significant_drop():
    previous = _offer(price=40.0)
    current = _offer(price=60.0)
    events = diff_offer(previous, current, _settings())
    types = {e.event_type for e in events}
    assert EventType.PRICE_CHANGE in types
    assert EventType.PRICE_DROP_SIGNIFICANT not in types


def test_seller_change_detected():
    previous = _offer(seller="Boutique A")
    current = _offer(seller="Boutique B")
    events = diff_offer(previous, current, _settings())
    assert EventType.SELLER_CHANGE in {e.event_type for e in events}


def test_no_change_emits_no_events():
    same = _offer()
    events = diff_offer(same, same, _settings())
    assert events == []


def test_event_hash_is_stable_and_dedupable():
    previous = _offer(in_stock=False, content_hash="hash_oos")
    current = _offer(in_stock=True, content_hash="hash_in")
    first_run = diff_offer(previous, current, _settings())
    second_run = diff_offer(previous, current, _settings())

    first_hashes = {e.event_hash for e in first_run}
    second_hashes = {e.event_hash for e in second_run}
    assert first_hashes == second_hashes
