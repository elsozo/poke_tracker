from __future__ import annotations

from poketracker.config import ProductConfig, SiteConfig
from poketracker.core.models import Event, ProductCategory, RawListing

SCALPER_KEYWORDS = ("occasion", "reconditionné", "seller offer", "marketplace")


def should_track(
    listing: RawListing,
    site_cfg: SiteConfig,
    is_pokemon: bool,
    matched_product: ProductConfig | None = None,
    blocked_keywords: tuple[str, ...] = (),
) -> bool:
    """Relevance filter, applied after product matching but before a listing becomes a tracked
    Offer: drop non-Pokémon products, third-party marketplace sellers, and blocked-keyword noise.
    `matched_product`/`blocked_keywords` let a specifically-configured product (e.g. a single
    card we do want) survive a keyword that would otherwise blanket-block it (e.g. "carte à
    l'unité") - the block only applies when nothing already matched."""
    if not is_pokemon:
        return False

    # Marketplace sites (Amazon, Bol.com, ...): only first-party stock passes. A site opts in
    # by setting only_seller in config - no code change needed to add another marketplace site.
    if site_cfg.only_seller:
        if listing.seller is None or site_cfg.only_seller.lower() not in listing.seller.lower():
            return False

    if listing.seller and any(kw in listing.seller.lower() for kw in SCALPER_KEYWORDS):
        return False

    is_configured_single_card = matched_product is not None and matched_product.category == ProductCategory.SINGLE_CARD
    if not is_configured_single_card and blocked_keywords:
        lowered_title = listing.title.lower()
        if any(kw.lower() in lowered_title for kw in blocked_keywords):
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
