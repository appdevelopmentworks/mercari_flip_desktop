from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.infra.db.repo import Repository
from app.infra.clients import amazon_paapi, rakuten, tavily, yahoo
from app.infra.logger import setup_logging


@dataclass(frozen=True)
class OfferInput:
    item_id: int
    search_keyword: str


def refresh_offers(repo: Repository, request: OfferInput) -> int:
    logger = setup_logging()
    sources = dict(repo.list_sources())
    fetched_at = datetime.now(timezone.utc).isoformat()

    offers = []
    for name, func in [
        ("rakuten", rakuten.search_offers),
        ("yahoo", yahoo.search_offers),
        ("amazon", amazon_paapi.search_offers),
        ("tavily", tavily.search_offers),
    ]:
        try:
            raw = func(request.search_keyword)
            offers.extend(
                _normalize_offers(
                    raw,
                    request.item_id,
                    sources.get(name),
                    fetched_at,
                )
            )
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("offer refresh failed: %s (%s)", name, exc)

    repo.add_offers(offers)
    return len(offers)


def _normalize_offers(
    raw_offers: list[dict],
    item_id: int,
    source_id: int | None,
    fetched_at: str,
) -> list[dict]:
    results = []
    for offer in raw_offers:
        price = offer.get("price")
        shipping = offer.get("shipping")
        total = None
        if price is not None:
            total = price + (shipping or 0)
        results.append(
            {
                "item_id": item_id,
                "source_id": source_id,
                "title": offer.get("title"),
                "price": price,
                "shipping": shipping,
                "total": total,
                "stock_status": offer.get("stock_status"),
                "url": offer.get("url"),
                "confidence": offer.get("confidence"),
                "fetched_at": fetched_at,
                "raw_text": offer.get("raw_text"),
            }
        )
    return results
