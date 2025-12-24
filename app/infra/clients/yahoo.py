from __future__ import annotations

from app.infra.clients.http_client import HttpClient
from app.infra.logger import setup_logging
from app.infra.secrets import get_secret


def search_offers(keyword: str) -> list[dict]:
    app_id = _get_secret_safe("yahoo_client_id")
    if not app_id or not keyword:
        return []

    client = HttpClient(min_interval=1.0)
    try:
        response = client.get(
            "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
            params={
                "appid": app_id,
                "query": keyword,
                "results": 10,
                "sort": "+price",
            },
        )
        data = response.json()
        items = data.get("hits", [])
        return [_normalize_item(item) for item in items]
    finally:
        client.close()


def _normalize_item(item: dict) -> dict:
    price = item.get("price")
    shipping = item.get("shipping")
    shipping_cost = None
    if isinstance(shipping, dict):
        shipping_cost = shipping.get("price")
    return {
        "title": item.get("name"),
        "price": price,
        "shipping": shipping_cost,
        "stock_status": item.get("inStock"),
        "url": item.get("url"),
        "confidence": None,
        "raw_text": None,
    }


def _get_secret_safe(key: str) -> str | None:
    try:
        return get_secret(key)
    except RuntimeError:
        setup_logging().warning("keyring unavailable for %s", key)
        return None
