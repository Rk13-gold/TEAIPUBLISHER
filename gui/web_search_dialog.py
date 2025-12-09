from __future__ import annotations
from typing import List, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QTextEdit, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from ai_integration.web_search import search as web_search, can_search


class WebSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar en web")
        self.setMinimumWidth(700)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Escribe la consulta (ej: 'cómo monetizar un canal de Telegram')")
        top.addWidget(self.query_input)
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.perform_search)
        top.addWidget(self.search_btn)
        layout.addLayout(top)

        body = QHBoxLayout()
        self.results_list = QListWidget()
        self.results_list.setMaximumWidth(380)
        self.results_list.itemClicked.connect(self.on_result_selected)
        body.addWidget(self.results_list)

        right = QVBoxLayout()
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        right.addWidget(self.preview)

        actions = QHBoxLayout()
        self.insert_in_instructions = QPushButton("Insertar en instrucciones")
        self.insert_in_instructions.clicked.connect(lambda: self._insert_selected('instructions'))
        actions.addWidget(self.insert_in_instructions)
        self.insert_in_content = QPushButton("Insertar en contenido")
        self.insert_in_content.clicked.connect(lambda: self._insert_selected('content'))
        actions.addWidget(self.insert_in_content)
        right.addLayout(actions)

        body.addLayout(right)
        layout.addLayout(body)

        self._results: List[Dict[str, str]] = []

    def perform_search(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Consulta vacía", "Escribe una consulta para buscar")
            return
        if not can_search():
            QMessageBox.critical(self, "Dependencia faltante", "Para usar la búsqueda web instala los paquetes: duckduckgo-search o ddgs.\nEjecuta: pip install -r requirements.txt")
            return
        self.results_list.clear()
        self.preview.clear()
        self._results = web_search(query, max_results=10)
        if not self._results:
            QMessageBox.information(self, "Sin resultados", "No se encontraron resultados.")
            return
        for r in self._results:
            title = r.get('title') or r.get('url') or 'Sin título'
            snippet = r.get('snippet') or ''
            self.results_list.addItem(f"{title}\n{snippet[:120]}")

    def on_result_selected(self, item):
        idx = self.results_list.row(item)
        if 0 <= idx < len(self._results):
            r = self._results[idx]
            text = f"{r.get('title')}\n\n{r.get('snippet')}\n\n{r.get('url')}"
            self.preview.setPlainText(text)

    def _insert_selected(self, where: str):
        # where: 'instructions' or 'content'
        current = self.results_list.currentRow()
        if current < 0 or current >= len(self._results):
            QMessageBox.warning(self, "Selecciona resultado", "Selecciona un resultado para insertarlo")
            return
        text = self.preview.toPlainText()
        # Deliver back to parent via attribute
        self.selected_text = text
        self.selected_target = where
        self.accept()
