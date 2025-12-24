# データベース（SQLite）

## 方針
- 単一ユーザー、ローカル完結
- まずは生SQL + sqlite3 で開始（将来SQLAlchemyへ移行可）
- マイグレーションは最初は「schema_version」テーブルで簡易管理

## 推奨テーブル
- items：追跡する商品
- sources：仕入れ先（rakuten/yahoo/amazon/kakaku/tavily 等）
- offers：仕入れ候補（取得のたびに履歴として貯める）
- shipping_rules：送料テーブル（手入力）
- market_refs：相場（手入力）
- calculations：利益計算結果（履歴）

## スキーマ（例）
```sql
CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  jan TEXT,
  model_number TEXT,
  search_keyword TEXT NOT NULL,
  category TEXT,
  status TEXT DEFAULT 'considering',
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,     -- rakuten / yahoo / amazon / kakaku / tavily / manual_url
  domain TEXT,
  enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  source_id INTEGER,
  title TEXT,
  price INTEGER,
  shipping INTEGER,
  total INTEGER,
  stock_status TEXT,
  url TEXT,
  confidence TEXT,
  fetched_at TEXT NOT NULL,
  raw_text TEXT,
  FOREIGN KEY(item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS shipping_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  carrier TEXT NOT NULL,
  service_name TEXT NOT NULL,
  max_l INTEGER, max_w INTEGER, max_h INTEGER,
  max_weight INTEGER,
  price INTEGER NOT NULL,
  packaging_cost INTEGER DEFAULT 0,
  enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS market_refs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  low INTEGER,
  mid INTEGER,
  high INTEGER,
  memo TEXT,
  ref_date TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS calculations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  offer_id INTEGER,
  sale_price INTEGER NOT NULL,
  fee_rate REAL NOT NULL,
  shipping_cost INTEGER NOT NULL,
  packaging_cost INTEGER NOT NULL,
  other_cost INTEGER DEFAULT 0,
  cost_price INTEGER NOT NULL,
  profit INTEGER NOT NULL,
  profit_rate REAL NOT NULL,
  breakeven_price INTEGER NOT NULL,
  target_profit INTEGER DEFAULT 0,
  min_price_for_target INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES items(id)
);
```

## インデックス（推奨）
- offers(item_id, fetched_at)
- offers(item_id, total)
- calculations(item_id, created_at)
