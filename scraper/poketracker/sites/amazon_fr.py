from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from poketracker.config import SiteConfig
from poketracker.core.base_scraper import SiteScraper
from poketracker.core.models import RawListing
from poketracker.sites.registry import register_site


@register_site("amazon_fr")
class AmazonFrScraper(SiteScraper):
    """Bespoke plugin for amazon.fr search results. Amazon runs aggressive bot mitigation
    (observed returning empty 202 responses to plain requests during development) — this is
    expected to land in data/errors/last_run.json most runs rather than to reliably succeed.
    Kept disabled by default in sites.yaml; the seller_filter ('sold_by_amazon_only') is only
    a best-effort signal since Amazon's search results don't expose the seller directly."""

    def fetch_listing_urls(self, cfg: SiteConfig) -> list[str]:
        return cfg.start_urls

    def parse_listing_page(self, html: str, url: str, cfg: SiteConfig) -> list[RawListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []

        for item in soup.select('div[data-component-type="s-search-result"]'):
            title_el = item.select_one("h2 span")
            link_el = item.select_one("h2 a")
            if title_el is None or link_el is None or not link_el.get("href"):
                continue

            price_el = item.select_one("span.a-price > span.a-offscreen")
            price = None
            if price_el:
                price = _parse_price(price_el.get_text(strip=True))

            availability_text = item.get_text(" ", strip=True).lower()
            in_stock = "indisponible" not in availability_text and "actuellement indisponible" not in availability_text

            listings.append(
                RawListing(
                    site_id=cfg.site_id,
                    title=title_el.get_text(strip=True),
                    url=urljoin(cfg.base_url, link_el["href"]),
                    price=price,
                    in_stock=in_stock,
                    is_preorder="précommander" in availability_text,
                    seller="Amazon" if "amazon" in availability_text else None,
                )
            )

        return listings


def _parse_price(text: str) -> float | None:
    cleaned = text.replace("\xa0", "").replace("€", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
