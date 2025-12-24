# メルカリ転売支援 デスクトップアプリ（PySide6 + SQLite）

自分専用のローカルアプリとして、仕入れ候補（楽天 / Yahoo / Amazon PA-API / 価格.com最安(暫定: Tavily)）を集約し、**最安（価格+送料）比較**と**配送最安推定**、**利益計算**、**相場の手入力保存**を行うツールです。

- 対応OS：Windows / macOS
- 配布：exe/app化はせず、ローカルで Python 実行（venv/uv/poetry）
- DB：SQLite（ローカル）
- 取得：手動更新のみ（スケジューラなし）
- 相場：手入力のみ（自動収集なし）

## ドキュメント構成
- docs/00_requirements.md … 要求定義（MVP）
- docs/01_setup.md … 開発環境セットアップ（venv/uv/poetry）
- docs/02_architecture.md … アーキテクチャ（層構造/依存方向）
- docs/03_database.md … SQLiteスキーマ/マイグレーション方針
- docs/04_ui_spec.md … 画面仕様（3ペイン）
- docs/05_connectors.md … 楽天/Yahoo/Amazon/Tavily(価格.com) コネクタ仕様
- docs/06_config_secrets.md … 設定/シークレット（keyring + config.json）
- docs/07_logging_errors.md … ログ/例外/リトライ/レート制限
- docs/08_test_plan.md … テスト計画（ユニット/手動）
- docs/09_task_breakdown.md … Codex向けタスク分割（T1〜）
- docs/10_codex_prompts.md … Codex貼り付け用プロンプト集
- docs/11_dev_workflow.md ... Development workflow (bootstrap to smoke test)
- docs/14_troubleshooting.md ... トラブルシューティング
- docs/13_dev_guidelines.md ... 開発ガイド（規約/運用）
- docs/12_todo.md ... 進捗管理用のTODOリスト

テンプレ
- templates/config.template.json … 非機密設定テンプレ
- templates/shipping_rules.seed.csv … 送料テーブル（手入力 seed）
- templates/items.import.template.csv … 商品CSVインポート雛形

## まず動かす（最短）
1. Python 3.11+ を推奨（3.10でも可）
2. venv で環境作成
3. 依存を入れる（PySide6 / requests or httpx / pydantic / keyring など）
4. `python -m app` で起動（このREADMEはドキュメントZIPのみ。実装はCodexで作成）

> 実装の開始点は docs/09_task_breakdown.md と docs/10_codex_prompts.md を推奨。

## 参考（公式ドキュメントURL）
※URLはコードブロック内に記載
```text
Rakuten Ichiba Item Search API: https://webservice.rakuten.co.jp/documentation/ichiba-item-search
Yahoo! Shopping item search(v3): https://developer.yahoo.co.jp/webapi/shopping/v3/itemsearch.html
Amazon PA-API locale(Japan): https://webservices.amazon.com/paapi5/documentation/locale-reference/japan.html
Tavily Extract: https://docs.tavily.com/documentation/api-reference/endpoint/extract
Tavily Crawl: https://docs.tavily.com/documentation/api-reference/endpoint/crawl
```
