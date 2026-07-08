from __future__ import annotations

import json
import logging
import os

from pywebpush import WebPushException, webpush

from poketracker.core.models import Event
from poketracker.storage.json_store import DataStore

log = logging.getLogger("poketracker.notify")


def _build_payload(events: list[Event]) -> dict:
    if len(events) == 1:
        e = events[0]
        return {"title": "PokeTracker Alert", "body": e.message, "url": e.url, "event_type": e.event_type.value}

    by_type: dict[str, int] = {}
    for e in events:
        by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
    summary = ", ".join(f"{count} {etype.replace('_', ' ')}" for etype, count in by_type.items())
    return {"title": "PokeTracker Alert", "body": summary, "url": "/", "event_type": "batch"}


def send_notifications(store: DataStore, events: list[Event]) -> None:
    if not events:
        return

    private_key = os.environ.get("VAPID_PRIVATE_KEY")
    if not private_key:
        log.warning("VAPID_PRIVATE_KEY not set, skipping %d notification(s)", len(events))
        return

    subscriptions = store.load_subscriptions()
    if not subscriptions:
        log.warning("No push subscriptions registered, skipping %d notification(s)", len(events))
        return

    payload = json.dumps(_build_payload(events))
    claims = {"sub": os.environ.get("VAPID_CONTACT_EMAIL", "mailto:admin@example.com")}

    still_valid: list[dict] = []
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=dict(claims),
            )
            still_valid.append(subscription)
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (404, 410):
                log.info("subscription expired, removing")
                continue
            log.error("push failed: %s", exc)
            still_valid.append(subscription)

    if len(still_valid) != len(subscriptions):
        store.save_subscriptions(still_valid)
