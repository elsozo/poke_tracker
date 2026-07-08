from __future__ import annotations

import importlib
import pkgutil

from poketracker.core.base_scraper import SiteScraper

_REGISTRY: dict[str, type[SiteScraper]] = {}


def register_site(site_id: str):
    def decorator(cls: type[SiteScraper]) -> type[SiteScraper]:
        _REGISTRY[site_id] = cls
        return cls

    return decorator


def discover_sites() -> dict[str, type[SiteScraper]]:
    """Import every module under poketracker.sites so their @register_site decorators run."""
    import poketracker.sites as sites_pkg

    for module_info in pkgutil.iter_modules(sites_pkg.__path__):
        if module_info.name == "registry":
            continue
        importlib.import_module(f"poketracker.sites.{module_info.name}")
    return dict(_REGISTRY)


def get_scraper(site_id: str, scraper_class: str | None) -> SiteScraper:
    key = scraper_class or site_id
    if key not in _REGISTRY:
        raise KeyError(f"No scraper registered for '{key}'. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[key]()
