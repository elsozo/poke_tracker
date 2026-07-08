from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawListing(BaseModel):
    """What a site plugin's parser produces, before filtering/matching/diffing."""

    site_id: str
    title: str
    url: str
    price: float | None
    currency: str = "EUR"
    in_stock: bool
    is_preorder: bool = False
    seller: str | None = None
    image_url: str | None = None
    scraped_at: datetime = Field(default_factory=utcnow)


class Offer(BaseModel):
    """A RawListing after filtering + product matching + hashing."""

    product_key: str
    site_id: str
    canonical_product_id: str
    url: str
    price: float | None
    currency: str = "EUR"
    in_stock: bool
    is_preorder: bool = False
    seller: str | None = None
    content_hash: str
    first_seen: datetime
    last_seen: datetime


class ProductCategory(StrEnum):
    SEALED = "sealed"
    SINGLE_CARD = "single_card"


class EventType(StrEnum):
    NEW_PRODUCT = "new_product"
    NEW_URL = "new_url"
    NEW_PAGE = "new_page"
    RESTOCK = "restock"
    NEW_PREORDER = "new_preorder"
    PRICE_CHANGE = "price_change"
    PRICE_DROP_SIGNIFICANT = "price_drop_significant"
    STOCK_CHANGE = "stock_change"
    SELLER_CHANGE = "seller_change"


class Event(BaseModel):
    event_type: EventType
    product_key: str
    site_id: str
    canonical_product_id: str
    url: str
    price: float | None
    previous_price: float | None = None
    message: str
    event_hash: str


class SiteError(BaseModel):
    site_id: str
    error: str
    traceback: str | None = None
    ts: datetime = Field(default_factory=utcnow)
