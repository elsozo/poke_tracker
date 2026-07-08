# poke_tracker

Personal Pokemon TCG price/stock/restock monitor for French retailers. Scrapes a
configurable list of sites hourly (via GitHub Actions), tracks price and stock history as
JSON committed into this repo, and (eventually) pushes Web Push notifications for restocks,
new preorders, and significant price drops. No paid services, no external accounts.

## Status

Milestone 1 (core engine + a handful of real pilot sites, manual runs only). See
[docs/ADDING_A_SITE.md](docs/ADDING_A_SITE.md) for how the per-site plugin pattern works.

## Running locally

```bash
cd scraper
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
python -m poketracker.main --config-dir config --data-dir ../data -v
```

Results land in `../data/` (products, price history, per-run errors) — nothing is sent
anywhere without `VAPID_PRIVATE_KEY` set (push notifications aren't wired up yet).
