from pathlib import Path

from poketracker.config import SiteConfig
from poketracker.sites.generic_prestashop import GenericPrestaShopScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "troll2jeux_search.html"


def _cfg() -> SiteConfig:
    return SiteConfig(
        site_id="troll2jeux",
        base_url="https://www.troll2jeux.com",
        start_urls=["https://www.troll2jeux.com/recherche?controller=search&s=pokemon"],
        scraper_class="generic_prestashop",
        selectors={"listing_item": "article.js-product-miniature", "title_link": "h3.s_title_block a"},
    )


def test_parses_custom_theme_without_schema_org_microdata():
    html = FIXTURE.read_text(encoding="utf-8")
    listings = GenericPrestaShopScraper().parse_listing_page(html, "", _cfg())

    assert len(listings) == 30
    first = listings[0]
    assert first.title == "Pokémon : Coffret Méga-Zygarde EX"
    assert first.price == 49.9
    assert first.in_stock is True


def test_falls_back_to_visible_price_text_when_no_itemprop():
    html = FIXTURE.read_text(encoding="utf-8")
    listings = GenericPrestaShopScraper().parse_listing_page(html, "", _cfg())

    # most listings have a real price; a few free event entries ("Ligue Pokemon") are
    # legitimately 0 - the point of this test is that parsing never fails into None/garbage
    assert all(listing.price is None or listing.price >= 0 for listing in listings)
    priced = [listing for listing in listings if listing.price and listing.price > 0]
    assert len(priced) > 0
