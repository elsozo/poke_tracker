from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from poketracker.config import SiteConfig
from poketracker.core.base_scraper import SiteScraper
from poketracker.core.models import RawListing
from poketracker.sites.price_parsing import parse_price
from poketracker.sites.registry import register_site

# UNVERIFIED: bol.com returned a 403 (Cloudflare "Just a moment...") to every plain HTTP request
# during development, so these selectors were never checked against real markup - they're a
# best-effort guess based on bol.com's general product-tile conventions (data-test attributes,
# "Verkoop door <seller>" seller line), not a confirmed scrape. Kept disabled in sites.yaml.
# MUST be verified against a real fetched page (e.g. via a browser or a proxy) before enabling.
_DEFAULT_SELECTORS = {
    "listing_item": "[data-test='product-item'], li.product-item",
    "title_link": "a[data-test='product-title'], a.product-title",
    "price": "[data-test='price'], .promo-price",
    "seller_line": "[data-test='seller-name'], .product-seller",
}

PREORDER_KEYWORDS = ("pre-order", "reserveren", "vooraf bestellen")


@register_site("bol_com")
class BolComScraper(SiteScraper):
    """Bespoke plugin for bol.com search results. Bol.com is a marketplace: first-party ("bol")
    and third-party seller listings are mixed in the same results, so only_seller (set to
    "bol" in sites.yaml) is required to keep only first-party stock - same pattern as amazon_fr.py."""

    def fetch_listing_urls(self, cfg: SiteConfig) -> list[str]:
        return cfg.start_urls

    def parse_listing_page(self, html: str, url: str, cfg: SiteConfig) -> list[RawListing]:
        selectors = {**_DEFAULT_SELECTORS, **cfg.selectors}
        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []

        for item in soup.select(selectors["listing_item"]):
            link = item.select_one(selectors["title_link"])
            if link is None or not link.get("href"):
                continue
            title = link.get_text(strip=True)
            listing_url = urljoin(cfg.base_url, link["href"])

            price_el = item.select_one(selectors["price"])
            price = parse_price(price_el.get_text(strip=True)) if price_el else None

            seller_el = item.select_one(selectors["seller_line"])
            seller_text = seller_el.get_text(strip=True) if seller_el else ""
            seller_match = re.search(r"verkoop(?:\s+door)?\s*:?\s*(.+)", seller_text, re.IGNORECASE)
            seller = seller_match.group(1).strip() if seller_match else (seller_text or None)

            lowered_title = title.lower()

            listings.append(
                RawListing(
                    site_id=cfg.site_id,
                    title=title,
                    url=listing_url,
                    price=price,
                    in_stock=True,  # bol.com search results are generally in-stock-only by default
                    is_preorder=any(kw in lowered_title for kw in PREORDER_KEYWORDS),
                    seller=seller,
                )
            )

        return listings
