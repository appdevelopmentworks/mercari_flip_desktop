from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.infra.db.repo import Repository
from app.usecases.refresh_offers import OfferInput, refresh_offers


class RefreshOffersWorker(QObject):
    finished = Signal(int)
    failed = Signal(str)

    def __init__(self, repo: Repository, request: OfferInput) -> None:
        super().__init__()
        self._repo = repo
        self._request = request

    def run(self) -> None:
        try:
            count = refresh_offers(self._repo, self._request)
            self.finished.emit(count)
        except Exception as exc:  # pragma: no cover - runtime errors
            self.failed.emit(str(exc))
