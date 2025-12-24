# 設定 / シークレット（ローカル保存）

## 要件
- APIキーは設定画面で入力
- ローカル保存し、次回起動時に復元
- Windows/macOS両対応

## 推奨：keyring + config.json
- 秘密情報（APIキー/Secret）は **keyring** で保存（OS資格情報ストア）
- 非秘密情報（手数料率、目標利益、既定資材費、UI設定、DBパス等）は config.json に保存

### keyring に保存するキー（提案）
- rakuten_app_id
- yahoo_client_id
- amazon_partner_tag
- amazon_access_key
- amazon_secret_key
- tavily_api_key

### config.json に保存する例
- fee_rate（default 0.10）
- target_profit（円）
- default_packaging_cost（円）
- db_path（デフォルト: ./data/app.db など）
- kakaku_mode（default tavily）
- last_selected_item_id（任意）

## keyring が使えない場合のフォールバック（任意）
- 暗号化した secrets.json を保存（マスターパスワード方式）
- MVPでは未実装でも可（keyring前提）

## 設定画面（UI）仕様
- 各APIキーの入力欄（表示/非表示トグル）
- 「保存」ボタン（keyring/configへ反映）
- 「接続テスト」ボタン（各コネクタを軽く叩いてOK/NG表示）
