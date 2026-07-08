from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from poketracker.config import load_products, load_settings, load_sites
from poketracker.core.runner import run
from poketracker.notify.webpush_sender import send_notifications
from poketracker.storage.json_store import DataStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PokeTracker scrape run")
    parser.add_argument("--config-dir", type=Path, default=Path(__file__).resolve().parents[1] / "config")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("poketracker.main")

    sites = load_sites(args.config_dir)
    products = load_products(args.config_dir)
    settings = load_settings(args.config_dir)
    store = DataStore(args.data_dir)

    enabled_count = sum(1 for s in sites if s.enabled)
    log.info("loaded %d sites (%d enabled), %d products", len(sites), enabled_count, len(products))

    result = run(store, sites, products, settings)

    log.info(
        "run complete: %d/%d sites ok, %d offers seen, %d notify-worthy events",
        result.sites_run - result.sites_failed,
        result.sites_run,
        result.offers_seen,
        len(result.notify_events),
    )
    for error in result.errors:
        log.warning("site error: %s: %s", error.site_id, error.error)

    send_notifications(store, result.notify_events)

    if enabled_count > 0 and result.sites_failed == result.sites_run:
        log.error("every enabled site failed this run — treating as a systemic failure")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
