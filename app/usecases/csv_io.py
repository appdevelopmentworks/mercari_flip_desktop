from __future__ import annotations

import csv
from pathlib import Path

from app.infra.db.repo import Calculation, Item, MarketRef, Offer, Repository


def export_items(repo: Repository, path: Path | str) -> None:
    rows = repo.list_items()
    _write_csv(
        path,
        ["id", "name", "search_keyword", "jan", "model_number", "category", "status"],
        [
            [
                item.id,
                item.name or "",
                item.search_keyword,
                item.jan or "",
                item.model_number or "",
                item.category or "",
                item.status,
            ]
            for item in rows
        ],
    )


def export_offers(repo: Repository, item_id: int, path: Path | str) -> None:
    rows = repo.list_offers(item_id)
    _write_csv(
        path,
        [
            "id",
            "item_id",
            "source_id",
            "title",
            "price",
            "shipping",
            "total",
            "stock_status",
            "url",
            "confidence",
            "fetched_at",
        ],
        [list(_offer_to_row(offer)) for offer in rows],
    )


def export_market_refs(repo: Repository, item_id: int, path: Path | str) -> None:
    rows = repo.list_market_refs(item_id)
    _write_csv(
        path,
        ["id", "item_id", "low", "mid", "high", "memo", "ref_date", "created_at"],
        [list(_market_to_row(row)) for row in rows],
    )


def export_calculations(repo: Repository, item_id: int, path: Path | str) -> None:
    rows = repo.list_calculations(item_id)
    _write_csv(
        path,
        [
            "id",
            "item_id",
            "offer_id",
            "sale_price",
            "fee_rate",
            "shipping_cost",
            "packaging_cost",
            "other_cost",
            "cost_price",
            "profit",
            "profit_rate",
            "breakeven_price",
            "target_profit",
            "min_price_for_target",
            "created_at",
        ],
        [list(_calc_to_row(row)) for row in rows],
    )


def import_items(repo: Repository, path: Path | str) -> int:
    items = _read_csv(path)
    count = 0
    for row in items:
        if not row.get("search_keyword"):
            continue
        repo.create_item(
            name=row.get("name") or None,
            search_keyword=row["search_keyword"],
            jan=row.get("jan") or None,
            model_number=row.get("model_number") or None,
            category=row.get("category") or None,
            status=row.get("status") or "considering",
            notes=None,
        )
        count += 1
    return count


def _write_csv(path: Path | str, headers: list[str], rows: list[list]) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _read_csv(path: Path | str) -> list[dict]:
    csv_path = Path(path)
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _offer_to_row(offer: Offer) -> tuple:
    return (
        offer.id,
        offer.item_id,
        offer.source_id,
        offer.title,
        offer.price,
        offer.shipping,
        offer.total,
        offer.stock_status,
        offer.url,
        offer.confidence,
        offer.fetched_at,
    )


def _market_to_row(row: MarketRef) -> tuple:
    return (
        row.id,
        row.item_id,
        row.low,
        row.mid,
        row.high,
        row.memo,
        row.ref_date,
        row.created_at,
    )


def _calc_to_row(row: Calculation) -> tuple:
    return (
        row.id,
        row.item_id,
        row.offer_id,
        row.sale_price,
        row.fee_rate,
        row.shipping_cost,
        row.packaging_cost,
        row.other_cost,
        row.cost_price,
        row.profit,
        row.profit_rate,
        row.breakeven_price,
        row.target_profit,
        row.min_price_for_target,
        row.created_at,
    )
