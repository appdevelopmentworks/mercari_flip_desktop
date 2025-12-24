from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class ItemDialog(QDialog):
    def __init__(self, parent=None, *, title: str, values: dict | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        self._name = QLineEdit()
        self._search = QLineEdit()
        self._search.setPlaceholderText("未入力なら商品名を使用します")
        self._jan = QLineEdit()
        self._model = QLineEdit()
        self._category = QLineEdit()
        self._status = QComboBox()
        self._status.addItem("検討中", "considering")
        self._status.addItem("運用中", "active")
        self._status.addItem("一時停止", "paused")
        self._notes = QTextEdit()

        if values:
            self._name.setText(values.get("name") or "")
            self._search.setText(values.get("search_keyword") or "")
            self._jan.setText(values.get("jan") or "")
            self._model.setText(values.get("model_number") or "")
            self._category.setText(values.get("category") or "")
            status = values.get("status") or "considering"
            index = self._status.findData(status)
            if index >= 0:
                self._status.setCurrentIndex(index)
            self._notes.setText(values.get("notes") or "")

        form = QFormLayout()
        form.addRow("商品名", self._name)
        form.addRow("検索キーワード", self._search)
        form.addRow("JAN", self._jan)
        form.addRow("型番", self._model)
        form.addRow("カテゴリ", self._category)
        form.addRow("状態", self._status)
        form.addRow("メモ", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict:
        name = self._name.text().strip()
        search = self._search.text().strip()
        if not search:
            search = name
        return {
            "name": name or None,
            "search_keyword": search,
            "jan": self._jan.text().strip() or None,
            "model_number": self._model.text().strip() or None,
            "category": self._category.text().strip() or None,
            "status": self._status.currentData(),
            "notes": self._notes.toPlainText().strip() or None,
        }
