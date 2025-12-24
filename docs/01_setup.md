# セットアップ（Python実行運用）

## 推奨
- Python 3.11+（3.10でも可）
- OS：Windows / macOS
- Git（推奨）

## 依存（目安）
- GUI：PySide6
- HTTP：httpx（推奨） or requests
- 型/バリデーション：pydantic
- 秘密情報：keyring（OS資格情報ストア）
- DB：sqlite3（標準）
- ログ：logging（標準）
- （任意）SQLAlchemy（将来）

## venv で作る（例）
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install -U pip
pip install PySide6 httpx pydantic keyring
```

## uv で作る（例）
```bash
# uv install (各自)
uv venv
source .venv/bin/activate
uv pip install PySide6 httpx pydantic keyring
```

## poetry で作る（例）
```bash
poetry init
poetry add PySide6 httpx pydantic keyring
poetry run python -m app
```

## 実行（想定）
```bash
python -m app
```

## 注意（macOS）
- 初回起動で「キーチェーンアクセス」の許可が求められる可能性あり（keyring利用時）
