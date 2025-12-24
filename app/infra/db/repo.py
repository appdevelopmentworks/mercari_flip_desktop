from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def default_db_path() -> Path:
    return Path("data") / "app.db"


def init_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _apply_schema(conn)
    _ensure_schema_version(conn, version=1)
    _seed_sources(conn)
    _seed_shipping_rules(conn)
    return conn


def _apply_schema(conn: sqlite3.Connection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def _ensure_schema_version(conn: sqlite3.Connection, version: int) -> None:
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current = row[0] if row else None
    if current is None or current < version:
        applied_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
            (version, applied_at),
        )
        conn.commit()


def _seed_sources(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM sources").fetchone()
    if existing and existing[0] > 0:
        return
    sources = [
        ("rakuten", "rakuten.co.jp"),
        ("yahoo", "shopping.yahoo.co.jp"),
        ("amazon", "amazon.co.jp"),
        ("tavily", "tavily.com"),
        ("manual_url", None),
    ]
    conn.executemany(
        "INSERT INTO sources(name, domain, enabled) VALUES (?, ?, 1)", sources
    )
    conn.commit()


def _seed_shipping_rules(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM shipping_rules").fetchone()
    if existing and existing[0] > 0:
        return
    data_path = Path("data") / "shipping_rules.csv"
    template_path = Path("templates") / "shipping_rules.seed.csv"
    source = data_path if data_path.exists() else template_path
    if not source.exists():
        return
    rows = _read_csv(source)
    if not rows:
        return
    conn.executemany(
        """
        INSERT INTO shipping_rules(
          carrier, service_name, max_l, max_w, max_h, max_weight,
          price, packaging_cost, enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["carrier"],
                row["service_name"],
                _to_int(row.get("max_l")),
                _to_int(row.get("max_w")),
                _to_int(row.get("max_h")),
                _to_int(row.get("max_weight")),
                int(row["price"]),
                int(row.get("packaging_cost") or 0),
                int(row.get("enabled") or 1),
            )
            for row in rows
            if row.get("carrier") and row.get("service_name") and row.get("price")
        ],
    )
    conn.commit()


@dataclass(frozen=True)
class Item:
    id: int
    name: str | None
    jan: str | None
    model_number: str | None
    search_keyword: str
    category: str | None
    status: str
    notes: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Offer:
    id: int
    item_id: int
    source_id: int | None
    title: str | None
    price: int | None
    shipping: int | None
    total: int | None
    stock_status: str | None
    url: str | None
    confidence: str | None
    fetched_at: str
    raw_text: str | None


@dataclass(frozen=True)
class ShippingRule:
    id: int
    carrier: str
    service_name: str
    max_l: int | None
    max_w: int | None
    max_h: int | None
    max_weight: int | None
    price: int
    packaging_cost: int
    enabled: int


@dataclass(frozen=True)
class MarketRef:
    id: int
    item_id: int
    low: int | None
    mid: int | None
    high: int | None
    memo: str | None
    ref_date: str | None
    created_at: str


@dataclass(frozen=True)
class Calculation:
    id: int
    item_id: int
    offer_id: int | None
    sale_price: int
    fee_rate: float
    shipping_cost: int
    packaging_cost: int
    other_cost: int
    cost_price: int
    profit: int
    profit_rate: float
    breakeven_price: int
    target_profit: int
    min_price_for_target: int | None
    created_at: str


class Repository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_items(self) -> list[Item]:
        rows = self._conn.execute(
            "SELECT * FROM items ORDER BY updated_at DESC"
        ).fetchall()
        return [Item(**row) for row in rows]

    def get_item(self, item_id: int) -> Item | None:
        row = self._conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return Item(**row) if row else None

    def create_item(
        self,
        name: str | None,
        search_keyword: str,
        jan: str | None = None,
        model_number: str | None = None,
        category: str | None = None,
        status: str = "considering",
        notes: str | None = None,
    ) -> int:
        now = _now()
        cur = self._conn.execute(
            """
            INSERT INTO items(
              name, jan, model_number, search_keyword, category, status, notes,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                jan,
                model_number,
                search_keyword,
                category,
                status,
                notes,
                now,
                now,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update_item(
        self,
        item_id: int,
        name: str | None,
        search_keyword: str,
        jan: str | None = None,
        model_number: str | None = None,
        category: str | None = None,
        status: str = "considering",
        notes: str | None = None,
    ) -> None:
        now = _now()
        self._conn.execute(
            """
            UPDATE items
            SET name = ?, jan = ?, model_number = ?, search_keyword = ?, category = ?,
                status = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name,
                jan,
                model_number,
                search_keyword,
                category,
                status,
                notes,
                now,
                item_id,
            ),
        )
        self._conn.commit()

    def delete_item(self, item_id: int) -> None:
        self._conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self._conn.commit()

    def list_offers(self, item_id: int) -> list[Offer]:
        rows = self._conn.execute(
            "SELECT * FROM offers WHERE item_id = ? ORDER BY fetched_at DESC",
            (item_id,),
        ).fetchall()
        return [Offer(**row) for row in rows]

    def add_offers(self, offers: Iterable[dict]) -> None:
        if not offers:
            return
        self._conn.executemany(
            """
            INSERT INTO offers(
              item_id, source_id, title, price, shipping, total, stock_status,
              url, confidence, fetched_at, raw_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    o["item_id"],
                    o.get("source_id"),
                    o.get("title"),
                    o.get("price"),
                    o.get("shipping"),
                    o.get("total"),
                    o.get("stock_status"),
                    o.get("url"),
                    o.get("confidence"),
                    o.get("fetched_at"),
                    o.get("raw_text"),
                )
                for o in offers
            ],
        )
        self._conn.commit()

    def list_shipping_rules(self) -> list[ShippingRule]:
        rows = self._conn.execute(
            "SELECT * FROM shipping_rules WHERE enabled = 1 ORDER BY price ASC"
        ).fetchall()
        return [ShippingRule(**row) for row in rows]

    def list_shipping_rules_all(self) -> list[ShippingRule]:
        rows = self._conn.execute(
            "SELECT * FROM shipping_rules ORDER BY id ASC"
        ).fetchall()
        return [ShippingRule(**row) for row in rows]

    def replace_shipping_rules(self, rules: Iterable[dict]) -> None:
        self._conn.execute("DELETE FROM shipping_rules")
        self._conn.executemany(
            """
            INSERT INTO shipping_rules(
              carrier, service_name, max_l, max_w, max_h, max_weight,
              price, packaging_cost, enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["carrier"],
                    row["service_name"],
                    row.get("max_l"),
                    row.get("max_w"),
                    row.get("max_h"),
                    row.get("max_weight"),
                    row["price"],
                    row.get("packaging_cost", 0),
                    row.get("enabled", 1),
                )
                for row in rules
            ],
        )
        self._conn.commit()

    def list_market_refs(self, item_id: int) -> list[MarketRef]:
        rows = self._conn.execute(
            "SELECT * FROM market_refs WHERE item_id = ? ORDER BY created_at DESC",
            (item_id,),
        ).fetchall()
        return [MarketRef(**row) for row in rows]

    def add_market_ref(
        self,
        item_id: int,
        low: int | None,
        mid: int | None,
        high: int | None,
        memo: str | None,
        ref_date: str | None = None,
    ) -> int:
        now = _now()
        cur = self._conn.execute(
            """
            INSERT INTO market_refs(item_id, low, mid, high, memo, ref_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, low, mid, high, memo, ref_date, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def add_calculation(
        self,
        item_id: int,
        offer_id: int | None,
        sale_price: int,
        fee_rate: float,
        shipping_cost: int,
        packaging_cost: int,
        other_cost: int,
        cost_price: int,
        profit: int,
        profit_rate: float,
        breakeven_price: int,
        target_profit: int,
        min_price_for_target: int | None,
    ) -> int:
        now = _now()
        cur = self._conn.execute(
            """
            INSERT INTO calculations(
              item_id, offer_id, sale_price, fee_rate, shipping_cost, packaging_cost,
              other_cost, cost_price, profit, profit_rate, breakeven_price,
              target_profit, min_price_for_target, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                offer_id,
                sale_price,
                fee_rate,
                shipping_cost,
                packaging_cost,
                other_cost,
                cost_price,
                profit,
                profit_rate,
                breakeven_price,
                target_profit,
                min_price_for_target,
                now,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def list_calculations(self, item_id: int) -> list[Calculation]:
        rows = self._conn.execute(
            "SELECT * FROM calculations WHERE item_id = ? ORDER BY created_at DESC",
            (item_id,),
        ).fetchall()
        return [Calculation(**row) for row in rows]

    def list_sources(self) -> list[tuple[str, int]]:
        rows = self._conn.execute(
            "SELECT id, name FROM sources WHERE enabled = 1 ORDER BY name ASC"
        ).fetchall()
        return [(row["name"], row["id"]) for row in rows]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return int(value)
