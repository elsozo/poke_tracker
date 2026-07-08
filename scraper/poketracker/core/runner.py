from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from poketracker.classification import heuristic_classifier, llm_classifier
from poketracker.config import ProductConfig, Settings, SiteConfig
from poketracker.core.http_client import build_session, fetch
from poketracker.core.models import Event, Offer, SiteError
from poketracker.core.rate_limiter import RateLimiterRegistry
from poketracker.diffing.dedup_store import DedupLedger
from poketracker.diffing.event_detector import NOTIFY_WORTHY, diff_offer
from poketracker.diffing.hashing import content_hash, product_key
from poketracker.filtering.smart_filter import should_notify, should_track
from poketracker.sites.registry import discover_sites, get_scraper
from poketracker.storage.json_store import DataStore

log = logging.getLogger("poketracker.runner")


class RunResult:
    def __init__(self) -> None:
        self.errors: list[SiteError] = []
        self.notify_events: list[Event] = []
        self.sites_run = 0
        self.sites_failed = 0
        self.offers_seen = 0


def _classify(title: str, products: list[ProductConfig], settings: Settings, site_cfg: SiteConfig):
    result = heuristic_classifier.classify(
        title,
        products,
        language_variants_enabled=site_cfg.language_variants_enabled,
        default_language=site_cfg.default_language,
    )
    threshold = settings.classification.confidence_threshold * 100
    if result.confidence < threshold and llm_classifier.is_available():
        llm_result = llm_classifier.classify(title, products, settings)
        if llm_result is not None:
            return llm_result
    return result


def run(
    store: DataStore,
    sites: list[SiteConfig],
    products: list[ProductConfig],
    settings: Settings,
) -> RunResult:
    result = RunResult()
    discover_sites()
    session = build_session(settings)
    limiters = RateLimiterRegistry()
    dedup = DedupLedger(store)
    products_by_id = {p.id: p for p in products}

    offers_cache: dict[str, dict[str, dict]] = {}  # canonical_product_id -> {product_key: offer_dict}
    history_batches: dict[str, list[dict]] = {}  # site_id -> rows
    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")

    enabled_sites = [s for s in sites if s.enabled]

    for site_cfg in enabled_sites:
        result.sites_run += 1
        limiter = limiters.get(site_cfg.site_id, site_cfg.rate_limit_rps)

        def fetch_fn(sess, url, cfg_settings, timeout_s=None):
            limiter.wait()
            return fetch(sess, url, cfg_settings, timeout_s=timeout_s)

        try:
            scraper = get_scraper(site_cfg.site_id, site_cfg.scraper_class)
            raw_listings = scraper.fetch_and_parse(site_cfg, session, settings, fetch_fn)
        except Exception as exc:  # noqa: BLE001 - a single site's failure must never kill the run
            result.sites_failed += 1
            result.errors.append(
                SiteError(site_id=site_cfg.site_id, error=str(exc), traceback=traceback.format_exc())
            )
            log.error("site %s failed: %s", site_cfg.site_id, exc)
            continue

        for listing in raw_listings:
            classification = _classify(listing.title, products, settings, site_cfg)
            product_cfg = (
                products_by_id.get(classification.canonical_product_id)
                if classification.canonical_product_id
                else None
            )

            # product_cfg is looked up before should_track so a configured single-card product
            # can override a generic blocked keyword (e.g. "carte à l'unité") that would
            # otherwise drop it - see should_track's matched_product/blocked_keywords params.
            if not should_track(
                listing,
                site_cfg,
                classification.is_pokemon,
                matched_product=product_cfg,
                blocked_keywords=tuple(settings.blocked_keywords_any),
            ):
                continue
            if product_cfg is None:
                continue

            key = product_key(site_cfg.site_id, product_cfg.id, listing.url)
            if product_cfg.id not in offers_cache:
                offers_cache[product_cfg.id] = store.load_product_offers(product_cfg.id)
            offers = offers_cache[product_cfg.id]

            previous_dict = offers.get(key)
            previous_offer = Offer(**previous_dict) if previous_dict else None
            c_hash = content_hash(listing.price, listing.in_stock, listing.is_preorder, listing.seller)

            current_offer = Offer(
                product_key=key,
                site_id=site_cfg.site_id,
                canonical_product_id=product_cfg.id,
                url=listing.url,
                price=listing.price,
                currency=listing.currency,
                in_stock=listing.in_stock,
                is_preorder=listing.is_preorder,
                seller=listing.seller,
                content_hash=c_hash,
                first_seen=previous_offer.first_seen if previous_offer else now,
                last_seen=now,
            )
            result.offers_seen += 1
            offers[key] = current_offer.model_dump()

            history_batches.setdefault(site_cfg.site_id, []).append(
                {
                    "product_key": key,
                    "canonical_product_id": product_cfg.id,
                    "price": listing.price,
                    "in_stock": listing.in_stock,
                    "is_preorder": listing.is_preorder,
                    "ts": now.isoformat(),
                }
            )

            for event in diff_offer(previous_offer, current_offer, settings):
                if (
                    event.event_type in NOTIFY_WORTHY
                    and should_notify(event, current_offer.in_stock, product_cfg)
                    and dedup.is_new(event.event_hash)
                ):
                    result.notify_events.append(event)
                    dedup.mark_sent(event.event_hash)

    for product_id, offers in offers_cache.items():
        store.save_product_offers(product_id, offers)
    for site_id, rows in history_batches.items():
        store.append_history(site_id, month, rows)
    store.save_errors([e.model_dump() for e in result.errors])
    dedup.flush()

    return result
