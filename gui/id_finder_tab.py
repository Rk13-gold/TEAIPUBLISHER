"""
ID Finder – obtiene IDs de bots, canales y grupos vía Bot API.

Útil para conseguir el chat_id o bot_id que necesitan las configuraciones.
"""

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.telegram_bot_client import TelegramBotClient

logger = logging.getLogger(__name__)


# ── WORKERS ──


class BotInfoWorker(QThread):
    """Obtiene info del bot a partir de un token."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, token):
        super().__init__()
        self.token = token

    def run(self):
        try:
            client = TelegramBotClient(self.token)
            if not client.test_connection():
                self.error.emit("Token inválido o no se pudo conectar.")
                return
            info = client.get_bot_info()
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class ChatInfoWorker(QThread):
    """Resuelve un identificador de chat y devuelve sus datos."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, token, identifier):
        super().__init__()
        self.token = token
        self.identifier = identifier

    def run(self):
        try:
            client = TelegramBotClient(self.token)
            info = client.get_chat_info(self.identifier)
            if not info:
                self.error.emit("Chat no encontrado. Verificá el identificador.")
                return
            self.finished.emit({
                "id": info.id,
                "title": info.title,
                "username": info.username or "",
                "type": info.type,
                "member_count": info.member_count or 0,
                "is_private": getattr(info, "is_private", False),
                "description": getattr(info, "description", "") or "",
            })
        except Exception as e:
            self.error.emit(str(e))


# ── TAB ──


class IDFinderTab(QWidget):
    """Busca IDs de bots, canales y grupos usando la Bot API."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self._bot_worker = None
        self._chat_worker = None
        self._default_token = (
            getattr(config, "bot_token", None)
            or getattr(config, "telegram_token", None)
            or ""
        )
        self._init_ui()

    def _cleanup_worker(self, attr):
        worker = getattr(self, attr, None)
        if worker is not None:
            if worker.isRunning():
                worker.quit()
                worker.wait(2000)
            worker.deleteLater()
            setattr(self, attr, None)

    def closeEvent(self, event):
        self._cleanup_worker('_bot_worker')
        self._cleanup_worker('_chat_worker')
        event.accept()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QLabel("ID Finder – Bots, Canales y Grupos")
        header.setFont(QFont("", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # ── Token ──
        token_group = QGroupBox("Token del Bot")
        tl = QHBoxLayout(token_group)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("123456:ABCdef...")
        self.token_input.setText(self._default_token)
        tl.addWidget(self.token_input, 1)
        token_group.setLayout(tl)
        layout.addWidget(token_group)

        # ── Bot Info ──
        bot_group = QGroupBox("Info del Bot")
        bl = QVBoxLayout(bot_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Token usado:"))
        self.bot_token_label = QLabel("—")
        row1.addWidget(self.bot_token_label, 1)
        row1.addWidget(QLabel("ID:"))
        self.bot_id_label = QLabel("—")
        row1.addWidget(self.bot_id_label)
        bl.addLayout(row1)

        row2 = QHBoxLayout()
        self.btn_bot_info = QPushButton("Obtener Info del Bot")
        self.btn_bot_info.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #106ebe; }"
        )
        self.btn_bot_info.clicked.connect(self._fetch_bot_info)
        row2.addWidget(self.btn_bot_info)
        bl.addLayout(row2)

        bot_group.setLayout(bl)
        layout.addWidget(bot_group)

        # ── Chat resolver ──
        chat_group = QGroupBox("Resolver Chat / Canal / Grupo")
        cl = QVBoxLayout(chat_group)

        irow = QHBoxLayout()
        irow.addWidget(QLabel("Identificador:"))
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("@username o -100123456789")
        irow.addWidget(self.chat_input, 1)
        self.btn_chat_info = QPushButton("Resolver")
        self.btn_chat_info.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #106ebe; }"
        )
        self.btn_chat_info.clicked.connect(self._fetch_chat_info)
        irow.addWidget(self.btn_chat_info)
        cl.addLayout(irow)

        # Tabla de resultados
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Campo", "Valor", "", "", ""])
        h = self.results_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cl.addWidget(self.results_table, 1)

        chat_group.setLayout(cl)
        layout.addWidget(chat_group, 1)

        # ── Estado ──
        self.status_label = QLabel("Listo. Ingresá un token de bot para empezar.")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    # ── Lógica ──

    def _get_token(self):
        t = self.token_input.text().strip()
        if not t:
            QMessageBox.warning(self, "Token requerido", "Ingresá el token del bot.")
        return t

    def _fetch_bot_info(self):
        token = self._get_token()
        if not token:
            return

        self.btn_bot_info.setEnabled(False)
        self.status_label.setText("Consultando bot...")

        self._bot_worker = BotInfoWorker(token)
        self._bot_worker.finished.connect(self._on_bot_info)
        self._bot_worker.error.connect(self._on_error)
        self._bot_worker.start()

    def _on_bot_info(self, info):
        self.btn_bot_info.setEnabled(True)
        self._cleanup_worker('_bot_worker')
        self.bot_token_label.setText(info.get("username", "?"))
        self.bot_id_label.setText(str(info.get("id", "?")))
        self.status_label.setText(
            f"Bot @{info.get('username', '?')} (ID: {info.get('id', '?')})"
        )

    def _on_error(self, msg):
        self.btn_bot_info.setEnabled(True)
        self.btn_chat_info.setEnabled(True)
        self._cleanup_worker('_bot_worker')
        self._cleanup_worker('_chat_worker')
        self.status_label.setText(f"Error: {msg}")

    def _fetch_chat_info(self):
        token = self._get_token()
        if not token:
            return
        identifier = self.chat_input.text().strip()
        if not identifier:
            QMessageBox.warning(self, "Identificador", "Ingresá @username o chat_id.")
            return

        self.btn_chat_info.setEnabled(False)
        self.status_label.setText(f"Resolviendo {identifier}...")

        self._chat_worker = ChatInfoWorker(token, identifier)
        self._chat_worker.finished.connect(self._on_chat_info)
        self._chat_worker.error.connect(self._on_error)
        self._chat_worker.start()

    def _on_chat_info(self, info):
        self.btn_chat_info.setEnabled(True)
        self._cleanup_worker('_chat_worker')

        rows = [
            ("ID", str(info["id"])),
            ("Título", info["title"]),
            ("Username", f"@{info['username']}" if info["username"] else "—"),
            ("Tipo", info["type"]),
            ("Miembros", str(info["member_count"])),
        ]
        self.results_table.setRowCount(len(rows))
        for i, (campo, valor) in enumerate(rows):
            self.results_table.setItem(i, 0, QTableWidgetItem(campo))
            item = QTableWidgetItem(valor)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.results_table.setItem(i, 1, QTableWidgetItem(valor))

        self.status_label.setText(
            f"{info['title']} — ID: {info['id']}  |  Copiado al portapapeles"
        )
        # Copiar ID al portapapeles
        QApplication = __import__("PySide6.QtWidgets").QtWidgets.QApplication
        QApplication.clipboard().setText(str(info["id"]))


IDFinder = IDFinderTab
