from pathlib import Path

from poketracker.config import SiteConfig
from poketracker.sites.generic_woocommerce import GenericWooCommerceScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pokelite_search.html"


def _cfg() -> SiteConfig:
    return SiteConfig(
        site_id="pokelite",
        base_url="https://www.pokelite.fr",
        start_urls=["https://www.pokelite.fr/?s=pokemon&post_type=product"],
        scraper_class="generic_woocommerce",
    )


def test_parses_real_pokelite_search_page():
    html = FIXTURE.read_text(encoding="utf-8")
    listings = GenericWooCommerceScraper().parse_listing_page(html, "", _cfg())

    assert len(listings) == 12
    first = listings[0]
    assert first.site_id == "pokelite"
    assert "Tripack" in first.title
    assert first.price == 109.90
    assert first.in_stock is True
    assert first.url.startswith("https://www.pokelite.fr/produit/")
