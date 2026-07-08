from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from poketracker.core.models import ProductCategory


class SiteConfig(BaseModel):
    site_id: str
    enabled: bool = True
    priority: str = "B"
    locale: str = "FR"  # country/locale this site ships from - FR, BE, NL, IE, ...
    base_url: str
    start_urls: list[str] = Field(default_factory=list)
    scraper_class: str | None = None  # defaults to site_id if unset
    needs_browser: bool = False
    # Marketplace sites (Amazon, Bol.com, ...) list third-party sellers alongside first-party
    # stock. Set only_seller to a substring that must appear in an offer's seller field for it
    # to pass the smart filter - e.g. "Amazon" or "bol.com". A new marketplace site needs zero
    # code changes: just this one config value, matched case-insensitively at filter time.
    only_seller: str | None = None
    # Enables the EN-vs-default print-language disambiguation in product_matching.py for this
    # site's offers. Restricted to sites confirmed to actually stock English-print product.
    language_variants_enabled: bool = False
    # When a title has no explicit language marker, which language to assume - "default" (the
    # site's local FR/NL print) or "EN" (for sites like PokiPair whose whole catalog is English).
    default_language: str = "default"
    rate_limit_rps: float = 0.5
    timeout_s: float = 15.0
    selectors: dict[str, str] = Field(default_factory=dict)


class ProductConfig(BaseModel):
    id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    # Each element is an OR-group (any keyword in it counts as a hit); a title must hit
    # EVERY group to match (AND across groups). A plain string is shorthand for a 1-item
    # OR-group. This is what lets "ETB" (too generic alone) be scoped to a specific set via
    # a second group like ["héros transcendants", "me2.5"].
    match_keywords: list[str | list[str]] = Field(default_factory=list)
    priority: int = 3  # 1-5, from the user's own star ratings; informational for now
    release_date: str | None = None  # ISO date, informational
    language: str = "FR"  # print language of this listing: FR, EN, NL, ...
    category: ProductCategory = ProductCategory.SEALED
    msrp_eur: float
    tolerance_pct: float = 20.0

    @property
    def max_accepted_price(self) -> float:
        return self.msrp_eur * (1 + self.tolerance_pct / 100)


class ClassificationSettings(BaseModel):
    confidence_threshold: float = 0.75
    model: str = "gpt-4o-mini"


class Settings(BaseModel):
    request_timeout_s: float = 15.0
    retry_total: int = 3
    retry_backoff_factor: float = 0.5
    retry_status_forcelist: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])
    user_agents: list[str] = Field(default_factory=list)
    significant_price_drop_pct: float = 10.0
    # Listings whose title contains any of these are dropped UNLESS they match a configured
    # single-card product - e.g. "carte à l'unité" ("single card") is noise when we only track
    # sealed product, but must not block the specific singles we do configure (see smart_filter).
    blocked_keywords_any: list[str] = Field(default_factory=list)
    classification: ClassificationSettings = Field(default_factory=ClassificationSettings)


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_sites(config_dir: Path) -> list[SiteConfig]:
    data = _load_yaml(config_dir / "sites.yaml") or {}
    return [SiteConfig(site_id=site_id, **cfg) for site_id, cfg in (data.get("sites") or {}).items()]


def load_products(config_dir: Path) -> list[ProductConfig]:
    data = _load_yaml(config_dir / "products.yaml") or {}
    return [ProductConfig(**entry) for entry in (data.get("products") or [])]


def load_settings(config_dir: Path) -> Settings:
    data = _load_yaml(config_dir / "settings.yaml") or {}
    return Settings(**data)
