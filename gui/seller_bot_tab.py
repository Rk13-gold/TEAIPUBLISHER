from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QComboBox, QDateTimeEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QFrame, QSplitter, QAbstractItemView,
    QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont, QIcon

from core.database import Database
from core.models import Bot, Chat, Schedule, ScheduleStatus
from gui.emoji_picker import EmojiPicker
from gui.emoji_renderer import render_emoji
from gui.emoji_text_helper import insert_emoji_textedit, emoji_document_to_plaintext
from services.scheduler_service import SchedulerWorker

_STICKER = """
QGroupBox {
    border: 1px solid #333;
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px 12px 12px 12px;
    background: #0a0a0a;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #89b4fa;
}
QTextEdit, QLineEdit, QComboBox, QDateTimeEdit {
    border: 1px solid #333;
    border-radius: 4px;
    padding: 4px 6px;
    background: transparent;
    color: #fff;
}
QTextEdit:focus, QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
    border: 1px solid #7c5cfc;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: #1a1a1a;
    color: #fff;
    selection-background-color: #7c5cfc;
}
QTableWidget {
    border: 1px solid #333;
    border-radius: 4px;
    background: transparent;
    color: #fff;
    gridline-color: #222;
}
QTableWidget::item:selected {
    background: #7c5cfc;
}
QHeaderView::section {
    background: #1a1a1a;
    color: #aaa;
    border: none;
    padding: 6px;
    font-weight: bold;
}
QCheckBox {
    color: #ddd;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555;
    background: transparent;
}
QCheckBox::indicator:checked {
    background: #7c5cfc;
    border: 1px solid #7c5cfc;
}
QPushButton {
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}
"""


class SellerBotTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._scheduler = None
        self._current_bot_id = None

        self.setStyleSheet(_STICKER)
        main = QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        # Header
        header = QLabel("Bot Vendedor — Programación de Mensajes")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; padding: 4px 0; background: transparent;")
        main.addWidget(header)

        # Top controls
        top = QHBoxLayout()
        top.setSpacing(8)

        self.bot_combo = QComboBox()
        self.bot_combo.setMinimumWidth(200)
        self.bot_combo.currentIndexChanged.connect(self._on_bot_changed)
        top.addWidget(QLabel("Bot:"))
        top.addWidget(self.bot_combo)

        self.chat_combo = QComboBox()
        self.chat_combo.setMinimumWidth(220)
        top.addWidget(QLabel("Chat:"))
        top.addWidget(self.chat_combo)

        top.addStretch()
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("Recargar bots y chats")
        self.refresh_btn.clicked.connect(self._load_bots)
        top.addWidget(self.refresh_btn)

        main.addLayout(top)

        # Splitter: message config / schedule list
        splitter = QSplitter(Qt.Vertical)

        # --- Message config ---
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(6)

        msg_group = QGroupBox("Mensaje")
        msg_layout = QVBoxLayout(msg_group)
        msg_layout.setSpacing(6)

        # Content editor
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Escribe el mensaje (puedes usar HTML: <b>, <i>, <a href=...)")
        self.content_edit.setMinimumHeight(100)
        msg_layout.addWidget(self.content_edit)

        # Emoji button row
        emoji_row = QHBoxLayout()
        self.emoji_btn = QPushButton()
        self.emoji_btn.setFixedSize(34, 34)
        _pix = render_emoji("😊", 20)
        if _pix and not _pix.isNull():
            self.emoji_btn.setIcon(QIcon(_pix))
            self.emoji_btn.setIconSize(_pix.size())
        self.emoji_btn.setToolTip("Insertar emoji")
        self.emoji_btn.clicked.connect(self._insert_emoji)
        self.emoji_btn.setStyleSheet("QPushButton { background: transparent; border: 1px solid #333; border-radius: 6px; }")
        emoji_row.addWidget(self.emoji_btn)
        emoji_row.addStretch()
        msg_layout.addLayout(emoji_row)

        config_layout.addWidget(msg_group)

        # Schedule config
        sched_group = QGroupBox("Programar Envío")
        sched_layout = QVBoxLayout(sched_group)
        sched_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Fecha y hora:"))
        self.dt_picker = QDateTimeEdit()
        self.dt_picker.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.dt_picker.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_picker.setCalendarPopup(True)
        row1.addWidget(self.dt_picker)

        row1.addWidget(QLabel("Repetir:"))
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["Sin repetición", "Cada día", "Cada semana", "Cada mes"])
        self.repeat_combo.setCurrentIndex(0)
        row1.addWidget(self.repeat_combo)

        sched_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.schedule_btn = QPushButton("📅 Programar Envío")
        self.schedule_btn.setStyleSheet("""
            QPushButton { background: #7c5cfc; color: #fff; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; }
            QPushButton:hover { background: #9178ff; }
            QPushButton:pressed { background: #6a4de0; }
        """)
        self.schedule_btn.clicked.connect(self._schedule_message)
        row2.addWidget(self.schedule_btn)

        self.send_now_btn = QPushButton("🚀 Enviar Ahora")
        self.send_now_btn.setStyleSheet("""
            QPushButton { background: #2a6d9c; color: #fff; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; }
            QPushButton:hover { background: #3580b8; }
        """)
        self.send_now_btn.clicked.connect(self._send_now)
        row2.addWidget(self.send_now_btn)
        row2.addStretch()

        sched_layout.addLayout(row2)
        config_layout.addWidget(sched_group)

        # Scheduler controls
        sched_ctrl = QHBoxLayout()
        self.toggle_scheduler_btn = QPushButton("▶ Iniciar Programador")
        self.toggle_scheduler_btn.setStyleSheet("""
            QPushButton { background: #2e7d32; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background: #3a9b40; }
        """)
        self.toggle_scheduler_btn.clicked.connect(self._toggle_scheduler)
        sched_ctrl.addWidget(self.toggle_scheduler_btn)

        self.scheduler_status = QLabel("⏹ Detenido")
        self.scheduler_status.setStyleSheet("color: #888; background: transparent;")
        sched_ctrl.addWidget(self.scheduler_status)
        sched_ctrl.addStretch()

        config_layout.addLayout(sched_ctrl)
        splitter.addWidget(config_widget)

        # --- Schedule list ---
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("Programaciones"))
        list_header.addStretch()
        self.delete_sched_btn = QPushButton("🗑 Eliminar seleccionadas")
        self.delete_sched_btn.setStyleSheet("QPushButton { background: #c62828; color: #fff; border: none; border-radius: 4px; padding: 4px 12px; }")
        self.delete_sched_btn.clicked.connect(self._delete_selected)
        list_header.addWidget(self.delete_sched_btn)
        list_layout.addLayout(list_header)

        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels(["ID", "Bot", "Chat", "Programado", "Repite", "Estado", "Último envío"])
        self.schedule_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.schedule_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.schedule_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        self.schedule_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.schedule_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.schedule_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setStyleSheet("alternate-background-color: #111;")
        list_layout.addWidget(self.schedule_table)

        splitter.addWidget(list_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        main.addWidget(splitter, 1)

        # Log
        self.log_label = QLabel("")
        self.log_label.setStyleSheet("color: #888; font-size: 10px; background: transparent; padding: 2px 0;")
        main.addWidget(self.log_label)

        # Load data
        QTimer.singleShot(0, self._load_bots)
        QTimer.singleShot(100, self._refresh_table)

    # --- Bot / Chat loading ---

    def _load_bots(self):
        self.bot_combo.clear()
        try:
            db = Database()
            session = db.get_session()
            bots = session.query(Bot).filter_by(activo=True).all()
            for b in bots:
                self.bot_combo.addItem(f"{b.nombre} ({b.token_api[:12]}...)", b.id)
            db.dispose()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los bots: {e}")

    def _on_bot_changed(self, idx):
        self.chat_combo.clear()
        bot_id = self.bot_combo.itemData(idx)
        if bot_id is None:
            return
        self._current_bot_id = bot_id
        try:
            db = Database()
            session = db.get_session()
            chats = session.query(Chat).filter_by(bot_id=bot_id, activo=True).all()
            for c in chats:
                label = f"{c.nombre or 'Sin nombre'} ({c.chat_id})"
                self.chat_combo.addItem(label, c.id)
            db.dispose()
        except Exception as e:
            self.log_label.setText(f"Error cargando chats: {e}")

    # --- Emoji ---

    def _insert_emoji(self):
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                insert_emoji_textedit(self.content_edit, emoji)

    # --- Schedule ---

    def _schedule_message(self):
        content = emoji_document_to_plaintext(self.content_edit.document()).strip()
        if not content:
            QMessageBox.warning(self, "Campos requeridos", "Escribe un mensaje para programar.")
            return
        bot_data = self.bot_combo.currentData()
        chat_data = self.chat_combo.currentData()
        if bot_data is None or chat_data is None:
            QMessageBox.warning(self, "Campos requeridos", "Selecciona un bot y un chat.")
            return

        repeat_map = {"Sin repetición": None, "Cada día": "daily", "Cada semana": "weekly", "Cada mes": "monthly"}
        repeat = repeat_map[self.repeat_combo.currentText()]
        dt = self.dt_picker.dateTime().toPython()

        try:
            db = Database()
            session = db.get_session()
            sched = Schedule(
                bot_id=bot_data,
                chat_id=chat_data,
                content=content,
                scheduled_at=dt,
                repeat=repeat,
                status='pending',
                created_at=datetime.now()
            )
            session.add(sched)
            session.commit()
            db.dispose()
            self.log_label.setText(f"✅ Programado para {dt.strftime('%Y-%m-%d %H:%M')}")
            self._refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo programar: {e}")

    def _send_now(self):
        content = emoji_document_to_plaintext(self.content_edit.document()).strip()
        if not content:
            QMessageBox.warning(self, "Mensaje vacío", "Escribe un mensaje para enviar.")
            return
        bot_data = self.bot_combo.currentData()
        chat_data = self.chat_combo.currentData()
        if bot_data is None or chat_data is None:
            QMessageBox.warning(self, "Campos requeridos", "Selecciona un bot y un chat.")
            return

        try:
            db = Database()
            session = db.get_session()
            bot = session.query(Bot).filter_by(id=bot_data).first()
            chat = session.query(Chat).filter_by(id=chat_data).first()
            db.dispose()

            if not bot or not chat:
                QMessageBox.warning(self, "Error", "Bot o chat no encontrado.")
                return

            import requests as req
            resp = req.post(
                f"https://api.telegram.org/bot{bot.token_api}/sendMessage",
                json={
                    'chat_id': chat.chat_id,
                    'text': content,
                    'parse_mode': 'HTML',
                },
                timeout=(5, 10)
            )
            data = resp.json()
            if data.get('ok'):
                self.log_label.setText(f"✅ Mensaje enviado a {chat.nombre or chat.chat_id}")
            else:
                desc = data.get('description', 'error desconocido')
                self.log_label.setText(f"❌ Error: {desc}")
        except Exception as e:
            self.log_label.setText(f"❌ Error: {e}")

    # --- Scheduler toggle ---

    def _toggle_scheduler(self):
        if self._scheduler and self._scheduler.isRunning():
            self._scheduler.stop()
            self._scheduler = None
            self.toggle_scheduler_btn.setText("▶ Iniciar Programador")
            self.toggle_scheduler_btn.setStyleSheet("""
                QPushButton { background: #2e7d32; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; font-weight: bold; }
                QPushButton:hover { background: #3a9b40; }
            """)
            self.scheduler_status.setText("⏹ Detenido")
        else:
            self._scheduler = SchedulerWorker(self)
            self._scheduler.log.connect(self.log_label.setText)
            self._scheduler.schedule_updated.connect(self._refresh_table)
            self._scheduler.start()
            self.toggle_scheduler_btn.setText("⏹ Detener Programador")
            self.toggle_scheduler_btn.setStyleSheet("""
                QPushButton { background: #c62828; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; font-weight: bold; }
                QPushButton:hover { background: #e53935; }
            """)
            self.scheduler_status.setText("▶ Corriendo")

    # --- Schedule table ---

    def _refresh_table(self):
        try:
            db = Database()
            session = db.get_session()
            schedules = session.query(Schedule).order_by(Schedule.scheduled_at.desc()).all()

            self.schedule_table.setRowCount(len(schedules))
            for row, s in enumerate(schedules):
                bot = session.query(Bot).filter_by(id=s.bot_id).first()
                chat = session.query(Chat).filter_by(id=s.chat_id).first()
                self.schedule_table.setItem(row, 0, QTableWidgetItem(str(s.id)))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(bot.nombre if bot else '?'))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(chat.nombre or chat.chat_id if chat else '?'))
                self.schedule_table.setItem(row, 3, QTableWidgetItem(s.scheduled_at.strftime('%Y-%m-%d %H:%M') if s.scheduled_at else ''))
                self.schedule_table.setItem(row, 4, QTableWidgetItem(s.repeat or 'No'))
                status_icon = {'pending': '⏳', 'sent': '✅', 'failed': '❌'}
                self.schedule_table.setItem(row, 5, QTableWidgetItem(f"{status_icon.get(s.status, '?')} {s.status}"))
                self.schedule_table.setItem(row, 6, QTableWidgetItem(s.last_sent_at.strftime('%Y-%m-%d %H:%M') if s.last_sent_at else ''))
            db.dispose()
        except Exception as e:
            self.log_label.setText(f"Error al cargar programaciones: {e}")

    def _delete_selected(self):
        rows = set(i.row() for i in self.schedule_table.selectedIndexes())
        if not rows:
            QMessageBox.information(self, "Selección", "Selecciona una o más filas para eliminar.")
            return
        reply = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar {len(rows)} programación(es)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            db = Database()
            session = db.get_session()
            for row in rows:
                item = self.schedule_table.item(row, 0)
                if item:
                    sched_id = int(item.text())
                    sched = session.query(Schedule).filter_by(id=sched_id).first()
                    if sched:
                        session.delete(sched)
            session.commit()
            db.dispose()
            self._refresh_table()
            self.log_label.setText(f"🗑 {len(rows)} programación(es) eliminada(s)")
        except Exception as e:
            self.log_label.setText(f"Error al eliminar: {e}")

    # --- Cleanup ---

    def closeEvent(self, event):
        if self._scheduler and self._scheduler.isRunning():
            self._scheduler.stop()
        super().closeEvent(event)
