from app.infra.db import Repository, init_db
from app.usecases.csv_io import export_items, import_items


def test_import_export_items_csv(tmp_path):
    db_path = tmp_path / "app.db"
    repo = Repository(init_db(db_path))

    csv_path = tmp_path / "items.csv"
    csv_path.write_text(
        "id,name,search_keyword,jan,model_number,category,status\n"
        "1,Item One,keyword1,,,,considering\n",
        encoding="utf-8",
    )
    imported = import_items(repo, csv_path)
    assert imported == 1

    out_path = tmp_path / "items_out.csv"
    export_items(repo, out_path)
    content = out_path.read_text(encoding="utf-8")
    assert "keyword1" in content
