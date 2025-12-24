# アーキテクチャ

## 目標
- UIとビジネスロジック、外部API、DBを分離して、拡張（仕入れ先追加）やテストを容易にする。
- 取得はUI非ブロッキング（Qtのスレッド/タスク）で行う。

## 推奨レイヤ
- Presentation（PySide6）
  - Widgets / Models / ViewModels 相当
  - 画面の入力→UseCase呼び出し→結果表示
- Application（UseCase）
  - 「候補更新」「最安ランキング」「配送推定」「利益計算」「CSV入出力」等のユースケース
- Domain（純粋ロジック）
  - Item / Offer / ShippingRule / ProfitCalc 等
  - 可能な限り副作用を持たない
- Infrastructure
  - Repositories（SQLite）
  - API Clients（Rakuten / Yahoo / Amazon PA-API / Tavily）
  - Secrets（keyring）
  - Logging

## 依存方向
Presentation → Application → Domain
Infrastructure → Application（DIして使用）
Domain は Infrastructure に依存しない

## 推奨フォルダ
```
app/
  __init__.py
  main.py              # エントリ
  ui/
    main_window.py
    models.py
    dialogs/
  usecases/
    refresh_offers.py
    calc_profit.py
    estimate_shipping.py
    csv_io.py
  domain/
    entities.py
    profit.py
    shipping.py
    normalize.py
  infra/
    db/
      schema.sql
      repo.py
    clients/
      rakuten.py
      yahoo.py
      amazon_paapi.py
      tavily.py
    secrets.py
    config.py
    logger.py
```

## スレッド方針（Qt）
- UIスレッドでHTTPを直接叩かない
- Worker(QObject) + QThread か QtConcurrent を使用
- 取得結果（Offer list）は signal でUIへ渡す
