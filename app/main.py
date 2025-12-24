import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .infra.config import load_config
from .infra.db import Repository, init_db
from .infra.logger import setup_logging
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parents[1] / "docs" / "Appico.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    config = load_config()
    setup_logging()
    conn = init_db(config.db_path)
    repo = Repository(conn)
    window = MainWindow(repo=repo, config=config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
