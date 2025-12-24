# コネクタ仕様（楽天 / Yahoo / Amazon PA-API / 価格.com最安(Tavily)）

## 共通：Offer正規化
アプリ内部の候補（Offer）は最低限この形に統一する。

- source: rakuten / yahoo / amazon / kakaku(tavily) / manual_url
- title: 取得できる範囲で
- price: int (JPY)
- shipping: int or NULL (JPY)
- total: price + shipping ただし shipping NULLなら NULL
- url: 商品ページ
- fetched_at: ISO8601
- stock_status: unknown / in_stock / out_of_stock（可能なら）
- confidence: high / medium / low
- raw_text: 抽出元テキスト（特にTavilyで必須）

## 楽天（Ichiba Item Search API）
### 入力
- keyword（必須）
- 任意で jan/model_number をkeywordに混ぜる（MVPは単純でOK）
### 出力（目安）
- title, price, url
- shipping は取れない場合がある → NULL 許容
### 失敗時
- HTTP/JSONエラーはログへ、UIは短文

## Yahoo!ショッピング（商品検索 v3）
### 入力
- query（keyword）
- jan_code（JANがある場合）
### 出力
- title, price, url
- shipping は取れない場合がある → NULL 許容

## Amazon（PA-API 5.0）
### 必要キー（設定画面）
- PartnerTag
- AccessKey / SecretKey
### 固定値（JP）
- host=webservices.amazon.co.jp
- region=us-west-2
- marketplace=www.amazon.co.jp
- service=ProductAdvertisingAPIv1
### 操作
- SearchItems（keyword検索）
- GetItems（ASIN指定）
### 出力
- title, price, url
- 配送/送料が必ず取れるとは限らない → shipping NULL 許容
### レート制限対策
- 同一商品を短時間に連打しない（クールダウン）
- 取得件数上限（例：上位10件）
- 失敗時はリトライ1回まで（429系は待つ/中止）

## 価格.com「最安」（MVP：Tavily）
### 方針
- 価格.comの公式APIが使えない可能性があるため、MVPは Tavily で「候補抽出」
- 抽出結果は誤る可能性があるため、必ず raw_text を表示して目視確認
### 手順
1) Tavily Search：価格.comの関連URL候補を取得（上位数件）
2) Tavily Extract：候補URLから本文抽出
3) 正規表現等で「最安」「¥」「円」等の近傍を解析し price候補を推定
4) confidence=low/medium を付与、Offerとして保存
### 追加（任意）
- ユーザーが「このURLを使う」と固定できるUI（誤URL回避）

## 参考（公式ドキュメントURL）
```text
Rakuten Ichiba Item Search API: https://webservice.rakuten.co.jp/documentation/ichiba-item-search
Yahoo!商品検索(v3): https://developer.yahoo.co.jp/webapi/shopping/v3/itemsearch.html
Amazon PA-API Japan locale: https://webservices.amazon.com/paapi5/documentation/locale-reference/japan.html
Tavily Extract: https://docs.tavily.com/documentation/api-reference/endpoint/extract
```
