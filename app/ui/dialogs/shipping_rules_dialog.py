from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.infra.db import Repository


class ShippingRulesDialog(QDialog):
    def __init__(self, parent=None, *, repo: Repository) -> None:
        super().__init__(parent)
        self.setWindowTitle("送料テーブル編集")
        self._repo = repo

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels(
            [
                "有効",
                "配送会社",
                "サービス",
                "縦上限",
                "横上限",
                "高さ上限",
                "重量上限",
                "送料",
                "資材費",
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setStretchLastSection(True)

        add_btn = QPushButton("行を追加")
        remove_btn = QPushButton("行を削除")
        add_btn.clicked.connect(self._add_row)
        remove_btn.clicked.connect(self._remove_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        top_actions = QHBoxLayout()
        top_actions.addWidget(add_btn)
        top_actions.addWidget(remove_btn)
        top_actions.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(top_actions)
        layout.addWidget(self._table)
        layout.addWidget(buttons)

        self._load_rules()

    def _load_rules(self) -> None:
        self._table.setRowCount(0)
        for rule in self._repo.list_shipping_rules_all():
            self._append_rule(
                enabled=bool(rule.enabled),
                carrier=rule.carrier,
                service_name=rule.service_name,
                max_l=rule.max_l,
                max_w=rule.max_w,
                max_h=rule.max_h,
                max_weight=rule.max_weight,
                price=rule.price,
                packaging_cost=rule.packaging_cost,
            )

    def _append_rule(
        self,
        *,
        enabled: bool,
        carrier: str,
        service_name: str,
        max_l: int | None,
        max_w: int | None,
        max_h: int | None,
        max_weight: int | None,
        price: int,
        packaging_cost: int,
    ) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        enabled_item = QTableWidgetItem()
        enabled_item.setFlags(enabled_item.flags() | Qt.ItemIsUserCheckable)
        enabled_item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        self._table.setItem(row, 0, enabled_item)

        self._table.setItem(row, 1, QTableWidgetItem(carrier))
        self._table.setItem(row, 2, QTableWidgetItem(service_name))
        self._table.setItem(row, 3, QTableWidgetItem(_to_text(max_l)))
        self._table.setItem(row, 4, QTableWidgetItem(_to_text(max_w)))
        self._table.setItem(row, 5, QTableWidgetItem(_to_text(max_h)))
        self._table.setItem(row, 6, QTableWidgetItem(_to_text(max_weight)))
        self._table.setItem(row, 7, QTableWidgetItem(str(price)))
        self._table.setItem(row, 8, QTableWidgetItem(str(packaging_cost)))

    def _add_row(self) -> None:
        self._append_rule(
            enabled=True,
            carrier="",
            service_name="",
            max_l=None,
            max_w=None,
            max_h=None,
            max_weight=None,
            price=0,
            packaging_cost=0,
        )

    def _remove_row(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    def _save(self) -> None:
        rules = []
        for row in range(self._table.rowCount()):
            enabled = self._checked(row, 0)
            carrier = self._text(row, 1)
            service = self._text(row, 2)
            if not carrier or not service:
                QMessageBox.warning(
                    self,
                    "入力確認",
                    "配送会社とサービス名は必須です。",
                )
                return
            price = _to_int(self._text(row, 7))
            if price is None:
                QMessageBox.warning(
                    self, "入力確認", "送料は数値で入力してください。"
                )
                return
            rules.append(
                {
                    "enabled": 1 if enabled else 0,
                    "carrier": carrier,
                    "service_name": service,
                    "max_l": _to_int(self._text(row, 3)),
                    "max_w": _to_int(self._text(row, 4)),
                    "max_h": _to_int(self._text(row, 5)),
                    "max_weight": _to_int(self._text(row, 6)),
                    "price": price,
                    "packaging_cost": _to_int(self._text(row, 8)) or 0,
                }
            )
        self._repo.replace_shipping_rules(rules)
        self.accept()

    def _text(self, row: int, column: int) -> str:
        item = self._table.item(row, column)
        return item.text().strip() if item else ""

    def _checked(self, row: int, column: int) -> bool:
        item = self._table.item(row, column)
        if not item:
            return False
        return item.checkState() == Qt.Checked


def _to_text(value: int | None) -> str:
    return "" if value is None else str(value)


def _to_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    if not value.isdigit():
        return None
    return int(value)
