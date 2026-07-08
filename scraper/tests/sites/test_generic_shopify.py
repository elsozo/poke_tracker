from pathlib import Path

from poketracker.config import SiteConfig
from poketracker.sites.generic_shopify import GenericShopifyScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "dracaugames_products.json"


def _cfg() -> SiteConfig:
    return SiteConfig(
        site_id="dracaugames",
        base_url="https://www.dracaugames.com",
        scraper_class="generic_shopify",
    )


def test_default_listing_url_uses_products_json():
    urls = GenericShopifyScraper().fetch_listing_urls(_cfg())
    assert urls == ["https://www.dracaugames.com/products.json?limit=250"]


def test_filters_to_pokemon_products_only():
    payload = FIXTURE.read_text(encoding="utf-8")
    listings = GenericShopifyScraper().parse_listing_page(payload, "", _cfg())

    # the fixture's first product is a Disney Lorcana display, not Pokemon — must be filtered out
    assert all("lorcana" not in listing.title.lower() for listing in listings)


def test_builds_product_url_from_handle():
    payload = FIXTURE.read_text(encoding="utf-8")
    listings = GenericShopifyScraper().parse_listing_page(payload, "", _cfg())

    for listing in listings:
        assert listing.url.startswith("https://www.dracaugames.com/products/")
        assert listing.price is None or listing.price > 0
