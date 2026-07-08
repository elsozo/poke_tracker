from __future__ import annotations


def parse_price(text: str) -> float | None:
    """Parse a price that may be plain ("24.9", from schema.org microdata) or French-formatted
    visible text ("49,90 €", with non-breaking spaces). Shared by every HTML-based site plugin."""
    cleaned = text.replace("\xa0", "").replace("€", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
