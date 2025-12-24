from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from app.infra.config import AppConfig, save_config
from app.infra.secrets import delete_secret, get_secret, set_secret


class SettingsDialog(QDialog):
    def __init__(self, parent=None, *, config: AppConfig) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self._config = config

        self._fee_rate = QSpinBox()
        self._fee_rate.setRange(0, 100)
        self._fee_rate.setValue(int(config.fee_rate * 100))

        self._target_profit = QSpinBox()
        self._target_profit.setRange(0, 1_000_000)
        self._target_profit.setValue(config.target_profit)

        self._packaging = QSpinBox()
        self._packaging.setRange(0, 100_000)
        self._packaging.setValue(config.default_packaging_cost)

        self._kakaku_mode = QLineEdit(config.kakaku_mode)
        self._amazon_locale = QLineEdit(config.amazon_locale)

        self._rakuten_app_id = QLineEdit(self._safe_get_secret("rakuten_app_id"))
        self._yahoo_client_id = QLineEdit(self._safe_get_secret("yahoo_client_id"))
        self._amazon_partner_tag = QLineEdit(
            self._safe_get_secret("amazon_partner_tag")
        )
        self._amazon_access_key = QLineEdit(
            self._safe_get_secret("amazon_access_key")
        )
        self._amazon_secret_key = QLineEdit(
            self._safe_get_secret("amazon_secret_key")
        )
        self._tavily_api_key = QLineEdit(self._safe_get_secret("tavily_api_key"))

        for field in [
            self._rakuten_app_id,
            self._yahoo_client_id,
            self._amazon_partner_tag,
            self._amazon_access_key,
            self._amazon_secret_key,
            self._tavily_api_key,
        ]:
            field.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("手数料率 (%)", self._fee_rate)
        form.addRow("目標利益", self._target_profit)
        form.addRow("資材費", self._packaging)
        form.addRow("価格.com取得方式", self._kakaku_mode)
        form.addRow("Amazonロケール", self._amazon_locale)
        form.addRow("楽天 App ID", self._rakuten_app_id)
        form.addRow("Yahoo クライアントID", self._yahoo_client_id)
        form.addRow("Amazon パートナータグ", self._amazon_partner_tag)
        form.addRow("Amazon アクセスキー", self._amazon_access_key)
        form.addRow("Amazon シークレットキー", self._amazon_secret_key)
        form.addRow("Tavily APIキー", self._tavily_api_key)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _save(self) -> None:
        self._config.fee_rate = self._fee_rate.value() / 100
        self._config.target_profit = self._target_profit.value()
        self._config.default_packaging_cost = self._packaging.value()
        self._config.kakaku_mode = self._kakaku_mode.text().strip() or "tavily"
        self._config.amazon_locale = self._amazon_locale.text().strip() or "JP"
        save_config(self._config)

        try:
            self._save_secret("rakuten_app_id", self._rakuten_app_id.text())
            self._save_secret("yahoo_client_id", self._yahoo_client_id.text())
            self._save_secret("amazon_partner_tag", self._amazon_partner_tag.text())
            self._save_secret("amazon_access_key", self._amazon_access_key.text())
            self._save_secret("amazon_secret_key", self._amazon_secret_key.text())
            self._save_secret("tavily_api_key", self._tavily_api_key.text())
        except RuntimeError:
            QMessageBox.warning(
                self,
                "キーリング",
                "keyringが利用できないため、シークレットは保存されませんでした。",
            )

        self.accept()

    def _save_secret(self, key: str, value: str) -> None:
        value = value.strip()
        if value:
            set_secret(key, value)
        else:
            delete_secret(key)

    def _safe_get_secret(self, key: str) -> str:
        try:
            return get_secret(key) or ""
        except RuntimeError:
            return ""
