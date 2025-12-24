from __future__ import annotations

from typing import Any

from app.infra.logger import setup_logging
from app.infra.secrets import get_secret
from app.infra.clients.http_client import HttpClient


def search_offers(keyword: str) -> list[dict]:
    app_id = _get_secret_safe("rakuten_app_id")
    if not app_id or not keyword:
        return []

    client = HttpClient(min_interval=1.0)
    try:
        response = client.get(
            "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706",
            params={
                "applicationId": app_id,
                "keyword": keyword,
                "hits": 10,
                "sort": "+itemPrice",
            },
        )
        data = response.json()
        items = data.get("Items", [])
        return [_normalize_item(entry.get("Item", {})) for entry in items]
    finally:
        client.close()


def _normalize_item(item: dict[str, Any]) -> dict:
    price = item.get("itemPrice")
    shipping = item.get("postageFlag")
    shipping_cost = 0 if shipping == 1 else None
    return {
        "title": item.get("itemName"),
        "price": price,
        "shipping": shipping_cost,
        "stock_status": "available" if item.get("availability") else None,
        "url": item.get("itemUrl"),
        "confidence": None,
        "raw_text": None,
    }


def _get_secret_safe(key: str) -> str | None:
    try:
        return get_secret(key)
    except RuntimeError:
        setup_logging().warning("keyring unavailable for %s", key)
        return None
