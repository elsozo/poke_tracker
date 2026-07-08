from __future__ import annotations

from poketracker.storage.json_store import DataStore


class DedupLedger:
    """Guarantees we never send a push notification twice for the same (product, event, state)."""

    def __init__(self, store: DataStore) -> None:
        self._store = store
        self._seen: set[str] = set(store.load_notified())

    def is_new(self, event_hash: str) -> bool:
        return event_hash not in self._seen

    def mark_sent(self, event_hash: str) -> None:
        self._seen.add(event_hash)

    def flush(self) -> None:
        self._store.save_notified(sorted(self._seen))
