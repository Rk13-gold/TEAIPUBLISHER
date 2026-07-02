from __future__ import annotations

"""Channel Manager Tab with Telegram Bot integration."""

import csv
import logging
from datetime import datetime
from typing import Dict, List

try:
    from gui.telegram_theme_simple import TelegramThemeSimple as TelegramTheme
except ImportError:  # pragma: no cover - optional dependency
    TelegramTheme = None

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QGroupBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QHeaderView,
)

from core.config import Config
from services.telegram_bot_client import TelegramBotClient, BotChannelInfo

logger = logging.getLogger(__name__)


def _channel_to_dict(info: BotChannelInfo, permissions: Dict | None) -> Dict:
    return {
        "id": info.id,
        "title": info.title,
        "username": info.username or "",
        "type": info.type,
        "member_count": info.member_count or 0,
        "is_verified": info.is_verified,
        "is_scam": info.is_scam,
        "description": info.description or "",
        "permissions": permissions or {},
    }


class ChannelLookupWorker(QThread):
    """Worker that fetches channel info sequentially using the bot token."""

    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, bot_token: str, channel_ids: List[str]):
        super().__init__()
        self.bot_token = bot_token
        self.channel_ids = channel_ids

    def run(self) -> None:  # pragma: no cover - Qt thread
        try:
            if not self.bot_token:
                self.error.emit("Bot token no configurado.")
                return

            client = TelegramBotClient(self.bot_token)
            self.progress.emit(5, "Conectando con el bot...")

            if not client.test_connection():
                self.error.emit("No se pudo conectar con el bot. Verifica el token.")
                return

            found_channels: List[Dict] = []
            total = max(len(self.channel_ids), 1)

            for index, raw_id in enumerate(self.channel_ids, start=1):
                channel_id = raw_id.strip()
                if not channel_id:
                    continue

                progress = 5 + int((index / total) * 85)
                self.progress.emit(progress, f"Buscando {channel_id}...")

                info = client.get_chat_info(channel_id)
                if not info:
                    continue

                permissions = client.validate_bot_permissions(str(info.id))
                found_channels.append(_channel_to_dict(info, permissions))

            self.progress.emit(100, "Búsqueda completada")
            self.finished.emit(found_channels)

        except Exception as exc:  # pragma: no cover - runtime feedback
            logger.exception("Channel lookup failed")
            self.error.emit(str(exc))


class SimpleChannelTab(QWidget):
    """Channel manager tab with Telegram Bot operations."""

    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        self.config = config or Config()
        self.channels: Dict[str, Dict] = {}
        self.lookup_worker: ChannelLookupWorker | None = None

        if TelegramTheme:
            TelegramTheme.apply_simple_theme(self)

        self._build_ui()

    def _cleanup_worker(self, attr):
        worker = getattr(self, attr, None)
        if worker is not None:
            if worker.isRunning():
                worker.quit()
                worker.wait(2000)
            worker.deleteLater()
            setattr(self, attr, None)

    def closeEvent(self, event):
        self._cleanup_worker('lookup_worker')
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # UI BUILDING
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(14)
        container_layout.setContentsMargins(18, 18, 18, 18)

        header = QLabel("🎛️ Channel Manager")
        header.setStyleSheet("font-size: 20px; font-weight: 600;")
        container_layout.addWidget(header)

        subheader = QLabel(
            "Gestiona y verifica los canales y grupos donde tu bot tiene permisos de administrador."
        )
        subheader.setWordWrap(True)
        container_layout.addWidget(subheader)

        self._build_token_section(container_layout)
        self._build_actions_section(container_layout)
        self._build_results_section(container_layout)

        # Scroll wrapper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

    def _build_token_section(self, parent_layout: QVBoxLayout) -> None:
        token_group = QGroupBox("Token del bot")
        token_layout = QVBoxLayout(token_group)

        row = QHBoxLayout()
        self.token_input = QLineEdit(self.config.bot_token or self.config.telegram_token or "")
        self.token_input.setEchoMode(QLineEdit.Password)
        row.addWidget(self.token_input)

        self.toggle_token_btn = QPushButton("👁️")
        self.toggle_token_btn.setFixedWidth(34)
        self.toggle_token_btn.clicked.connect(self._toggle_token_visibility)
        row.addWidget(self.toggle_token_btn)

        self.test_bot_btn = QPushButton("🤖 Probar conexión")
        self.test_bot_btn.clicked.connect(self._test_bot_connection)

        self.validate_config_btn = QPushButton("🔎 Probar configuración")
        self.validate_config_btn.clicked.connect(self._test_configuration)
        row.addWidget(self.validate_config_btn)
        row.addWidget(self.test_bot_btn)

        token_layout.addLayout(row)

        self.status_label = QLabel("Listo para comenzar")
        token_layout.addWidget(self.status_label)

        parent_layout.addWidget(token_group)

    def _build_actions_section(self, parent_layout: QVBoxLayout) -> None:
        actions_group = QGroupBox("Búsqueda de canales")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(10)

        single_row = QHBoxLayout()
        single_row.addWidget(QLabel("Canal o ID:"))
        self.single_input = QLineEdit()
        self.single_input.setPlaceholderText("@canal o -100123456789")
        single_row.addWidget(self.single_input)

        self.single_search_btn = QPushButton("Agregar canal")
        self.single_search_btn.clicked.connect(self._lookup_single_channel)
        single_row.addWidget(self.single_search_btn)

        actions_layout.addLayout(single_row)

        self.bulk_input = QPlainTextEdit()
        self.bulk_input.setPlaceholderText("Introduce múltiples canales o IDs (uno por línea)")
        self.bulk_input.setMaximumHeight(120)
        actions_layout.addWidget(self.bulk_input)

        bulk_row = QHBoxLayout()
        self.bulk_search_btn = QPushButton("🔍 Buscar lista")
        self.bulk_search_btn.clicked.connect(self._lookup_multiple_channels)
        bulk_row.addWidget(self.bulk_search_btn)

        self.list_admin_btn = QPushButton("📋 Ver administrados")
        self.list_admin_btn.clicked.connect(self._list_administered_channels)
        bulk_row.addWidget(self.list_admin_btn)

        self.clear_results_btn = QPushButton("Limpiar resultados")
        self.clear_results_btn.clicked.connect(self._clear_results)
        bulk_row.addWidget(self.clear_results_btn)

        bulk_row.addStretch()
        actions_layout.addLayout(bulk_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        actions_layout.addWidget(self.progress_bar)

        parent_layout.addWidget(actions_group)

    def _build_results_section(self, parent_layout: QVBoxLayout) -> None:
        results_group = QGroupBox("Canales encontrados")
        results_layout = QVBoxLayout(results_group)

        self.channels_table = QTableWidget(0, 6)
        self.channels_table.setHorizontalHeaderLabels(
            ["Título", "Usuario", "ID", "Tipo", "Miembros", "Estado"]
        )
        header = self.channels_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.channels_table)

        buttons_row = QHBoxLayout()
        self.export_btn = QPushButton("📤 Exportar CSV")
        self.export_btn.clicked.connect(self._export_channels)
        self.export_btn.setEnabled(False)
        buttons_row.addWidget(self.export_btn)

        self.remove_selected_btn = QPushButton("Eliminar seleccionados")
        self.remove_selected_btn.clicked.connect(self._remove_selected_rows)
        buttons_row.addWidget(self.remove_selected_btn)

        self.set_chat_btn = QPushButton("📌 Establecer como chat")
        self.set_chat_btn.clicked.connect(self._set_selected_as_chat)
        buttons_row.addWidget(self.set_chat_btn)

        buttons_row.addStretch()
        results_layout.addLayout(buttons_row)

        parent_layout.addWidget(results_group)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _toggle_token_visibility(self) -> None:
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.toggle_token_btn.setText("🔒")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.toggle_token_btn.setText("👁️")

    def _ensure_token(self) -> str | None:
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Token requerido", "Introduce un token de bot válido.")
            return None

        if token != self.config.bot_token:
            self.config.bot_token = token
            self.config.telegram_token = token
            if hasattr(self.config, "save_config"):
                try:
                    self.config.save_config()
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning("No se pudo guardar config: %s", exc)

        return token

    def _build_client(self) -> TelegramBotClient | None:
        token = self._ensure_token()
        if not token:
            return None
        return TelegramBotClient(token)

    @Slot()
    def _test_bot_connection(self) -> None:
        client = self._build_client()
        if not client:
            return

        self.status_label.setText("Conectando con el bot...")
        try:
            if client.test_connection():
                info = client.get_bot_info()
                username = info.get("username", "desconocido")
                QMessageBox.information(
                    self,
                    "Bot conectado",
                    f"✅ Conexión exitosa con @{username}\nID: {info.get('id')}",
                )
                self.status_label.setText(f"Bot conectado: @{username}")
            else:
                QMessageBox.warning(
                    self,
                    "Conexión fallida",
                    "No se pudo verificar el token. Intenta nuevamente.",
                )
                self.status_label.setText("Error al conectar con el bot")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error conectando con el bot: {exc}")
            self.status_label.setText("Error al conectar con el bot")

    @Slot()
    def _test_configuration(self) -> None:
        """Validate token and configured chat in `Config` using check_telegram_bot_and_chat."""
        token = self._ensure_token()
        if not token:
            return

        self.status_label.setText("Validando configuración...")
        ok, message = self.config.check_telegram_bot_and_chat()
        if ok:
            QMessageBox.information(self, "Configuración válida", f"✅ {message}")
            self.status_label.setText("Configuración valida")
        else:
            QMessageBox.critical(self, "Configuración inválida", f"❌ {message}\n\nAsegúrate que el token es correcto y que el bot está en el canal como administrador.")
            self.status_label.setText(f"Error: {message}")

    @Slot()
    def _lookup_single_channel(self) -> None:
        client = self._build_client()
        if not client:
            return

        channel_id = self.single_input.text().strip()
        if not channel_id:
            QMessageBox.warning(self, "Canal requerido", "Introduce un canal o ID.")
            return

        self.status_label.setText(f"Buscando {channel_id}...")
        try:
            info = client.get_chat_info(channel_id)
            if not info:
                QMessageBox.warning(self, "No encontrado", f"No se encontró información para {channel_id}.")
                self.status_label.setText("Canal no encontrado")
                return

            permissions = client.validate_bot_permissions(str(info.id))
            self._store_channel(_channel_to_dict(info, permissions))
            self.status_label.setText(f"Canal añadido: {info.title}")
            self.single_input.clear()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error obteniendo el canal: {exc}")
            self.status_label.setText("Error buscando canal")

    @Slot()
    def _lookup_multiple_channels(self) -> None:
        token = self._ensure_token()
        if not token:
            return

        ids_text = self.bulk_input.toPlainText().strip()
        if not ids_text:
            QMessageBox.warning(self, "Sin canales", "Introduce al menos un canal o ID.")
            return

        channel_ids = [line.strip() for line in ids_text.splitlines() if line.strip()]
        if not channel_ids:
            QMessageBox.warning(self, "Sin canales", "No se encontraron entradas válidas.")
            return

        if self.lookup_worker and self.lookup_worker.isRunning():
            QMessageBox.information(self, "Búsqueda en curso", "Espera a que finalice la búsqueda actual.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Iniciando búsqueda...")
        self.bulk_search_btn.setEnabled(False)

        self.lookup_worker = ChannelLookupWorker(token, channel_ids)
        self.lookup_worker.progress.connect(self._on_lookup_progress)
        self.lookup_worker.finished.connect(self._on_lookup_finished)
        self.lookup_worker.error.connect(self._on_lookup_error)
        self.lookup_worker.start()

    @Slot()
    def _list_administered_channels(self) -> None:
        token = self._ensure_token()
        if not token:
            return

        self.list_admin_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Buscando canales administrados...")

        try:
            client = TelegramBotClient(token)
            raw_chats = client.get_administered_chats(200)

            if not raw_chats:
                QMessageBox.information(
                    self,
                    "Sin resultados",
                    "No se encontraron canales o grupos administrados en los últimos eventos del bot.",
                )
                self.status_label.setText("No se encontraron canales administrados")
                return

            summary_lines: List[str] = []
            for chat in raw_chats:
                info = client.get_chat_info(str(chat["id"]))
                if info:
                    permissions = client.validate_bot_permissions(str(info.id))
                    channel_dict = _channel_to_dict(info, permissions)
                else:
                    channel_dict = {
                        "id": chat["id"],
                        "title": chat["title"],
                        "username": chat.get("username", ""),
                        "type": chat.get("type", "desconocido"),
                        "member_count": 0,
                        "is_verified": False,
                        "is_scam": False,
                        "description": "",
                        "permissions": {},
                    }

                self._store_channel(channel_dict)
                summary_lines.append(f"{channel_dict['title']} — {channel_dict['id']}")

            preview = "\n".join(summary_lines[:20])
            remaining = len(summary_lines) - 20
            if remaining > 0:
                preview += f"\n... y {remaining} más"

            QMessageBox.information(
                self,
                "Canales administrados",
                f"Se encontraron {len(summary_lines)} canales/grupos administrados:\n\n{preview}",
            )
            self.status_label.setText(f"✅ {len(summary_lines)} canales administrados encontrados")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la lista: {exc}")
            self.status_label.setText("Error obteniendo canales administrados")
        finally:
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 100)
            self.list_admin_btn.setEnabled(True)

    @Slot()
    def _set_selected_as_chat(self) -> None:
        """Take the currently selected row in the channels table and set it as the current config.telegram_chat_id."""
        selected_rows = {idx.row() for idx in self.channels_table.selectedIndexes()}
        if not selected_rows:
            QMessageBox.information(self, "Sin selección", "Selecciona al menos un canal en la lista.")
            return
        # Use the first selected
        row = sorted(selected_rows)[0]
        item = self.channels_table.item(row, 2)
        if not item:
            QMessageBox.warning(self, "Error", "No se pudo leer el ID del canal seleccionado.")
            return
        selected_id = item.text().strip()
        # Save into config
        self.config.telegram_chat_id = selected_id
        try:
            self.config.save_config()
        except Exception as exc:
            logger.warning("No se pudo guardar la configuración: %s", exc)
        QMessageBox.information(self, "Configuración guardada", f"ID de chat guardado: {selected_id}")
        self.status_label.setText(f"Chat configurado: {selected_id}")

    @Slot(int, str)
    def _on_lookup_progress(self, value: int, message: str) -> None:
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    @Slot(list)
    def _on_lookup_finished(self, channels: List[Dict]) -> None:
        self.bulk_search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._cleanup_worker('lookup_worker')

        for channel in channels:
            self._store_channel(channel)

        if channels:
            self.status_label.setText(f"✅ {len(channels)} canales actualizados")
        else:
            self.status_label.setText("No se encontraron canales nuevos")

    @Slot(str)
    def _on_lookup_error(self, message: str) -> None:
        self.bulk_search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._cleanup_worker('lookup_worker')
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText(f"Error: {message}")

    def _store_channel(self, channel_data: Dict) -> None:
        channel_id = str(channel_data["id"])
        self.channels[channel_id] = channel_data
        self._refresh_table()
        self.export_btn.setEnabled(bool(self.channels))

    def _refresh_table(self) -> None:
        rows = list(self.channels.values())
        self.channels_table.setRowCount(len(rows))

        for row_index, channel in enumerate(rows):
            self.channels_table.setItem(row_index, 0, QTableWidgetItem(channel["title"]))
            username = f"@{channel['username']}" if channel["username"] else "Privado"
            self.channels_table.setItem(row_index, 1, QTableWidgetItem(username))
            self.channels_table.setItem(row_index, 2, QTableWidgetItem(str(channel["id"])))
            self.channels_table.setItem(row_index, 3, QTableWidgetItem(channel["type"].title()))
            members = f"{channel['member_count']:,}" if channel["member_count"] else "Desconocido"
            self.channels_table.setItem(row_index, 4, QTableWidgetItem(members))
            status = channel.get("permissions", {}).get("status", "desconocido").title()
            self.channels_table.setItem(row_index, 5, QTableWidgetItem(status))

    @Slot()
    def _remove_selected_rows(self) -> None:
        selected_rows = {idx.row() for idx in self.channels_table.selectedIndexes()}
        if not selected_rows:
            QMessageBox.information(self, "Sin selección", "Selecciona al menos un canal para eliminar.")
            return

        rows = list(self.channels.keys())
        for row in sorted(selected_rows, reverse=True):
            if row < len(rows):
                self.channels.pop(rows[row], None)

        self._refresh_table()
        self.export_btn.setEnabled(bool(self.channels))
        self.status_label.setText("Canales eliminados de la lista")

    @Slot()
    def _clear_results(self) -> None:
        self.channels.clear()
        self._refresh_table()
        self.export_btn.setEnabled(False)
        self.status_label.setText("Resultados limpiados")

    @Slot()
    def _export_channels(self) -> None:
        if not self.channels:
            QMessageBox.information(self, "Sin datos", "No hay canales para exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar canales",
            f"channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)",
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Título", "Usuario", "ID", "Tipo", "Miembros", "Estado", "Descripción"])
                for channel in self.channels.values():
                    writer.writerow(
                        [
                            channel["title"],
                            channel["username"],
                            channel["id"],
                            channel["type"],
                            channel["member_count"],
                            channel.get("permissions", {}).get("status", "desconocido"),
                            channel["description"].replace("\n", " "),
                        ]
                    )

            QMessageBox.information(self, "Exportación completada", f"Datos guardados en {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {exc}")

