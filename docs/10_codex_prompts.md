# Codex貼り付け用プロンプト集

> 使い方：各セクションをそのままCodexへ貼り付けて実装を進める。
> ここでは「実装の規約」「ファイル構成」「受け入れ条件」を強めに固定して、ブレを減らす。

---

## 共通ルール（全タスク）
- Python 3.11想定（3.10互換なら尚良）
- 型ヒント必須
- ログは `app/infra/logger.py` に集約
- HTTPは `httpx` を推奨（asyncは使わず同期 + QThreadで非同期化）
- DBは `sqlite3`（将来拡張のため Repository パターン）
- UIスレッドでネットワークしない（必ずWorker/QThread）
- エラーはクラッシュさせずUIに短文表示、詳細はログ
- 依存の注入（Clients/Repo）はMainで組み立てて渡す

---

## T1 プロンプト：雛形 + 3ペインUI
あなたはPython/PySide6のシニア開発者です。
以下の仕様で `app/` プロジェクト雛形を作ってください。

### 要件
- エントリ `python -m app` で起動
- `MainWindow` は3ペイン（左=Items、中央=Offers、右=Shipping+Profit）
- メニュー：Settings / CSV Export / CSV Import / Open Logs
- ステータスバー：通信中表示、エラー短文表示
- ログ：./logs/app.log に出力（ローテーションは後回しでOK）

### ファイル構成（必須）
- app/__init__.py
- app/__main__.py
- app/main.py
- app/ui/main_window.py
- app/infra/logger.py

### 受け入れ
- 例外なく起動し、メニューと3ペインが表示される
- ログファイルが生成される

---

## T2 プロンプト：SQLiteスキーマ + Repository
以下を実装してください。

### スキーマ
docs/03_database.md のSQLを `app/infra/db/schema.sql` に置く。
起動時にDBが無ければ作成。`schema_version` も作る。

### Repository
- app/infra/db/repo.py に `SqliteRepo` を実装
- items/offers/shipping_rules/market_refs/calculations のCRUD
- offers は履歴として insert-only（削除はMVPでは不要）

### 受け入れ
- items CRUD が動く（簡易CLIテストでも可）
- DBファイルが作成される

---

## T3 プロンプト：設定（keyring + config.json）
### 要件
- 設定画面（QDialog）で以下を入力し保存：
  rakuten_app_id, yahoo_client_id, amazon_partner_tag, amazon_access_key, amazon_secret_key, tavily_api_key
- 秘密情報は keyring に保存
- 非秘密情報は `config.json` に保存（fee_rate, target_profit, default_packaging_cost, db_path）
- 起動時に復元し、UIに反映

### ファイル
- app/infra/config.py
- app/infra/secrets.py
- app/ui/dialogs/settings_dialog.py

### 受け入れ
- 保存→再起動で復元される
- macOSでも動く（keychain許可はユーザー操作でOK）

---

## T4 プロンプト：配送最安推定
### 要件
- shipping_rules テーブルを読み込み、入力(縦横高さcm,重量g)に適合する候補を返す
- enabled=1のみ対象
- 最安候補を1つ返し、候補一覧も返す
- 右ペインに表示（簡易でOK）

### 受け入れ
- templates/shipping_rules.seed.csv を読み込んで初期投入できる（任意）
- 入力変更で最安が変わる

---

## T5 プロンプト：利益計算
### 要件
- sale_price, fee_rate, shipping_cost, packaging_cost, other_cost, cost_price から
  profit, profit_rate, breakeven_price を計算
- target_profit があれば min_price_for_target を計算
- calculations テーブルに保存

### 受け入れ
- 右ペインで計算が表示され、保存できる

---

## T6 プロンプト：楽天コネクタ
### 要件
- httpx でRakuten Ichiba Item Search APIを呼び出し、上位10件をOffer化
- price/title/url を保存
- shipping は取れなければNULL
- 取得はWorker(QThread)で実行し、完了後UIを更新

### ファイル
- app/infra/clients/rakuten.py
- app/usecases/refresh_offers.py

---

## T7 プロンプト：Yahooコネクタ
同様にYahooショッピング商品検索(v3)で上位10件をOffer化。

---

## T8 プロンプト：Amazon PA-API
### 要件
- SigV4署名で `SearchItems` を実行
- locale=JP固定（host/region/marketplaceはdocs参照）
- 上位10件をOffer化（price/title/url）
- 失敗時は設定ミスの可能性を示すエラーメッセージ

---

## T9 プロンプト：価格.com最安（Tavily）
### 要件
- Tavily Searchで価格.comの候補URLを取得
- Tavily Extractでraw_text取得
- 正規表現で価格っぽい数値を推定
- confidence=low/medium を付与してOffer化
- raw_text はoffers.raw_textに保存し、UIで表示できるようにする
