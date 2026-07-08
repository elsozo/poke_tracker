from __future__ import annotations

from poketracker.config import ProductConfig, SiteConfig
from poketracker.core.models import Event, RawListing

# Named seller rules referenced from sites.yaml's `seller_filter` key.
# Each returns True to KEEP the listing, False to drop it as a marketplace/scalper offer.
_SELLER_RULES = {
    "sold_by_amazon_only": lambda seller: seller is not None and "amazon" in seller.lower(),
}

SCALPER_KEYWORDS = ("occasion", "reconditionné", "seller offer", "marketplace")


def should_track(listing: RawListing, site_cfg: SiteConfig, is_pokemon: bool) -> bool:
    """Relevance filter, applied before a listing becomes a tracked Offer: drop non-Pokémon
    products and known marketplace/scalper sellers outright — these are noise, not state to track."""
    if not is_pokemon:
        return False

    if site_cfg.seller_filter:
        rule = _SELLER_RULES.get(site_cfg.seller_filter)
        if rule is not None and not rule(listing.seller):
            return False

    if listing.seller and any(kw in listing.seller.lower() for kw in SCALPER_KEYWORDS):
        return False

    return True


def should_notify(event: Event, current_in_stock: bool, product_cfg: ProductConfig | None) -> bool:
    """Notification-time suppression: an offer that is currently out of stock or priced above
    its configured ceiling still gets tracked/stored (so a future restock/price-drop can be
    detected), but we don't want a push about it in that state."""
    if not current_in_stock:
        return False
    if product_cfg is not None and event.price is not None and event.price > product_cfg.max_accepted_price:
        return False
    return True
