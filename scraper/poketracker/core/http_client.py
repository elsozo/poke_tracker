from __future__ import annotations

import random

import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from poketracker.config import Settings

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
]


def build_session(settings: Settings) -> requests.Session:
    """Shared session factory: retry/backoff on 429/5xx, no site plugin should call requests directly."""
    session = requests.Session()
    retry = Retry(
        total=settings.retry_total,
        backoff_factor=settings.retry_backoff_factor,
        status_forcelist=settings.retry_status_forcelist,
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def random_user_agent(settings: Settings) -> str:
    pool = settings.user_agents or DEFAULT_USER_AGENTS
    return random.choice(pool)


def fetch(session: requests.Session, url: str, settings: Settings, *, timeout_s: float | None = None) -> str:
    """GET a URL with a rotated User-Agent and the settings-configured timeout. Raises on non-2xx."""
    headers = {
        "User-Agent": random_user_agent(settings),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = session.get(url, headers=headers, timeout=timeout_s or settings.request_timeout_s)
    response.raise_for_status()
    return response.text
