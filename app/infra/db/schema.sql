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
  name TEXT NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_offers_item_fetched_at
  ON offers(item_id, fetched_at);
CREATE INDEX IF NOT EXISTS idx_offers_item_total
  ON offers(item_id, total);
CREATE INDEX IF NOT EXISTS idx_calculations_item_created_at
  ON calculations(item_id, created_at);
