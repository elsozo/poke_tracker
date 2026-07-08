from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from poketracker.config import SiteConfig
from poketracker.core.base_scraper import SiteScraper
from poketracker.core.models import RawListing
from poketracker.sites.registry import register_site

PREORDER_KEYWORDS = ("précommande", "precommande", "pre-order", "preorder")

_DEFAULT_SELECTORS = {
    "listing_item": ".product-miniature-wrapper, .js-product-miniature-wrapper",
    "title_link": ".product-title a",
    "price": "[itemprop=price]",
    "availability": "[itemprop=availability]",
}


@register_site("generic_prestashop")
class GenericPrestaShopScraper(SiteScraper):
    """Config-driven scraper for the many boutique shops running default-theme PrestaShop,
    which expose schema.org Offer microdata on their category/search listing pages.
    Adding a new PrestaShop shop needs no new code: one sites.yaml entry with
    `scraper_class: generic_prestashop` and a `start_urls` search/category URL."""

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
            price = float(price_el.get_text(strip=True)) if price_el else None

            availability_el = item.select_one(selectors["availability"])
            in_stock = bool(availability_el) and "instock" in availability_el.get_text(strip=True).lower()

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
