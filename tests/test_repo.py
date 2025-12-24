from app.infra.db import Repository, init_db


def test_repo_item_crud(tmp_path):
    db_path = tmp_path / "app.db"
    repo = Repository(init_db(db_path))

    item_id = repo.create_item(name="n1", search_keyword="kw1")
    item = repo.get_item(item_id)
    assert item is not None
    assert item.search_keyword == "kw1"

    repo.update_item(item_id=item_id, name="n2", search_keyword="kw2")
    item = repo.get_item(item_id)
    assert item is not None
    assert item.name == "n2"
    assert item.search_keyword == "kw2"

    repo.delete_item(item_id)
    assert repo.get_item(item_id) is None


def test_repo_shipping_rules_replace(tmp_path):
    db_path = tmp_path / "app.db"
    repo = Repository(init_db(db_path))
    repo.replace_shipping_rules(
        [
            {
                "carrier": "c1",
                "service_name": "s1",
                "max_l": 10,
                "max_w": 10,
                "max_h": 10,
                "max_weight": 100,
                "price": 500,
                "packaging_cost": 0,
                "enabled": 1,
            }
        ]
    )
    rules = repo.list_shipping_rules_all()
    assert len(rules) == 1
    assert rules[0].carrier == "c1"
