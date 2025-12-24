from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config.json")


@dataclass
class AppConfig:
    fee_rate: float = 0.1
    target_profit: int = 2000
    default_packaging_cost: int = 50
    db_path: str = "./data/app.db"
    kakaku_mode: str = "tavily"
    amazon_locale: str = "JP"


def load_config(path: Path | str | None = None) -> AppConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        config = AppConfig()
        save_config(config, config_path)
        return config

    data = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = asdict(AppConfig())
    for key in list(data.keys()):
        if key not in defaults:
            data.pop(key)
    merged = {**defaults, **data}
    return AppConfig(**merged)


def save_config(config: AppConfig, path: Path | str | None = None) -> None:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = asdict(config)
    config_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
