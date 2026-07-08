from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from poketracker.config import SiteConfig
from poketracker.core.base_scraper import SiteScraper
from poketracker.core.models import RawListing
from poketracker.sites.registry import register_site

PREORDER_KEYWORDS = ("précommande", "precommande", "pre-order", "preorder")

_DEFAULT_SELECTORS = {
    "listing_item": "li.product",
    "title_link": ".woocommerce-loop-product__title a, a.woocommerce-LoopProduct-link-title",
    "price_amount": ".price .woocommerce-Price-amount bdi, .price .woocommerce-Price-amount",
}


@register_site("generic_woocommerce")
class GenericWooCommerceScraper(SiteScraper):
    """Config-driven scraper for shops running WooCommerce's default theme markup on their
    `?s=<query>&post_type=product` search results. No new code needed per shop: one sites.yaml
    entry with `scraper_class: generic_woocommerce`."""

    def fetch_listing_urls(self, cfg: SiteConfig) -> list[str]:
        return cfg.start_urls

    def parse_listing_page(self, html: str, url: str, cfg: SiteConfig) -> list[RawListing]:
        selectors = {**_DEFAULT_SELECTORS, **cfg.selectors}
        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []

        for item in soup.select(selectors["listing_item"]):
            anchor = item.select_one(selectors["title_link"])
            if anchor is None or not anchor.get("href"):
                continue
            title = anchor.get_text(strip=True)
            listing_url = urljoin(cfg.base_url, anchor["href"])

            price_el = item.select_one(selectors["price_amount"])
            price = _parse_french_price(price_el.get_text(strip=True)) if price_el else None

            item_classes = item.get("class", [])
            in_stock = "outofstock" not in item_classes

            lowered_title = title.lower()
            is_preorder = any(kw in lowered_title for kw in PREORDER_KEYWORDS)

            listings.append(
                RawListing(
                    site_id=cfg.site_id,
                    title=title,
                    url=listing_url,
                    price=price,
                    in_stock=in_stock,
                    is_preorder=is_preorder,
                    seller=None,
                )
            )

        return listings


def _parse_french_price(text: str) -> float | None:
    cleaned = text.replace("\xa0", "").replace("€", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
