from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.infra.db.repo import Repository, init_db
from app.usecases.refresh_offers import OfferInput, refresh_offers


class RefreshOffersWorker(QObject):
    finished = Signal(int)
    failed = Signal(str)

    def __init__(self, db_path: str, request: OfferInput) -> None:
        super().__init__()
        self._db_path = db_path
        self._request = request

    def run(self) -> None:
        try:
            conn = init_db(self._db_path)
            repo = Repository(conn)
            count = refresh_offers(repo, self._request)
            self.finished.emit(count)
        except Exception as exc:  # pragma: no cover - runtime errors
            self.failed.emit(str(exc))
