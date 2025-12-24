from PySide6.QtCore import QThread, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QWidget,
)

from app.infra.config import AppConfig
from app.infra.db import Repository
from app.usecases.calc_profit import calc_profit
from app.usecases.csv_io import (
    export_calculations,
    export_items,
    export_market_refs,
    export_offers,
    import_items,
)
from app.usecases.estimate_shipping import ShippingInput, estimate_shipping
from app.usecases.refresh_offers import OfferInput
from app.ui.dialogs import ItemDialog, SettingsDialog, ShippingRulesDialog
from app.ui.workers import RefreshOffersWorker


class MainWindow(QMainWindow):
    def __init__(self, *, repo: Repository, config: AppConfig) -> None:
        super().__init__()
        self._repo = repo
        self._config = config
        self._refresh_thread: QThread | None = None
        self._refresh_worker: RefreshOffersWorker | None = None
        self._selected_offer_id: int | None = None
        self._selected_shipping_cost: int = 0

        self.setWindowTitle("メルカリ仕入れ支援")
        self._apply_icon()
        self.setMinimumSize(1200, 720)
        self.resize(1820, 1170)
        self._build_menu()
        self._build_layout()
        self.statusBar().showMessage("準備完了")
        self._apply_style()
        self._load_items()
        self._update_shipping()
        self._update_profit()
        self._update_controls_enabled()
        self._show_help_on_start()

    def _build_menu(self) -> None:
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self._open_settings)

        csv_import_items = QAction("商品CSVをインポート", self)
        csv_import_items.triggered.connect(self._import_items_csv)

        csv_export_items = QAction("商品CSVをエクスポート", self)
        csv_export_items.triggered.connect(self._export_items_csv)

        csv_export_offers = QAction("候補CSVをエクスポート", self)
        csv_export_offers.triggered.connect(self._export_offers_csv)

        csv_export_market = QAction("相場CSVをエクスポート", self)
        csv_export_market.triggered.connect(self._export_market_csv)

        csv_export_calc = QAction("計算CSVをエクスポート", self)
        csv_export_calc.triggered.connect(self._export_calculations_csv)

        logs_action = QAction("ログフォルダを開く", self)
        logs_action.triggered.connect(self._open_logs_folder)

        menu = self.menuBar()
        settings_menu = menu.addMenu("設定")
        settings_menu.addAction(settings_action)
        settings_menu.addSeparator()
        shipping_action = QAction("送料テーブル編集", self)
        shipping_action.triggered.connect(self._open_shipping_rules)
        settings_menu.addAction(shipping_action)

        csv_menu = menu.addMenu("CSV入出力")
        csv_menu.addAction(csv_import_items)
        csv_menu.addAction(csv_export_items)
        csv_menu.addSeparator()
        csv_menu.addAction(csv_export_offers)
        csv_menu.addAction(csv_export_market)
        csv_menu.addAction(csv_export_calc)

        tools_menu = menu.addMenu("ツール")
        tools_menu.addAction(logs_action)

    def _build_layout(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_left_pane())
        splitter.addWidget(self._build_center_pane())
        splitter.addWidget(self._build_right_pane())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 3)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([280, 720, 400])

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

    def _build_left_pane(self) -> QWidget:
        pane = self._panel("商品")
        layout = pane.layout()

        self._search = QLineEdit()
        self._search.setPlaceholderText("商品検索")
        self._search.setToolTip("商品名または検索キーワードで絞り込みます。")
        self._search.textChanged.connect(self._load_items)
        layout.addWidget(self._search)

        filter_row = QHBoxLayout()
        self._status_filter = QComboBox()
        self._status_filter.addItem("すべて", "all")
        self._status_filter.addItem("検討中", "considering")
        self._status_filter.addItem("運用中", "active")
        self._status_filter.addItem("一時停止", "paused")
        self._status_filter.currentIndexChanged.connect(self._load_items)
        filter_row.addWidget(QLabel("状態"))
        filter_row.addWidget(self._status_filter)
        layout.addLayout(filter_row)

        self._item_list = QListWidget()
        self._item_list.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self._item_list)

        actions = QHBoxLayout()
        self._add_btn = QPushButton("追加")
        self._edit_btn = QPushButton("編集")
        self._delete_btn = QPushButton("削除")
        self._add_btn.setToolTip("商品を追加します。")
        self._edit_btn.setToolTip("選択中の商品を編集します。")
        self._delete_btn.setToolTip("選択中の商品を削除します。")
        self._add_btn.clicked.connect(self._add_item)
        self._edit_btn.clicked.connect(self._edit_item)
        self._delete_btn.clicked.connect(self._delete_item)
        actions.addWidget(self._add_btn)
        actions.addWidget(self._edit_btn)
        actions.addWidget(self._delete_btn)
        layout.addLayout(actions)

        return pane

    def _build_center_pane(self) -> QWidget:
        pane = self._panel("仕入れ候補")
        layout = pane.layout()

        controls = QHBoxLayout()
        self._refresh_btn = QPushButton("候補更新")
        self._refresh_btn.setToolTip("選択中の商品で候補取得を実行します。")
        self._refresh_btn.clicked.connect(self._refresh_offers)
        controls.addWidget(self._refresh_btn)
        controls.addStretch()
        controls.addWidget(QLabel("並び替え"))
        self._sort_box = QComboBox()
        self._sort_box.addItems(["合計 (昇順)", "価格 (昇順)", "送料 (昇順)"])
        self._sort_box.currentIndexChanged.connect(self._load_offers)
        controls.addWidget(self._sort_box)
        layout.addLayout(controls)

        self._best_label = QLabel("最安: -")
        self._best_label.setProperty("emphasis", "true")
        layout.addWidget(self._best_label)

        self._offers_table = QTableWidget(0, 6)
        self._offers_table.setHorizontalHeaderLabels(
            ["仕入れ先", "商品名", "価格", "送料", "合計", "在庫"]
        )
        self._offers_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._offers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._offers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._offers_table.horizontalHeader().setStretchLastSection(True)
        self._offers_table.setAlternatingRowColors(True)
        self._offers_table.itemSelectionChanged.connect(self._on_offer_selected)
        layout.addWidget(self._offers_table)

        return pane

    def _build_right_pane(self) -> QWidget:
        pane = self._panel("配送・利益")
        layout = pane.layout()

        shipping_box = QGroupBox("配送入力")
        shipping_box.setObjectName("card")
        shipping_layout = QFormLayout(shipping_box)
        self._length = self._int_spin(suffix=" cm")
        self._width = self._int_spin(suffix=" cm")
        self._height = self._int_spin(suffix=" cm")
        self._weight = self._int_spin(suffix=" g")
        self._packaging = self._int_spin(suffix=" 円")
        self._length.setMaximum(200)
        self._width.setMaximum(200)
        self._height.setMaximum(200)
        self._weight.setMaximum(30000)
        self._packaging.setMaximum(10000)
        self._length.setToolTip("上限: 200 cm")
        self._width.setToolTip("上限: 200 cm")
        self._height.setToolTip("上限: 200 cm")
        self._weight.setToolTip("上限: 30000 g")
        self._packaging.setToolTip("上限: 10000 円")
        self._packaging.setValue(self._config.default_packaging_cost)
        shipping_layout.addRow("縦 (cm)", self._length)
        shipping_layout.addRow("横 (cm)", self._width)
        shipping_layout.addRow("高さ (cm)", self._height)
        shipping_layout.addRow("重量 (g)", self._weight)
        shipping_layout.addRow("資材費 (円)", self._packaging)
        layout.addWidget(shipping_box)

        self._shipping_table = QTableWidget(0, 3)
        self._shipping_table.setHorizontalHeaderLabels(
            ["配送会社", "サービス", "料金"]
        )
        self._shipping_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._shipping_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._shipping_table.horizontalHeader().setStretchLastSection(True)
        self._shipping_table.setAlternatingRowColors(True)
        self._shipping_table.itemSelectionChanged.connect(self._on_shipping_selected)
        layout.addWidget(self._shipping_table)

        market_box = QGroupBox("相場")
        market_box.setObjectName("card")
        market_layout = QFormLayout(market_box)
        self._market_low = self._int_spin(suffix=" 円")
        self._market_mid = self._int_spin(suffix=" 円")
        self._market_high = self._int_spin(suffix=" 円")
        for field in [self._market_low, self._market_mid, self._market_high]:
            field.setMaximum(10000000)
            field.setToolTip("上限: 10,000,000 円")
        self._market_memo = QTextEdit()
        self._market_memo.setPlaceholderText("相場の根拠や補足を記録")
        market_layout.addRow("安値", self._market_low)
        market_layout.addRow("中央値", self._market_mid)
        market_layout.addRow("高値", self._market_high)
        market_layout.addRow("メモ", self._market_memo)
        layout.addWidget(market_box)

        profit_box = QGroupBox("利益")
        profit_box.setObjectName("card")
        profit_layout = QFormLayout(profit_box)
        self._sale_price = self._int_spin(suffix=" 円")
        self._cost_price = self._int_spin(suffix=" 円")
        self._fee_rate = self._int_spin(suffix=" %")
        self._fee_rate.setRange(0, 100)
        self._fee_rate.setValue(int(self._config.fee_rate * 100))
        self._sale_price.setMaximum(10000000)
        self._cost_price.setMaximum(10000000)
        self._sale_price.setToolTip("上限: 10,000,000 円")
        self._cost_price.setToolTip("上限: 10,000,000 円")
        self._profit_label = QLabel("-")
        self._profit_rate_label = QLabel("-")
        self._breakeven_label = QLabel("-")
        self._target_label = QLabel("-")
        profit_layout.addRow("想定売価", self._sale_price)
        profit_layout.addRow("原価", self._cost_price)
        profit_layout.addRow("手数料率 (%)", self._fee_rate)
        profit_layout.addRow("利益", self._profit_label)
        profit_layout.addRow("利益率", self._profit_rate_label)
        profit_layout.addRow("損益分岐", self._breakeven_label)
        profit_layout.addRow("目標ライン", self._target_label)
        layout.addWidget(profit_box)

        self._save_calc_btn = QPushButton("計算結果を保存")
        self._save_calc_btn.setToolTip("現在の計算結果と相場を保存します。")
        self._save_calc_btn.clicked.connect(self._save_calculation)
        layout.addWidget(self._save_calc_btn)
        layout.addStretch()

        for spin in [
            self._length,
            self._width,
            self._height,
            self._weight,
            self._packaging,
        ]:
            spin.valueChanged.connect(self._update_shipping)

        for spin in [self._sale_price, self._cost_price, self._fee_rate]:
            spin.valueChanged.connect(self._update_profit)

        for spin in [
            self._length,
            self._width,
            self._height,
            self._weight,
            self._packaging,
            self._market_low,
            self._market_mid,
            self._market_high,
            self._sale_price,
            self._cost_price,
            self._fee_rate,
        ]:
            self._auto_reset_spinbox(spin)

        return pane

    def _panel(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(10)
        header = QLabel(title)
        header.setObjectName("panelTitle")
        frame_layout.addWidget(header)
        return frame

    def _int_spin(self, *, suffix: str = "") -> QSpinBox:
        box = QSpinBox()
        box.setRange(0, 1_000_000)
        if suffix:
            box.setSuffix(suffix)
        return box

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f3f5f9;
                font-family: "Yu Gothic UI", "Meiryo", "Segoe UI", sans-serif;
            }
            QFrame#panel {
                background: #ffffff;
                border: 1px solid #e2e6ef;
                border-radius: 10px;
            }
            QGroupBox#card {
                background: #fbfdff;
                border: 1px solid #e5e9f5;
                border-radius: 10px;
                margin-top: 6px;
            }
            QGroupBox#card::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #1f2937;
                font-weight: 600;
            }
            QLabel#panelTitle {
                font-size: 14px;
                font-weight: 700;
                color: #111827;
            }
            QLabel[emphasis="true"] {
                font-weight: 600;
                color: #1f2937;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QTableWidget {
                background: #fafbff;
                border: 1px solid #e2e6ef;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit[warning="true"], QSpinBox[warning="true"] {
                border: 1px solid #ef4444;
                background: #fff5f5;
            }
            QHeaderView::section {
                background: #eef2ff;
                color: #1f2937;
                padding: 6px;
                border: none;
                font-weight: 600;
            }
            QPushButton {
                background: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            """
        )

    def _apply_icon(self) -> None:
        icon_path = QIcon("docs/Appico.png")
        if not icon_path.isNull():
            self.setWindowIcon(icon_path)

    def _load_items(self) -> None:
        self._item_list.clear()
        query = self._search.text().strip().lower()
        status = self._status_filter.currentData() or "all"
        for item in self._repo.list_items():
            if status != "all" and item.status != status:
                continue
            label = item.name or item.search_keyword
            if query and query not in label.lower():
                continue
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, item.id)
            self._item_list.addItem(list_item)
        if self._item_list.count() > 0 and not self._item_list.currentItem():
            self._item_list.setCurrentRow(0)
        if self._item_list.count() == 0:
            self.statusBar().showMessage("商品がありません。左下の「追加」から登録してください。")
        self._update_controls_enabled()

    def _current_item_id(self) -> int | None:
        current = self._item_list.currentItem()
        if not current:
            return None
        return int(current.data(Qt.UserRole))

    def _update_controls_enabled(self) -> None:
        has_item = self._current_item_id() is not None
        self._refresh_btn.setEnabled(has_item)
        self._edit_btn.setEnabled(has_item)
        self._delete_btn.setEnabled(has_item)
        self._save_calc_btn.setEnabled(has_item)
        self._offers_table.setEnabled(has_item)

    def _add_item(self) -> None:
        dialog = ItemDialog(self, title="商品追加")
        if dialog.exec() != ItemDialog.Accepted:
            return
        values = dialog.values()
        if not values["search_keyword"]:
            QMessageBox.warning(self, "入力確認", "検索キーワードか商品名を入力してください。")
            return
        self._repo.create_item(**values)
        self._load_items()

    def _edit_item(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            return
        item = self._repo.get_item(item_id)
        if not item:
            return
        dialog = ItemDialog(
            self,
            title="商品編集",
            values={
                "name": item.name,
                "search_keyword": item.search_keyword,
                "jan": item.jan,
                "model_number": item.model_number,
                "category": item.category,
                "status": item.status,
                "notes": item.notes,
            },
        )
        if dialog.exec() != ItemDialog.Accepted:
            return
        values = dialog.values()
        if not values["search_keyword"]:
            QMessageBox.warning(self, "入力確認", "検索キーワードか商品名を入力してください。")
            return
        self._repo.update_item(item_id=item_id, **values)
        self._load_items()

    def _delete_item(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            return
        confirm = QMessageBox.question(
            self,
            "削除確認",
            "選択中の商品を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        self._repo.delete_item(item_id)
        self._load_items()
        self._offers_table.setRowCount(0)
        self._best_label.setText("最安: -")

    def _on_item_selected(self) -> None:
        self._selected_offer_id = None
        self._load_offers()
        self._load_market()
        self._update_controls_enabled()

    def _load_offers(self) -> None:
        item_id = self._current_item_id()
        self._offers_table.setRowCount(0)
        if item_id is None:
            return
        source_map = {source_id: name for name, source_id in self._repo.list_sources()}
        offers = self._repo.list_offers(item_id)
        if self._sort_box.currentText() == "価格 (昇順)":
            offers.sort(key=lambda x: x.price or 0)
        elif self._sort_box.currentText() == "送料 (昇順)":
            offers.sort(key=lambda x: x.shipping or 0)
        else:
            offers.sort(key=lambda x: x.total or 0)

        best_total = None
        for offer in offers:
            row = self._offers_table.rowCount()
            self._offers_table.insertRow(row)
            source_name = source_map.get(offer.source_id, str(offer.source_id))
            self._offers_table.setItem(row, 0, QTableWidgetItem(str(source_name)))
            self._offers_table.setItem(row, 1, QTableWidgetItem(offer.title or ""))
            self._offers_table.setItem(
                row, 2, QTableWidgetItem(str(offer.price or "-"))
            )
            self._offers_table.setItem(
                row, 3, QTableWidgetItem(str(offer.shipping or "-"))
            )
            self._offers_table.setItem(
                row, 4, QTableWidgetItem(str(offer.total or "-"))
            )
            self._offers_table.setItem(
                row, 5, QTableWidgetItem(offer.stock_status or "-")
            )
            self._offers_table.setVerticalHeaderItem(
                row, QTableWidgetItem(str(offer.id))
            )
            if offer.total is not None:
                best_total = (
                    offer.total
                    if best_total is None
                    else min(best_total, offer.total)
                )
        self._best_label.setText(
            f"最安: {best_total}" if best_total is not None else "最安: -"
        )
        if not offers:
            self.statusBar().showMessage("候補がありません。候補更新を実行してください。")
            self._cost_price.setValue(0)
            self._selected_offer_id = None
            self._update_profit()

    def _load_market(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            return
        refs = self._repo.list_market_refs(item_id)
        if not refs:
            self._market_low.setValue(0)
            self._market_mid.setValue(0)
            self._market_high.setValue(0)
            self._market_memo.setText("")
            return
        latest = refs[0]
        self._market_low.setValue(latest.low or 0)
        self._market_mid.setValue(latest.mid or 0)
        self._market_high.setValue(latest.high or 0)
        self._market_memo.setText(latest.memo or "")

    def _refresh_offers(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QMessageBox.information(self, "商品選択", "商品を選択してください。")
            return
        if self._refresh_thread and self._refresh_thread.isRunning():
            return
        item = self._repo.get_item(item_id)
        if not item:
            return
        request = OfferInput(item_id=item.id, search_keyword=item.search_keyword)

        self._refresh_worker = RefreshOffersWorker(
            self._config.db_path, request
        )
        self._refresh_thread = QThread(self)
        self._refresh_worker.moveToThread(self._refresh_thread)
        self._refresh_thread.started.connect(self._refresh_worker.run)
        self._refresh_worker.finished.connect(self._refresh_done)
        self._refresh_worker.failed.connect(self._refresh_failed)
        self._refresh_worker.finished.connect(self._refresh_thread.quit)
        self._refresh_worker.failed.connect(self._refresh_thread.quit)
        self._refresh_thread.finished.connect(self._refresh_worker.deleteLater)
        self._refresh_thread.finished.connect(self._refresh_thread.deleteLater)

        self._refresh_btn.setEnabled(False)
        self.statusBar().showMessage("候補取得中...")
        self._refresh_thread.start()

    def _refresh_done(self, count: int) -> None:
        self._refresh_btn.setEnabled(True)
        self.statusBar().showMessage(f"候補取得完了: {count} 件")
        self._load_offers()
        self._refresh_worker = None
        self._refresh_thread = None

    def _refresh_failed(self, message: str) -> None:
        self._refresh_btn.setEnabled(True)
        QMessageBox.warning(self, "取得失敗", message)
        self.statusBar().showMessage("取得失敗")
        self._refresh_worker = None
        self._refresh_thread = None

    def _on_offer_selected(self) -> None:
        selected = self._offers_table.currentRow()
        if selected < 0:
            return
        header = self._offers_table.verticalHeaderItem(selected)
        if header:
            self._selected_offer_id = int(header.text())
        price_item = self._offers_table.item(selected, 2)
        shipping_item = self._offers_table.item(selected, 3)
        price = int(price_item.text()) if price_item and price_item.text().isdigit() else 0
        shipping = (
            int(shipping_item.text())
            if shipping_item and shipping_item.text().isdigit()
            else 0
        )
        self._cost_price.setValue(price + shipping)
        self._update_profit()

    def _update_shipping(self) -> None:
        data = ShippingInput(
            length=self._length.value(),
            width=self._width.value(),
            height=self._height.value(),
            weight=self._weight.value(),
            packaging_cost=self._packaging.value(),
        )
        self._clear_shipping_warnings()
        missing_fields = []
        dims = [self._length.value(), self._width.value(), self._height.value()]
        has_any_dim = any(value > 0 for value in dims)
        if has_any_dim and 0 in dims:
            if self._length.value() == 0:
                missing_fields.append(self._length)
            if self._width.value() == 0:
                missing_fields.append(self._width)
            if self._height.value() == 0:
                missing_fields.append(self._height)
        if has_any_dim and self._weight.value() == 0:
            missing_fields.append(self._weight)
        if self._weight.value() > 0 and not has_any_dim:
            missing_fields.extend([self._length, self._width, self._height])

        if missing_fields:
            for field in missing_fields:
                self._mark_warning(field)
            self.statusBar().showMessage(
                "配送条件が未入力です。寸法と重量を入力してください。"
            )

        if (
            self._length.value() == 0
            and self._width.value() == 0
            and self._height.value() == 0
            and self._weight.value() == 0
        ):
            self.statusBar().showMessage(
                "配送条件が未入力です。寸法や重量を入力してください。"
            )
        rules = self._repo.list_shipping_rules()
        estimates = estimate_shipping(rules, data)
        self._shipping_table.setRowCount(0)
        self._selected_shipping_cost = 0
        if not estimates:
            self._shipping_table.insertRow(0)
            self._shipping_table.setItem(0, 0, QTableWidgetItem("送料ルール未設定"))
            self._shipping_table.setItem(0, 1, QTableWidgetItem("-"))
            self._shipping_table.setItem(0, 2, QTableWidgetItem("-"))
            self._update_profit()
            return
        for estimate in estimates:
            row = self._shipping_table.rowCount()
            self._shipping_table.insertRow(row)
            self._shipping_table.setItem(
                row, 0, QTableWidgetItem(estimate.rule.carrier)
            )
            self._shipping_table.setItem(
                row, 1, QTableWidgetItem(estimate.rule.service_name)
            )
            self._shipping_table.setItem(
                row, 2, QTableWidgetItem(str(estimate.total_cost))
            )
        if estimates:
            self._selected_shipping_cost = estimates[0].total_cost
            self._update_profit()

    def _on_shipping_selected(self) -> None:
        row = self._shipping_table.currentRow()
        if row < 0:
            return
        price_item = self._shipping_table.item(row, 2)
        if price_item and price_item.text().isdigit():
            self._selected_shipping_cost = int(price_item.text())
            self._update_profit()

    def _update_profit(self) -> None:
        self._clear_warnings([self._sale_price, self._cost_price, self._fee_rate])
        if self._sale_price.value() <= 0:
            self._mark_warning(self._sale_price)
        if self._cost_price.value() <= 0:
            self._mark_warning(self._cost_price)
        if self._fee_rate.value() <= 0:
            self._mark_warning(self._fee_rate)
        shipping_cost = max(0, self._selected_shipping_cost - self._packaging.value())
        result = calc_profit(
            sale_price=self._sale_price.value(),
            cost_price=self._cost_price.value(),
            fee_rate=self._fee_rate.value() / 100,
            shipping_cost=shipping_cost,
            packaging_cost=self._packaging.value(),
            other_cost=0,
            target_profit=self._config.target_profit,
        )
        self._profit_label.setText(str(result.profit))
        self._profit_rate_label.setText(f"{result.profit_rate:.2%}")
        self._breakeven_label.setText(str(result.breakeven_price))
        self._target_label.setText(
            str(result.min_price_for_target)
            if result.min_price_for_target
            else "-"
        )

    def _save_calculation(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QMessageBox.information(self, "商品選択", "商品を選択してください。")
            return
        if self._sale_price.value() <= 0:
            QMessageBox.warning(self, "入力確認", "想定売価を入力してください。")
            return
        if self._cost_price.value() <= 0:
            QMessageBox.warning(self, "入力確認", "原価を入力してください。")
            return
        shipping_cost = max(0, self._selected_shipping_cost - self._packaging.value())
        result = calc_profit(
            sale_price=self._sale_price.value(),
            cost_price=self._cost_price.value(),
            fee_rate=self._fee_rate.value() / 100,
            shipping_cost=shipping_cost,
            packaging_cost=self._packaging.value(),
            other_cost=0,
            target_profit=self._config.target_profit,
        )
        self._repo.add_calculation(
            item_id=item_id,
            offer_id=self._selected_offer_id,
            sale_price=self._sale_price.value(),
            fee_rate=self._fee_rate.value() / 100,
            shipping_cost=shipping_cost,
            packaging_cost=self._packaging.value(),
            other_cost=0,
            cost_price=self._cost_price.value(),
            profit=result.profit,
            profit_rate=result.profit_rate,
            breakeven_price=result.breakeven_price,
            target_profit=self._config.target_profit,
            min_price_for_target=result.min_price_for_target,
        )
        if any(
            [
                self._market_low.value(),
                self._market_mid.value(),
                self._market_high.value(),
                self._market_memo.toPlainText().strip(),
            ]
        ):
            self._repo.add_market_ref(
                item_id=item_id,
                low=self._market_low.value(),
                mid=self._market_mid.value(),
                high=self._market_high.value(),
                memo=self._market_memo.toPlainText().strip() or None,
            )
        QMessageBox.information(self, "保存完了", "計算結果を保存しました。")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, config=self._config)
        if dialog.exec() == SettingsDialog.Accepted:
            self._fee_rate.setValue(int(self._config.fee_rate * 100))
            self._packaging.setValue(self._config.default_packaging_cost)
            self._update_shipping()

    def _open_shipping_rules(self) -> None:
        dialog = ShippingRulesDialog(self, repo=self._repo)
        if dialog.exec() == ShippingRulesDialog.Accepted:
            self._update_shipping()

    def _import_items_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "商品CSVをインポート", "", "CSVファイル (*.csv)"
        )
        if not path:
            return
        count = import_items(self._repo, path)
        self.statusBar().showMessage(f"商品をインポートしました: {count} 件")
        self._load_items()

    def _export_items_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "商品CSVをエクスポート", "items.csv", "CSVファイル (*.csv)"
        )
        if not path:
            return
        export_items(self._repo, path)
        self.statusBar().showMessage("商品CSVを出力しました")

    def _export_offers_csv(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QMessageBox.information(self, "商品選択", "商品を選択してください。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "候補CSVをエクスポート", "offers.csv", "CSVファイル (*.csv)"
        )
        if not path:
            return
        export_offers(self._repo, item_id, path)
        self.statusBar().showMessage("候補CSVを出力しました")

    def _export_market_csv(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QMessageBox.information(self, "商品選択", "商品を選択してください。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "相場CSVをエクスポート", "market_refs.csv", "CSVファイル (*.csv)"
        )
        if not path:
            return
        export_market_refs(self._repo, item_id, path)
        self.statusBar().showMessage("相場CSVを出力しました")

    def _export_calculations_csv(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QMessageBox.information(self, "商品選択", "商品を選択してください。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "計算CSVをエクスポート", "calculations.csv", "CSVファイル (*.csv)"
        )
        if not path:
            return
        export_calculations(self._repo, item_id, path)
        self.statusBar().showMessage("計算CSVを出力しました")

    def _open_logs_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile("logs"))

    def _auto_reset_spinbox(self, spinbox: QSpinBox) -> None:
        spinbox.editingFinished.connect(
            lambda box=spinbox: self._reset_if_empty(box)
        )

    def _reset_if_empty(self, spinbox: QSpinBox) -> None:
        text = spinbox.lineEdit().text().strip()
        suffix = spinbox.suffix()
        if suffix:
            text = text.replace(suffix, "").strip()
        if text == "":
            spinbox.setValue(0)

    def _mark_warning(self, widget: QWidget) -> None:
        widget.setProperty("warning", "true")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _clear_warnings(self, widgets: list[QWidget]) -> None:
        for widget in widgets:
            widget.setProperty("warning", "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _clear_shipping_warnings(self) -> None:
        self._clear_warnings(
            [self._length, self._width, self._height, self._weight]
        )

    def _show_help_on_start(self) -> None:
        if self._item_list.count() == 0:
            QMessageBox.information(
                self,
                "はじめに",
                "商品を追加して、候補更新を実行すると仕入れ候補が表示されます。",
            )
