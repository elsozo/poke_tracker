from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

_TRACKING_PARAM_PREFIXES = ("utm_", "ref", "affiliate", "aff_", "tag", "gclid", "fbclid")


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not any(k.lower().startswith(p) for p in _TRACKING_PARAM_PREFIXES)
    ]
    query = urlencode(sorted(kept))
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), query, ""))


def product_key(site_id: str, canonical_product_id: str, url: str) -> str:
    raw = f"{site_id}|{canonical_product_id}|{normalize_url(url)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def content_hash(price: float | None, in_stock: bool, is_preorder: bool, seller: str | None) -> str:
    raw = f"{price}|{in_stock}|{is_preorder}|{seller}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def event_hash(product_key_: str, event_type: str, content_hash_: str) -> str:
    raw = f"{product_key_}|{event_type}|{content_hash_}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
