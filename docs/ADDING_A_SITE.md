# Adding a new site

Most boutique shops run one of three platforms. If yours matches, **no Python code is
needed** — just a `sites.yaml` entry.

## Shopify (has `/products.json`)

```yaml
my_shop:
  enabled: true
  priority: B
  base_url: "https://www.my-shop.com"
  scraper_class: generic_shopify
```

Verify first: `curl https://www.my-shop.com/products.json?limit=5` should return JSON.

## PrestaShop (default theme, schema.org microdata)

```yaml
my_shop:
  enabled: true
  priority: B
  base_url: "https://www.my-shop.com"
  start_urls:
    - "https://www.my-shop.com/recherche?controller=search&s=pokemon"
  scraper_class: generic_prestashop
```

Verify first: view-source the search URL and look for `.product-miniature-wrapper` and
`itemprop="price"` in the markup. If the theme uses different class names, override via
`selectors: {listing_item: "...", title_link: "...", price: "...", availability: "..."}`.

## WooCommerce (default theme)

```yaml
my_shop:
  enabled: true
  priority: B
  base_url: "https://www.my-shop.com"
  start_urls:
    - "https://www.my-shop.com/?s=pokemon&post_type=product"
  scraper_class: generic_woocommerce
```

Verify first: same idea, look for `li.product` and `.woocommerce-loop-product__title`.

## Anything else — bespoke plugin

Create `poketracker/sites/my_shop.py`:

```python
from poketracker.core.base_scraper import SiteScraper
from poketracker.sites.registry import register_site

@register_site("my_shop")
class MyShopScraper(SiteScraper):
    def fetch_listing_urls(self, cfg):
        return cfg.start_urls

    def parse_listing_page(self, html, url, cfg):
        ...  # BeautifulSoup, return list[RawListing]
```

Then reference it from `sites.yaml` with `scraper_class: my_shop`.

## Before enabling a site

Probe it from the command line first — many big retailers (Amazon, Fnac, Cultura,
Micromania, King Jouet were all observed blocking plain HTTP requests during development
via Datadome/Incapsula) will need `needs_browser: true` (Playwright) at minimum, and some
may not be worth pursuing without residential proxies or a paid anti-bot bypass service —
neither of which this project builds. If a site blocks scraping, leave it `enabled: false`
with a comment rather than spending time fighting it; the runner already treats a blocked
site as a normal per-run error, not a pipeline failure.

## Tuning what gets tracked

A listing is only tracked if it passes `filtering.smart_filter.should_track` (must look like
a Pokémon product, must pass any `seller_filter`) **and** matches a product in
`config/products.yaml` via a `match_keywords` hit (see the comment at the top of that file —
generic words like "coffret"/"pokemon" are deliberately not enough to match). If a real site
run comes back with 0 tracked offers, check `data/errors/last_run.json` first (site failed?)
then check whether `products.yaml`'s `match_keywords` actually correspond to what's currently
listed — retailers reuse generic photos/names across many unrelated sets.
