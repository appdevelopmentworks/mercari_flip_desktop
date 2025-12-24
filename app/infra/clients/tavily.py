from __future__ import annotations

import re

from app.infra.clients.http_client import HttpClient
from app.infra.logger import setup_logging
from app.infra.secrets import get_secret


def search_offers(keyword: str) -> list[dict]:
    api_key = _get_secret_safe("tavily_api_key")
    if not api_key or not keyword:
        return []

    client = HttpClient(min_interval=1.0)
    try:
        response = client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": keyword,
                "search_depth": "basic",
                "max_results": 5,
                "include_raw_content": True,
            },
        )
        data = response.json()
        results = data.get("results", [])
        offers = []
        for entry in results:
            price = _extract_price(entry.get("title"), entry.get("content"), entry.get("raw_content"))
            offers.append(
                {
                    "title": entry.get("title"),
                    "price": price,
                    "shipping": None,
                    "stock_status": None,
                    "url": entry.get("url"),
                    "confidence": entry.get("score"),
                    "raw_text": entry.get("content") or entry.get("raw_content"),
                }
            )
        return offers
    finally:
        client.close()


def _get_secret_safe(key: str) -> str | None:
    try:
        return get_secret(key)
    except RuntimeError:
        setup_logging().warning("keyring unavailable for %s", key)
        return None


def _extract_price(*texts: str | None) -> int | None:
    candidates: list[int] = []
    pattern = re.compile(r"(?:¥|￥)\s*([0-9][0-9,]{1,})|([0-9][0-9,]{1,})\s*円")
    for text in texts:
        if not text:
            continue
        for match in pattern.finditer(text):
            value = match.group(1) or match.group(2)
            if not value:
                continue
            numeric = int(value.replace(",", ""))
            if 100 <= numeric <= 10_000_000:
                candidates.append(numeric)
    if not candidates:
        return None
    return min(candidates)
