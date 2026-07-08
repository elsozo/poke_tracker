from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from poketracker.config import Settings, SiteConfig
from poketracker.core.models import RawListing


class SiteScraper(ABC):
    """A site plugin implements only these two methods; everything else (HTTP, retry,
    rate limiting, filtering, matching, diffing, storage, notification) is shared."""

    needs_browser: bool = False

    @abstractmethod
    def fetch_listing_urls(self, cfg: SiteConfig) -> list[str]:
        """Return the URLs to check this run (category/search pages, or a fixed list from cfg)."""

    @abstractmethod
    def parse_listing_page(self, html: str, url: str, cfg: SiteConfig) -> list[RawListing]:
        """Parse one fetched page's HTML into RawListings."""

    def fetch_and_parse(
        self, cfg: SiteConfig, session: requests.Session, settings: Settings, fetch_fn
    ) -> list[RawListing]:
        """Default orchestration: fetch each listing URL via fetch_fn, parse, and flatten.
        fetch_fn is injected by the runner so it can apply rate limiting between calls."""
        listings: list[RawListing] = []
        for url in self.fetch_listing_urls(cfg):
            html = fetch_fn(session, url, settings, timeout_s=cfg.timeout_s)
            listings.extend(self.parse_listing_page(html, url, cfg))
        return listings
