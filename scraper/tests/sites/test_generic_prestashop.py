from pathlib import Path

from poketracker.config import SiteConfig
from poketracker.sites.generic_prestashop import GenericPrestaShopScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "ludifolie_search.html"


def _cfg() -> SiteConfig:
    return SiteConfig(
        site_id="ludifolie",
        base_url="https://www.ludifolie.com",
        start_urls=["https://www.ludifolie.com/recherche?controller=search&s=pokemon"],
        scraper_class="generic_prestashop",
    )


def test_parses_real_ludifolie_listing_page():
    html = FIXTURE.read_text(encoding="utf-8")
    scraper = GenericPrestaShopScraper()

    listings = scraper.parse_listing_page(html, _cfg().start_urls[0], _cfg())

    assert len(listings) == 24
    first = listings[0]
    assert first.site_id == "ludifolie"
    assert first.title == "Pokémon - Coffret Journée Pokémon 2026"
    assert first.url == "https://www.ludifolie.com/23887-pokemon-coffret-journee-pokemon-2026.html"
    assert first.price == 24.9
    assert first.in_stock is False


def test_finds_at_least_one_in_stock_item():
    html = FIXTURE.read_text(encoding="utf-8")
    listings = GenericPrestaShopScraper().parse_listing_page(html, "", _cfg())

    assert any(listing.in_stock for listing in listings)
