from __future__ import annotations

from poketracker.config import Settings
from poketracker.core.models import Event, EventType, Offer
from poketracker.diffing.hashing import event_hash


def diff_offer(previous: Offer | None, current: Offer, settings: Settings) -> list[Event]:
    """Compare the last known state of one offer (product_key) to its freshly scraped state.
    Returns every event type that applies this run; several can fire at once (e.g. restock + price drop)."""
    events: list[Event] = []

    def emit(event_type: EventType, message: str, previous_price: float | None = None) -> None:
        events.append(
            Event(
                event_type=event_type,
                product_key=current.product_key,
                site_id=current.site_id,
                canonical_product_id=current.canonical_product_id,
                url=current.url,
                price=current.price,
                previous_price=previous_price,
                message=message,
                event_hash=event_hash(current.product_key, event_type.value, current.content_hash),
            )
        )

    if previous is None:
        emit(EventType.NEW_PRODUCT, f"New listing detected: {current.canonical_product_id} on {current.site_id}")
        if current.is_preorder:
            emit(EventType.NEW_PREORDER, f"New preorder: {current.canonical_product_id} on {current.site_id}")
        return events

    if not previous.in_stock and current.in_stock:
        emit(EventType.RESTOCK, f"Restocked: {current.canonical_product_id} on {current.site_id}")
    elif previous.in_stock != current.in_stock:
        emit(EventType.STOCK_CHANGE, f"Stock status changed for {current.canonical_product_id} on {current.site_id}")

    if not previous.is_preorder and current.is_preorder:
        emit(EventType.NEW_PREORDER, f"New preorder: {current.canonical_product_id} on {current.site_id}")

    if previous.price != current.price:
        emit(
            EventType.PRICE_CHANGE,
            f"Price changed for {current.canonical_product_id} on {current.site_id}: "
            f"{previous.price} -> {current.price}",
            previous_price=previous.price,
        )
        if previous.price and current.price and current.price < previous.price:
            drop_pct = (previous.price - current.price) / previous.price * 100
            if drop_pct >= settings.significant_price_drop_pct:
                emit(
                    EventType.PRICE_DROP_SIGNIFICANT,
                    f"Price dropped {drop_pct:.0f}% for {current.canonical_product_id} on {current.site_id}: "
                    f"{previous.price} -> {current.price}",
                    previous_price=previous.price,
                )

    if previous.seller != current.seller:
        emit(
            EventType.SELLER_CHANGE,
            f"Seller changed for {current.canonical_product_id} on {current.site_id}: "
            f"{previous.seller} -> {current.seller}",
        )

    return events


NOTIFY_WORTHY = frozenset(
    {
        EventType.NEW_PREORDER,
        EventType.RESTOCK,
        EventType.PRICE_DROP_SIGNIFICANT,
        EventType.NEW_PRODUCT,
    }
)


def detect_new_pages(site_id: str, previously_seen_urls: set[str], current_urls: set[str]) -> list[str]:
    """URLs returned by a site's fetch_listing_urls that were never seen before for that site."""
    return sorted(current_urls - previously_seen_urls)
