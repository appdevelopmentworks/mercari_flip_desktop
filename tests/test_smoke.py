from app.infra.config import AppConfig, load_config, save_config


def test_config_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    config = AppConfig(fee_rate=0.2, target_profit=1234)
    save_config(config, path)
    loaded = load_config(path)
    assert loaded.fee_rate == 0.2
    assert loaded.target_profit == 1234
