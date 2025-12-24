import sys

from PySide6.QtWidgets import QApplication

from .infra.config import load_config
from .infra.db import Repository, init_db
from .infra.logger import setup_logging
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    config = load_config()
    setup_logging()
    conn = init_db(config.db_path)
    repo = Repository(conn)
    window = MainWindow(repo=repo, config=config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
