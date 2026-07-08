from __future__ import annotations

import threading
import time


class RateLimiter:
    """Per-domain minimum-interval limiter. One instance per site_id, sequential use only."""

    def __init__(self, requests_per_second: float) -> None:
        self._min_interval_s = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._last_call_ts: float | None = None

    def wait(self) -> None:
        if self._min_interval_s <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if self._last_call_ts is not None:
                elapsed = now - self._last_call_ts
                remaining = self._min_interval_s - elapsed
                if remaining > 0:
                    time.sleep(remaining)
            self._last_call_ts = time.monotonic()


class RateLimiterRegistry:
    """Hands out one RateLimiter per site_id, built from that site's configured rate."""

    def __init__(self) -> None:
        self._limiters: dict[str, RateLimiter] = {}

    def get(self, site_id: str, requests_per_second: float) -> RateLimiter:
        if site_id not in self._limiters:
            self._limiters[site_id] = RateLimiter(requests_per_second)
        return self._limiters[site_id]
