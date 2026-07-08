from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path: Path, data: Any) -> None:
    """Write via a temp file + rename so a crash mid-write never leaves a corrupt/partial JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=_default, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, path)


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, default=_default, ensure_ascii=False))
            f.write("\n")


class DataStore:
    """All reads/writes to the committed data/ directory go through here."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load_product_offers(self, product_id: str) -> dict[str, dict[str, Any]]:
        path = self.data_dir / "products" / f"{product_id}.json"
        return load_json(path, {"product_id": product_id, "offers": {}})["offers"]

    def save_product_offers(self, product_id: str, offers: dict[str, dict[str, Any]]) -> None:
        path = self.data_dir / "products" / f"{product_id}.json"
        atomic_write_json(path, {"product_id": product_id, "offers": offers})

    def append_history(self, site_id: str, month: str, rows: list[dict[str, Any]]) -> None:
        path = self.data_dir / "history" / month / f"{site_id}.jsonl"
        append_jsonl(path, rows)

    def load_notified(self) -> list[str]:
        path = self.data_dir / "events" / "notified.json"
        return load_json(path, {"event_hashes": []})["event_hashes"]

    def save_notified(self, event_hashes: list[str]) -> None:
        path = self.data_dir / "events" / "notified.json"
        atomic_write_json(path, {"event_hashes": event_hashes})

    def save_errors(self, errors: list[dict[str, Any]]) -> None:
        path = self.data_dir / "errors" / "last_run.json"
        atomic_write_json(path, {"errors": errors, "run_at": datetime.now().isoformat()})

    def load_subscriptions(self) -> list[dict[str, Any]]:
        path = self.data_dir / "subscriptions.json"
        return load_json(path, {"subscriptions": []})["subscriptions"]

    def save_subscriptions(self, subscriptions: list[dict[str, Any]]) -> None:
        path = self.data_dir / "subscriptions.json"
        atomic_write_json(path, {"subscriptions": subscriptions})

    def load_seen_urls(self, site_id: str) -> set[str]:
        path = self.data_dir / "products"
        seen: set[str] = set()
        if not path.exists():
            return seen
        for product_file in path.glob("*.json"):
            data = load_json(product_file, {"offers": {}})
            for offer in data["offers"].values():
                if offer.get("site_id") == site_id:
                    seen.add(offer["url"])
        return seen
