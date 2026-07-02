"""
Centro de Mando – interfaz unificada con 3 pestañas internas:

  1. Red Telegram   → formularios Bot/Chat + INICIAR MOTORES
  2. Generador IA   → nichos + generar post
  3. Caja           → tabla de ventas + verificar pagos PayPal
"""

import asyncio
import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.database import Database
from core.models import Bot, Chat, Nicho, Venta

logger = logging.getLogger(__name__)


# ─────────────────────────────── WORKERS ───────────────────────────────

class BotEngineWorker(QThread):
    """Arranca el TelegramEngine en un hilo separado con su propio event loop."""

    status = Signal(str)
    error = Signal(str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.engine = None
        self._loop = None

    def run(self):
        async def _start():
            from services.bot_engine import TelegramEngine

            self.engine = TelegramEngine(self.config)
            self.status.emit("Inicializando bots…")
            await self.engine.init()
            self.status.emit(f"{len(self.engine.clients)} bot(es) conectados.")
            await self.engine.start_listeners()
            self.status.emit("✅ Motores encendidos – escuchando mensajes…")
            await self.engine.run()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(_start())
        except Exception as e:
            self.error.emit(str(e))

    def stop_engine(self):
        if self.engine and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.engine.stop(), self._loop)


class AiGenerateWorker(QThread):
    """Genera un post de IA en segundo plano."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, nicho_id, config):
        super().__init__()
        self.nicho_id = nicho_id
        self.config = config

    def run(self):
        try:
            from services.ai_content_generator import generate_post

            result = generate_post(self.nicho_id, self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PayPalCheckWorker(QThread):
    """Verifica pagos PayPal pendientes en segundo plano."""

    finished = Signal(list)
    error = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            from services.paypal_manager import PayPalManager

            mgr = PayPalManager(self.config)
            completadas = mgr.check_pending_payments()
            self.finished.emit(completadas)
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────── TAB PRINCIPAL ───────────────────────────────

class ControlCenterTab(QWidget):
    """Centro de Mando con Red Telegram / Generador IA / Caja."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.db = Database()
        self._bot_worker = None
        self._ai_worker = None
        self._paypal_worker = None
        self._editing_bot_id = None
        self._editing_chat_id = None
        self._editing_chat_bot_id = None
        self._init_ui()
        self._load_data()

    # ── UI ──

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("🎛️ Centro de Mando")
        header.setFont(QFont("", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_red_tab(), "📡 Red Telegram")
        tabs.addTab(self._build_ai_tab(), "🤖 Generador IA")
        tabs.addTab(self._build_caja_tab(), "💰 Caja")
        layout.addWidget(tabs, 1)

    # ── PESTAÑA 1: RED TELEGRAM ──

    def _build_red_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # -- Bots --
        gb_bots = QGroupBox("Bots")
        fl = QHBoxLayout()
        self.bot_nombre = QLineEdit()
        self.bot_nombre.setPlaceholderText("Ej: Bot Vendedor")
        self.bot_token = QLineEdit()
        self.bot_token.setPlaceholderText("Token de BotFather")
        self.bot_edit_label = QLabel("")
        self.bot_edit_label.setStyleSheet("color: #f57c00; font-weight: bold;")
        self.bot_edit_label.hide()
        self.btn_save_bot = QPushButton("Guardar Bot")
        self.btn_save_bot.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #388e3c; }"
        )
        self.btn_save_bot.clicked.connect(self._guardar_bot)
        self.btn_cancel_bot = QPushButton("Cancelar")
        self.btn_cancel_bot.setStyleSheet(
            "QPushButton { background-color: #6d2e2e; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #8e3838; }"
        )
        self.btn_cancel_bot.clicked.connect(self._cancel_edit_bot)
        self.btn_cancel_bot.hide()
        fl.addWidget(QLabel("Nombre:"))
        fl.addWidget(self.bot_nombre)
        fl.addWidget(QLabel("Token:"))
        fl.addWidget(self.bot_token)
        fl.addWidget(self.bot_edit_label)
        fl.addWidget(self.btn_save_bot)
        fl.addWidget(self.btn_cancel_bot)
        gb_bots.setLayout(fl)
        layout.addWidget(gb_bots)

        # -- Chats --
        gb_chats = QGroupBox("Chats")
        fl2 = QHBoxLayout()
        self.chat_nombre = QLineEdit()
        self.chat_nombre.setPlaceholderText("Ej: Canal Señales")
        self.chat_bot_combo = QComboBox()
        self.chat_tipo = QComboBox()
        self.chat_tipo.addItems(["Canal", "Grupo", "Privado"])
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("-100123456789")
        self.chat_edit_label = QLabel("")
        self.chat_edit_label.setStyleSheet("color: #f57c00; font-weight: bold;")
        self.chat_edit_label.hide()
        self.btn_save_chat = QPushButton("Guardar Chat")
        self.btn_save_chat.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #388e3c; }"
        )
        self.btn_save_chat.clicked.connect(self._guardar_chat)
        self.btn_cancel_chat = QPushButton("Cancelar")
        self.btn_cancel_chat.setStyleSheet(
            "QPushButton { background-color: #6d2e2e; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #8e3838; }"
        )
        self.btn_cancel_chat.clicked.connect(self._cancel_edit_chat)
        self.btn_cancel_chat.hide()
        fl2.addWidget(QLabel("Nombre:"))
        fl2.addWidget(self.chat_nombre)
        fl2.addWidget(QLabel("Bot:"))
        fl2.addWidget(self.chat_bot_combo)
        fl2.addWidget(QLabel("Tipo:"))
        fl2.addWidget(self.chat_tipo)
        fl2.addWidget(QLabel("Chat ID:"))
        fl2.addWidget(self.chat_id_input)
        fl2.addWidget(self.chat_edit_label)
        fl2.addWidget(self.btn_save_chat)
        fl2.addWidget(self.btn_cancel_chat)
        gb_chats.setLayout(fl2)
        layout.addWidget(gb_chats)

        # -- Tabla resumen --
        self.red_table = QTableWidget()
        self.red_table.setColumnCount(7)
        self.red_table.setHorizontalHeaderLabels(["Tipo", "Nombre", "ID / Token", "Activo", "Bot", "", ""])
        h = self.red_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        layout.addWidget(self.red_table)

        # -- Botón INICIAR MOTORES --
        self.engine_status = QLabel("Motores apagados")
        self.engine_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.engine_status)

        self.btn_start = QPushButton("🚀 INICIAR MOTORES")
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-size: 16px; "
            "font-weight: bold; padding: 12px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #388e3c; }"
            "QPushButton:disabled { background-color: #555; }"
        )
        self.btn_start.clicked.connect(self._toggle_engine)
        layout.addWidget(self.btn_start)

        return tab

    # ── PESTAÑA 2: GENERADOR IA ──

    def _build_ai_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Nicho selector
        row = QHBoxLayout()
        row.addWidget(QLabel("Nicho:"))
        self.nicho_combo = QComboBox()
        row.addWidget(self.nicho_combo, 1)
        layout.addLayout(row)

        # Texto generado
        self.ai_output = QTextEdit()
        self.ai_output.setPlaceholderText("El post generado aparecerá aquí…")
        layout.addWidget(self.ai_output, 1)

        # Botón generar
        self.btn_generate = QPushButton("🤖 Generar con IA")
        self.btn_generate.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; font-size: 14px; "
            "font-weight: bold; padding: 10px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #1565c0; }"
            "QPushButton:disabled { background-color: #555; }"
        )
        self.btn_generate.clicked.connect(self._generar_post)
        layout.addWidget(self.btn_generate)

        return tab

    # ── PESTAÑA 3: CAJA ──

    def _build_caja_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        self.ventas_table = QTableWidget()
        self.ventas_table.setColumnCount(7)
        self.ventas_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "eBook", "Método", "Payment ID", "Monto", "Estado"
        ])
        h = self.ventas_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.ventas_table, 1)

        row = QHBoxLayout()
        self.btn_verificar = QPushButton("🔄 Verificar Pagos PayPal")
        self.btn_verificar.setStyleSheet(
            "QPushButton { background-color: #f57c00; color: white; font-size: 14px; "
            "font-weight: bold; padding: 10px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #e65100; }"
            "QPushButton:disabled { background-color: #555; }"
        )
        self.btn_verificar.clicked.connect(self._verificar_pagos)
        row.addWidget(self.btn_verificar)

        self.btn_refresh_ventas = QPushButton("📋 Refrescar tabla")
        self.btn_refresh_ventas.clicked.connect(self._cargar_ventas)
        row.addWidget(self.btn_refresh_ventas)
        layout.addLayout(row)

        self.paypal_status = QLabel("")
        self.paypal_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.paypal_status)

        return tab

    # ── CRUD BOTS / CHATS ──

    def _guardar_bot(self):
        nombre = self.bot_nombre.text().strip()
        token = self.bot_token.text().strip()
        if not nombre or not token:
            QMessageBox.warning(self, "Campos incompletos", "Nombre y Token son obligatorios.")
            return
        session = self.db.get_session()
        try:
            if self._editing_bot_id is not None:
                bot = session.query(Bot).get(self._editing_bot_id)
                if bot:
                    bot.nombre = nombre
                    bot.token_api = token
                self._editing_bot_id = None
            else:
                session.add(Bot(nombre=nombre, token_api=token, activo=True))
            session.commit()
            self._reset_bot_form()
            self._refrescar_combos()
            self._cargar_resumen()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            session.close()

    def _guardar_chat(self):
        nombre = self.chat_nombre.text().strip()
        chat_id = self.chat_id_input.text().strip()
        bot_id = self.chat_bot_combo.currentData()
        tipo = self.chat_tipo.currentText()
        if not nombre or not chat_id or bot_id is None:
            QMessageBox.warning(self, "Campos incompletos", "Nombre, Chat ID y Bot son obligatorios.")
            return
        session = self.db.get_session()
        try:
            if self._editing_chat_id is not None:
                chat = session.query(Chat).get(self._editing_chat_id)
                if chat:
                    chat.nombre = nombre
                    chat.chat_id = chat_id
                    chat.bot_id = bot_id
                    chat.tipo = tipo
                self._editing_chat_id = None
            else:
                session.add(Chat(nombre=nombre, chat_id=chat_id, tipo=tipo, bot_id=bot_id, activo=True))
            session.commit()
            self._reset_chat_form()
            self._cargar_resumen()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            session.close()

    def _refrescar_combos(self):
        session = self.db.get_session()
        try:
            bots = session.query(Bot).all()
            self.chat_bot_combo.clear()
            for bot in bots:
                self.chat_bot_combo.addItem(f"{bot.nombre} (id={bot.id})", bot.id)
        finally:
            session.close()

    def _cargar_resumen(self):
        self.red_table.setRowCount(0)
        session = self.db.get_session()
        try:
            for bot in session.query(Bot).all():
                row = self.red_table.rowCount()
                self.red_table.insertRow(row)
                self.red_table.setItem(row, 0, QTableWidgetItem("🤖 Bot"))
                self.red_table.setItem(row, 1, QTableWidgetItem(bot.nombre))
                self.red_table.setItem(row, 2, QTableWidgetItem(bot.token_api[:20] + "…"))
                self.red_table.setItem(row, 3, QTableWidgetItem("✅" if bot.activo else "❌"))
                self.red_table.setItem(row, 4, QTableWidgetItem("—"))
                self._add_action_buttons(row, "bot", bot.id)

            for chat in session.query(Chat).all():
                row = self.red_table.rowCount()
                self.red_table.insertRow(row)
                self.red_table.setItem(row, 0, QTableWidgetItem(f"💬 {chat.tipo}"))
                self.red_table.setItem(row, 1, QTableWidgetItem(chat.nombre or ""))
                self.red_table.setItem(row, 2, QTableWidgetItem(chat.chat_id))
                self.red_table.setItem(row, 3, QTableWidgetItem("✅" if chat.activo else "❌"))
                self.red_table.setItem(row, 4, QTableWidgetItem(str(chat.bot_id)))
                self._add_action_buttons(row, "chat", chat.id)
        finally:
            session.close()

    def _add_action_buttons(self, row, kind, obj_id):
        btn_edit = QPushButton("Editar")
        btn_edit.setFixedWidth(70)
        btn_edit.setStyleSheet(
            "QPushButton { background-color: #2a6d9c; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 10px; }"
            "QPushButton:hover { background-color: #3a7dac; }"
        )
        btn_edit.clicked.connect(lambda checked, k=kind, i=obj_id: self._editar(k, i))
        self.red_table.setCellWidget(row, 5, btn_edit)

        btn_del = QPushButton("Eliminar")
        btn_del.setFixedWidth(70)
        btn_del.setStyleSheet(
            "QPushButton { background-color: #9c2a2a; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 10px; }"
            "QPushButton:hover { background-color: #ac3a3a; }"
        )
        btn_del.clicked.connect(lambda checked, k=kind, i=obj_id: self._eliminar(k, i))
        self.red_table.setCellWidget(row, 6, btn_del)

    # ── EDITAR / ELIMINAR ──

    def _editar(self, kind, obj_id):
        session = self.db.get_session()
        try:
            if kind == "bot":
                bot = session.query(Bot).get(obj_id)
                if not bot:
                    return
                self.bot_nombre.setText(bot.nombre)
                self.bot_token.setText(bot.token_api)
                self._editing_bot_id = bot.id
                self.bot_edit_label.setText(f"Editando Bot #{bot.id}")
                self.bot_edit_label.show()
                self.btn_save_bot.setText("Actualizar Bot")
                self.btn_cancel_bot.show()
            else:
                chat = session.query(Chat).get(obj_id)
                if not chat:
                    return
                self.chat_nombre.setText(chat.nombre or "")
                self.chat_id_input.setText(chat.chat_id)
                idx = self.chat_tipo.findText(chat.tipo, Qt.MatchFixedString)
                if idx >= 0:
                    self.chat_tipo.setCurrentIndex(idx)
                bot_idx = self.chat_bot_combo.findData(chat.bot_id)
                if bot_idx >= 0:
                    self.chat_bot_combo.setCurrentIndex(bot_idx)
                self._editing_chat_id = chat.id
                self.chat_edit_label.setText(f"Editando Chat #{chat.id}")
                self.chat_edit_label.show()
                self.btn_save_chat.setText("Actualizar Chat")
                self.btn_cancel_chat.show()
        finally:
            session.close()

    def _eliminar(self, kind, obj_id):
        label = "bot" if kind == "bot" else "chat"
        reply = QMessageBox.question(
            self, f"Eliminar {label}",
            f"¿Estás seguro de eliminar este {label}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        session = self.db.get_session()
        try:
            if kind == "bot":
                session.query(Bot).filter(Bot.id == obj_id).delete()
            else:
                session.query(Chat).filter(Chat.id == obj_id).delete()
            session.commit()
            self._refrescar_combos()
            self._cargar_resumen()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            session.close()

    def _reset_bot_form(self):
        self.bot_nombre.clear()
        self.bot_token.clear()
        self._editing_bot_id = None
        self.bot_edit_label.hide()
        self.btn_save_bot.setText("Guardar Bot")
        self.btn_cancel_bot.hide()

    def _reset_chat_form(self):
        self.chat_nombre.clear()
        self.chat_id_input.clear()
        self._editing_chat_id = None
        self.chat_edit_label.hide()
        self.btn_save_chat.setText("Guardar Chat")
        self.btn_cancel_chat.hide()

    def _cancel_edit_bot(self):
        self._reset_bot_form()

    def _cancel_edit_chat(self):
        self._reset_chat_form()

    # ── INICIAR / DETENER MOTORES ──

    def _set_engine_stopped_state(self):
        self._bot_worker = None
        self.btn_start.setText("🚀 INICIAR MOTORES")
        self.engine_status.setText("Motores apagados")

    def _toggle_engine(self):
        if self._bot_worker and self._bot_worker.isRunning():
            self._bot_worker.stop_engine()
            self.btn_start.setEnabled(False)
            self.btn_start.setText("Deteniendo...")
            self.engine_status.setText("Apagando motores...")
            QTimer.singleShot(100, self._check_engine_stopped)
            return

        self._bot_worker = BotEngineWorker(self.config)
        self._bot_worker.status.connect(self.engine_status.setText)
        self._bot_worker.error.connect(lambda msg: self.engine_status.setText(f"Error: {msg}"))
        self._bot_worker.finished.connect(self._set_engine_stopped_state)
        self.btn_start.setText("DETENER MOTORES")
        self.engine_status.setText("Arrancando...")
        self._bot_worker.start()

    def _check_engine_stopped(self):
        if self._bot_worker and self._bot_worker.isRunning():
            QTimer.singleShot(100, self._check_engine_stopped)
            return
        self.btn_start.setEnabled(True)
        self._set_engine_stopped_state()

    # ── GENERAR POST ──

    def _generar_post(self):
        nicho_id = self.nicho_combo.currentData()
        if nicho_id is None:
            QMessageBox.warning(self, "Sin nicho", "No hay nichos en la DB.")
            return

        self.btn_generate.setEnabled(False)
        self.ai_output.setPlainText("Generando…")
        self._ai_worker = AiGenerateWorker(nicho_id, self.config)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

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
        self._cleanup_worker('_ai_worker')
        self._cleanup_worker('_paypal_worker')
        event.accept()

    def _on_ai_finished(self, text):
        self.ai_output.setPlainText(text)
        self.btn_generate.setEnabled(True)
        self._cleanup_worker('_ai_worker')

    def _on_ai_error(self, msg):
        self.ai_output.setPlainText(f"[Error] {msg}")
        self.btn_generate.setEnabled(True)
        self._cleanup_worker('_ai_worker')

    # ── CAJA / PAYPAL ──

    def _cargar_ventas(self):
        self.ventas_table.setRowCount(0)
        session = self.db.get_session()
        try:
            for venta in session.query(Venta).order_by(Venta.id.desc()).all():
                row = self.ventas_table.rowCount()
                self.ventas_table.insertRow(row)
                self.ventas_table.setItem(row, 0, QTableWidgetItem(str(venta.id)))
                self.ventas_table.setItem(row, 1, QTableWidgetItem(str(venta.usuario_id)))
                self.ventas_table.setItem(row, 2, QTableWidgetItem(str(venta.ebook_id)))
                self.ventas_table.setItem(row, 3, QTableWidgetItem(venta.metodo_pago))
                pid = venta.payment_id or ""
                self.ventas_table.setItem(row, 4, QTableWidgetItem(pid[:30] + "…" if len(pid) > 30 else pid))
                self.ventas_table.setItem(row, 5, QTableWidgetItem(f"${venta.monto:.2f}"))
                self.ventas_table.setItem(row, 6, QTableWidgetItem(venta.estado))
        finally:
            session.close()

    def _verificar_pagos(self):
        self.btn_verificar.setEnabled(False)
        self.paypal_status.setText("🔄 Verificando pagos PayPal…")
        self._paypal_worker = PayPalCheckWorker(self.config)
        self._paypal_worker.finished.connect(self._on_paypal_finished)
        self._paypal_worker.error.connect(self._on_paypal_error)
        self._paypal_worker.start()

    def _on_paypal_finished(self, completadas):
        self.btn_verificar.setEnabled(True)
        self._cleanup_worker('_paypal_worker')
        if completadas:
            self.paypal_status.setText(f"✅ {len(completadas)} venta(s) completada(s).")
            QMessageBox.information(
                self, "Pagos detectados",
                f"{len(completadas)} venta(s) pasaron a Pagado.\n"
                "Refrescá la tabla para ver los cambios.",
            )
        else:
            self.paypal_status.setText("ℹ Ninguna venta nueva pagada.")
        self._cargar_ventas()

    def _on_paypal_error(self, msg):
        self.btn_verificar.setEnabled(True)
        self._cleanup_worker('_paypal_worker')
        self.paypal_status.setText(f"❌ Error: {msg}")

    # ── CARGA INICIAL ──

    def _load_data(self):
        self._refrescar_combos()
        self._cargar_resumen()
        self._cargar_ventas()
        session = self.db.get_session()
        try:
            for n in session.query(Nicho).all():
                self.nicho_combo.addItem(f"{n.nombre} (id={n.id})", n.id)
        finally:
            session.close()


ControlCenter = ControlCenterTab
