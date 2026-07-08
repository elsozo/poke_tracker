from __future__ import annotations

import json

from poketracker.config import SiteConfig
from poketracker.core.base_scraper import SiteScraper
from poketracker.core.models import RawListing
from poketracker.filtering.product_matching import looks_like_pokemon
from poketracker.sites.registry import register_site

PREORDER_KEYWORDS = ("précommande", "precommande", "pre-order", "preorder")


@register_site("generic_shopify")
class GenericShopifyScraper(SiteScraper):
    """Config-driven scraper for Shopify boutique shops, using Shopify's public
    `/products.json` storefront endpoint instead of HTML parsing — it's structured JSON,
    enabled by default on Shopify stores, and far more stable than scraping markup.
    Adding a new Shopify shop needs no new code: one sites.yaml entry with
    `scraper_class: generic_shopify` and `base_url` set."""

    def fetch_listing_urls(self, cfg: SiteConfig) -> list[str]:
        return cfg.start_urls or [f"{cfg.base_url.rstrip('/')}/products.json?limit=250"]

    def parse_listing_page(self, html: str, url: str, cfg: SiteConfig) -> list[RawListing]:
        data = json.loads(html)
        listings: list[RawListing] = []

        for product in data.get("products", []):
            title = product.get("title", "")
            if not looks_like_pokemon(title) and not looks_like_pokemon(product.get("product_type", "")):
                continue

            variants = product.get("variants", [])
            if not variants:
                continue

            prices = [float(v["price"]) for v in variants if v.get("price") is not None]
            in_stock = any(v.get("available") for v in variants)
            lowered_title = title.lower()

            listings.append(
                RawListing(
                    site_id=cfg.site_id,
                    title=title,
                    url=f"{cfg.base_url.rstrip('/')}/products/{product['handle']}",
                    price=min(prices) if prices else None,
                    in_stock=in_stock,
                    is_preorder=any(kw in lowered_title for kw in PREORDER_KEYWORDS),
                    seller=None,
                )
            )

        return listings
