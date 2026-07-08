# poke_tracker

A personal Pokémon TCG price/stock/restock monitor across French, Belgian, Dutch, and Irish
retailers. It scrapes a configurable list of sites hourly (via GitHub Actions), tracks price
and stock history as JSON committed straight into this repo, and will eventually push Web Push
notifications for restocks, new preorders, and significant price drops.

Design constraints, chosen deliberately: **no paid services, no external accounts, no database.**
Everything lives in this GitHub repo — the JSON files under `data/` *are* the database, GitHub
Actions *is* the job scheduler, and (later) GitHub Pages *is* the frontend host.

## Status

Core scraping engine is live and running hourly via GitHub Actions against 15 real sites
across 4 countries. See [docs/ADDING_A_SITE.md](docs/ADDING_A_SITE.md) for how to add a new
site. The PWA dashboard and Web Push notifications are not built yet (see Roadmap below).

## How it works, end to end

Every hour, `.github/workflows/scrape.yml` runs `python -m poketracker.main`, which:

1. Loads `config/sites.yaml` (which sites, how to scrape them) and `config/products.yaml`
   (the canonical catalog of products/sets worth tracking).
2. For each **enabled** site, fetches its search/category/products.json URL(s) with retry,
   backoff, timeout, and rotating User-Agent (`core/http_client.py`), rate-limited per site
   (`core/rate_limiter.py`).
3. Parses the fetched page into raw listings via that site's plugin (`sites/*.py`).
4. Classifies each listing's title against the product catalog (`filtering/product_matching.py`)
   — does this title match a product we track, and if so which language variant?
5. Runs the smart filter (`filtering/smart_filter.py`) — drop non-Pokémon noise, third-party
   marketplace sellers, and generic single-card clutter (unless it's a card we specifically
   track).
6. Diffs the new state against the last known state (`diffing/event_detector.py`) to detect
   new products, restocks, new preorders, price changes/drops, stock changes, and seller changes.
7. Writes updated state to `data/products/*.json` and appends to `data/history/<month>/<site>.jsonl`.
8. Sends Web Push for notify-worthy events (once VAPID keys are configured — not yet).
9. Commits `data/` back to the repo if anything changed.

**One site failing never breaks the run.** Every site's scrape is wrapped in its own
try/except; a failure is logged to `data/errors/last_run.json` and the run continues. The job
only fails outright if *every* enabled site fails in the same run.

## Repository layout

```text
scraper/
  poketracker/
    core/           # models, HTTP client, rate limiter, base scraper class, the runner
    sites/          # one plugin per site (or a generic platform scraper + config)
    filtering/      # product_matching.py (what does this title match?) +
                     # smart_filter.py (should we track/notify this offer?)
    classification/ # heuristic (free, always on) + optional LLM fallback for ambiguous titles
    diffing/        # hashing, event detection, notification dedup ledger
    storage/        # atomic JSON read/write to data/
    notify/         # Web Push sender (pywebpush + VAPID)
    config.py       # Pydantic schemas for sites.yaml / products.yaml / settings.yaml
    main.py         # CLI entrypoint
  config/
    sites.yaml      # every site: locale, scraper, URLs, filters
    products.yaml   # every product/set/card worth tracking, with matching rules
    settings.yaml   # global timeouts, retry policy, blocked keywords
  tests/            # pytest, mostly fixture-based against real captured HTML/JSON
data/
  products/         # current known offers per product (small JSON, one file per product)
  history/          # append-only per-month/per-site price+stock log (JSONL)
  events/           # dedup ledger so nothing gets notified twice
  errors/           # last run's per-site failures
.github/workflows/
  scrape.yml        # hourly cron + manual dispatch
```

## Sites (15 enabled, 21 documented-but-not-working, 36 total)

Every site plugin is one of three **generic, config-only scrapers** (no code needed per shop)
or a **bespoke plugin** for sites with unusual structure. See `sites.yaml`'s comments for why
each disabled site isn't working.

### Generic scrapers

| Scraper | How it works | Used by |
|---|---|---|
| `generic_shopify` | Fetches Shopify's public `/products.json` endpoint — structured JSON, no HTML parsing, far more stable than scraping markup | DracauGames, RelicTCG, OutpostBrussels, DeBroerGrot, Bescards |
| `generic_prestashop` | Parses PrestaShop search-result pages; prefers schema.org `itemprop` microdata for price/stock, falls back to visible price text + an out-of-stock CSS flag for themes without microdata | Ludifolie, Variantes, BCDJeux, Troll2Jeux |
| `generic_woocommerce` | Parses WooCommerce `?s=<query>&post_type=product` search results; tries the heading's own link, then a configured override, then any link in the card — WooCommerce themes vary a lot in whether the title text is actually linked | Pokelite, OuvreTonBooster, VintiCards, Pokemagic, PKMkaarten, PokiPair |

### Bespoke plugins

| Plugin | Site | Status |
|---|---|---|
| `amazon_fr` | Amazon.fr | Disabled — observed returning empty/blocked responses to plain requests |
| `bol_com` | Bol.com | Disabled — selectors are **explicitly unverified**, the site blocked every fetch attempt during development (Cloudflare). Do not enable without checking real markup first. |

### Working sites by locale

- **France (8):** Ludifolie, Variantes, BCDJeux, Troll2Jeux, DracauGames, RelicTCG, Pokelite, OuvreTonBooster
- **Belgium (2):** OutpostBrussels, VintiCards
- **Netherlands (4):** DeBroerGrot, Bescards, Pokemagic, PKMkaarten
- **Ireland (1):** PokiPair

### Documented-but-disabled sites, and why

No evasion of bot protection is attempted anywhere in this project — a blocked site is
recorded and left disabled, not fought.

- **Cloudflare-blocked** ("Just a moment..." challenge): Keytwo.be, MagicFranco, MediaMarkt NL,
  Spellenrijk, Bol.com, Pokemart.fr/be
- **Enterprise bot protection** (Datadome/Incapsula, 403 on plain request): Fnac, Cultura,
  Micromania, King Jouet, Carrefour, Smyths Toys FR
- **JS-only SPA, no server-rendered product data** (confirmed by direct fetch, not assumed):
  CeesCards (Vue/headless, huge real catalog but the grid loads client-side — only a small
  typeahead endpoint is static), EuroTCG (Next.js), PokéCardShop.be (Wix), Leclerc (Angular)
- **Fingerprint-gated redirect**: PicWicToys (FingerprintJS challenge before serving content)
- **Real but not currently operational**: BelgiumCardsGame (Odoo shop mid-migration, serving an
  upgrade placeholder)
- **Real but unconfirmed selectors**: Smartoys.be (custom platform, no verified search URL),
  LePtitPoucet (WooCommerce, but its `?s=` search endpoint returns generic blog-search results
  instead of the product catalog)

Any of these could be revisited later — e.g. with Playwright for the JS-only sites — but that's
a deliberate scope decision, not an oversight.

## Product catalog (`config/products.yaml`)

57 products across three product lines, driven entirely by config — no code changes needed to
add a new product or set.

### How matching works

A listing's title only matches a product if it passes **`match_keywords`**: a list of AND-groups,
where each group is a list of OR'd synonyms. *Every* group must have a hit. This exists because
generic words ("coffret", "pokemon", "collection") are shared by nearly every listing and score
far too high with fuzzy matching alone — a product like `30th-etb` requires *both* an
anniversary-line keyword (`30th`/`célébration`/`30 ans`/`30-jarig jubileum`) *and* an ETB-type
keyword (`etb`/`elite trainer`/`dresseur d'élite`). This is what lets a generic product type
like "ETB" — which alone would match every Pokémon set ever released — be scoped to one specific
set. Among keyword-qualified candidates, fuzzy string similarity (`rapidfuzz`) picks the best match.

### Product lines

- **30th Anniversary Celebration** (5 waves, Sept–Dec 2026): ETBs, Ultra Premium Collections
  (Day/Night), ex Boxes, Figure Collections, Battle Decks, Tech Sticker Collections, Mini Tins,
  and more. `priority` (1–5) and `release_date` are carried through from the original wishlist —
  informational for now, useful for a future dashboard sort order. **MSRP values are estimates**
  (none of these products have official pricing yet) — correct them once real pricing lands;
  `tolerance_pct` absorbs some of the estimate error in the meantime.
- **Héros Transcendants (ME2.5)**: a real, currently-selling set — ETB, Booster Bundle, UPC,
  named character coffrets (Méga-Aligatueur ex, Méga-Florizarre ex, Méga-Dracaufeu X ex, Poster
  Premium Lucario/Gardevoir), Mini Tins, Tripacks, Blisters, and boosters/displays.
- **Rivalités Destinées (EV10)**: ETB, Booster Bundle, Display, Blisters, Build & Battle
  Box/Stadium, Portfolio, Decks — generic product types scoped to this specific set the same way.

### English print-language tracking

7 products have a parallel `-en` entry (`language: "EN"` vs the default `"FR"`) for the
priority-5 30th Celebration items: ETB, Poster Collection, Sylveon/Greninja ex Box, Knock Out
Collection, UPC Day/Night. A site only participates in this disambiguation if
`language_variants_enabled: true` is set for it — currently **Pokemart.be, PKMkaarten.nl,
Bescards, and PokiPair** only, since those are the sites confirmed to actually carry English
print (see `product_matching.py`'s `detect_language_marker`):

- An explicit marker in the title ("English", "Engelse versie", "Française", "(FR)"...) picks
  the matching variant directly.
- No marker → falls back to the site's `default_language` ("default" for most sites; PokiPair
  is set to `"EN"` since its entire catalog is English-only).
- If no EN counterpart is configured yet for a given product (most of the catalog — this was
  rolled out for the priority-5 items "to start"), the language filter is skipped rather than
  losing the match: a lone default-language product still matches regardless of a marker with
  nothing to compare against.
- Sites *without* `language_variants_enabled` can never match an EN-tagged product at all, even
  if "English" happens to appear in a title — this is what keeps a stray word from misfiring on
  a site that doesn't actually stock English print.

Real finding from live testing: OutpostBrussels' catalog already lists the *entire* 30th
Celebration line with `-en-` URL slugs (e.g. `pokemon-30th-celebration-greninja-ex-box-en-s`),
but it's not in the 4-site allowlist above, so it correctly still matches the default (non-EN)
product rather than the EN variant. Worth adding to the allowlist if that scope should expand.

### Single cards

Most of the catalog is sealed product (`category: sealed`, the default). A handful of specific
single cards use `category: single_card` instead — currently 3 illustrative picks tied to the
30th Celebration line (a Pikachu anniversary promo, Mew ex and Sylveon ex Special Illustration
Rares graded PSA 10). These are representative examples, **not confirmed official card
numbers** — this product line hasn't released yet, so there's no real singles market to check
against. The point of `category: single_card` is filtering, not completeness: `settings.yaml`'s
`blocked_keywords_any` (`"carte à l'unité"`, `"losse kaart"`, etc.) drops generic single-card
marketplace noise, since we mostly care about sealed product — but a listing that already
matched a configured `single_card` product is exempt from that block. This required looking up
the matched product *before* running the smart filter in `runner.py`, not after.

### Marketplace sites (Amazon, Bol.com)

Marketplace sites list third-party sellers alongside first-party stock. Setting `only_seller:
"Amazon"` (or `"bol.com"`) in a site's config means only offers whose `seller` field contains
that substring pass the filter — everything else is a third-party/scalper listing and gets
dropped. This is a plain config value, not a per-site code path: adding a third marketplace
site needs zero code changes (`tests/test_smart_filter.py` has a regression test proving this
with a synthetic example).

## Data storage (`data/`)

- `data/products/<product_id>.json` — current known offers for that product, keyed by a stable
  `product_key` hash of (site, product, normalized URL). Small, diff-friendly commits each hour.
- `data/history/<YYYY-MM>/<site>.jsonl` — append-only price/stock snapshot per offer per run,
  regardless of whether anything changed. Powers a future price-history chart. Never causes
  merge conflicts.
- `data/events/notified.json` — dedup ledger keyed by a hash of (product, event type, state) so
  the same restock/price-drop is never pushed twice, with no timestamp/TTL bookkeeping needed.
- `data/errors/last_run.json` — every site that failed in the most recent run, and why.
- `data/subscriptions.json` — Web Push subscriptions (not populated yet).

## Running locally

```bash
cd scraper
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/                    # 48 tests, mostly fixture-based against real captured pages
python -m poketracker.main -v    # scrapes all enabled sites, writes to ../data/
```

Results land in `../data/`. Nothing is sent anywhere without `VAPID_PRIVATE_KEY` set (push
notifications aren't wired up yet — see Roadmap).

## GitHub Actions (`.github/workflows/scrape.yml`)

Runs hourly (`cron: "0 * * * *"`) plus manual `workflow_dispatch`. Checks out the repo, installs
the scraper, runs it, reports per-site errors as a step summary (via `jq`, no fragile embedded
Python in the workflow YAML), and commits `data/` back to `main` only if something actually
changed — no empty commits. A `concurrency` guard prevents overlapping runs. Optional secrets
(`OPENAI_API_KEY`, `VAPID_PRIVATE_KEY`/`VAPID_PUBLIC_KEY`/`VAPID_CONTACT_EMAIL`) are read but
never required — their absence just disables that feature, never breaks the run.

## Adding a new site

See [docs/ADDING_A_SITE.md](docs/ADDING_A_SITE.md). Short version: if it's Shopify, WooCommerce,
or PrestaShop, it's usually a config-only addition (`scraper_class` + `start_urls`). Otherwise,
write a small plugin implementing `fetch_listing_urls` + `parse_listing_page`
(`core/base_scraper.py`). Always verify the site is actually reachable and fingerprint its
platform before writing selectors — don't guess.

## Optional LLM classification

`classification/heuristic_classifier.py` (keyword + fuzzy matching, free, always on) handles
the vast majority of titles. `classification/llm_classifier.py` only runs for titles the
heuristic couldn't confidently place, and only if `OPENAI_API_KEY` is set — its absence never
breaks anything (the import itself is lazy). Not currently needed in practice.

## Roadmap

1. ~~Core scraping engine + pilot sites, manual runs~~ — done
2. ~~Full site coverage + hourly Actions cron~~ — done (15 sites across FR/BE/NL/IE)
3. **PWA read-only dashboard on GitHub Pages** — not started
4. **Web Push notifications** — VAPID keys, service worker subscribe flow, a
   `workflow_dispatch`-based subscription registration (no backend, no standing credential in
   the client bundle) — not started
5. Stretch: LLM classification tuning, more sites (JS-rendering via Playwright for the
   confirmed-but-SPA sites, real verification of Bol.com/Smartoys selectors)

## Known limitations

- No JS rendering: several confirmed-real sites (CeesCards, EuroTCG, PokéCardShop.be, Leclerc)
  need a real browser to scrape and aren't implemented.
- `bol_com.py`'s selectors are unverified against a live page — treat it as a starting point,
  not a working scraper, until checked.
- MSRP values for unreleased products (30th Celebration waves) are estimates.
- The 3 configured single cards are illustrative, not a confirmed official card list.
- `priority`/`release_date`/`locale` fields are informational only — not yet wired into any
  filtering, sorting, or notification behavior.
