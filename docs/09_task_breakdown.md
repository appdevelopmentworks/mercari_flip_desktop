# Codex向け タスク分割（T1〜T9）

## T1: プロジェクト雛形 + メインUI（3ペイン）
- PySide6でMainWindowを作る
- 左：Items、中央：Offers、右：Shipping+Profit
- ログ初期化、ステータスバー、メニュー枠

## T2: SQLite層（スキーマ + Repository）
- schema.sql を読み込み、初回作成
- Items/Offers/ShippingRules/MarketRefs/Calculations のCRUD
- 取得履歴を溜める（offersは上書きしない方針）

## T3: 設定（keyring + config.json）
- 設定ダイアログ
- 保存/読み出し
- 接続テスト（各コネクタを軽く叩く）

## T4: 配送最安推定（shipping_rules）
- 入力（縦横高さ、重量）から適用可能ルールを抽出
- 最安を返す
- 右ペインに候補一覧表示

## T5: 利益計算（保存含む）
- 売価、手数料率、送料、資材、原価から
  粗利/利益率/分岐点/目標ラインを計算
- calculationsに保存

## T6: 楽天コネクタ
- keyword検索
- Offer正規化して保存/表示

## T7: Yahooコネクタ
- keyword検索（JANがあればJAN優先）
- Offer正規化して保存/表示

## T8: Amazon PA-APIコネクタ
- 署名（SigV4）実装
- SearchItems/GetItems
- Offer正規化して保存/表示

## T9: 価格.com最安（Tavily）
- Tavily Searchで候補URL
- Tavily Extractでraw_text抽出
- 価格推定（正規表現）→ Offer化（confidence付与）
