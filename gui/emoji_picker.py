from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QScrollArea,
    QWidget, QTabWidget, QLabel, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from gui.emoji_renderer import render_emoji, prewarm
from gui.emoji_data import EMOJIS, search_emojis, emoji_name, load_recent, add_recent

try:
    from gui import theme
except Exception:  # pragma: no cover - fallback si el módulo falta
    theme = None


class _EmojiButton(QPushButton):
    def __init__(self, emoji: str, size: int, parent=None):
        super().__init__(parent)
        self._emoji = emoji
        self.setFixedSize(44, 44)
        pix = render_emoji(emoji, size)
        if pix and not pix.isNull():
            self.setIcon(QIcon(pix))
            self.setIconSize(pix.size())
        else:
            self.setText(emoji)
            self.setFont(QFont("Noto Color Emoji", 26))
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(emoji_name(emoji))

    @property
    def emoji(self) -> str:
        return self._emoji


class EmojiPicker(QDialog):
    """Selección de emojis con pestaña de Frecuentes y búsqueda por tags.

    API pública preservada: `EmojiPicker(parent)`, `.exec()`, `.selected_emoji`.
    Al seleccionar un emoji se registra en los recientes (persistente).
    """

    CATS = list(EMOJIS.keys())

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar emoji")
        self.setMinimumWidth(540)
        self.setMinimumHeight(440)
        self.selected_emoji = None
        self._queue: list[tuple[str, str]] = []
        self._buttons: dict[str, QPushButton] = {}
        self._grids: dict[str, QGridLayout] = {}
        self._results_tab_index = -1

        c = theme or _DEFAULT_THEME
        self.setStyleSheet(_build_picker_qss(c))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("Emojis")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(header)

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Buscar emoji (ej: fuego, corazon, mover)...")
        main_layout.addWidget(self.search_edit)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        # Pestaña de Frecuentes (primera)
        self._build_frecuentes_tab()

        for cat in self.CATS:
            scroll = self._make_scroll()
            widget = QWidget()
            grid = QGridLayout(widget)
            grid.setSpacing(4)
            grid.setContentsMargins(6, 6, 6, 6)
            scroll.setWidget(widget)
            self._grids[cat] = grid
            self.tabs.addTab(scroll, cat)
            self._queue.extend((cat, e) for e in EMOJIS[cat])

        self.search_edit.textChanged.connect(self.on_search_changed)

        self.tabs.setCurrentIndex(0)
        QTimer.singleShot(0, self._process_queue)

    def _make_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        return scroll

    def _build_frecuentes_tab(self):
        recents = load_recent()
        scroll = self._make_scroll()
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(4)
        grid.setContentsMargins(6, 6, 6, 6)
        scroll.setWidget(widget)
        tab_title = "⭐ Frecuentes" if recents else "Recientes"
        self._grids["__frec__"] = grid
        self.tabs.addTab(scroll, tab_title)
        if recents:
            for idx, emoji in enumerate(recents):
                btn = _EmojiButton(emoji, 26)
                btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
                grid.addWidget(btn, idx // 12, idx % 12)
                self._buttons[emoji] = btn
        else:
            empty = QLabel("Aún no tienes emojis recientes.\nLos emojis que uses aparecerán aquí.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            grid.addWidget(empty, 0, 0, 1, 12)

    def _process_queue(self):
        processed = 0
        while self._queue and processed < 30:
            cat, emoji = self._queue.pop(0)
            if emoji in self._buttons:
                continue
            btn = _EmojiButton(emoji, 26)
            btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
            grid = self._grids[cat]
            count = grid.count()
            grid.addWidget(btn, count // 12, count % 12)
            self._buttons[emoji] = btn
            processed += 1
        if self._queue:
            QTimer.singleShot(10, self._process_queue)

    def on_search_changed(self, text):
        q = text.strip().lower()
        if not q:
            # Quitar la pestaña de resultados si estaba
            if self._results_tab_index >= 0:
                self.tabs.removeTab(self._results_tab_index)
                self._results_tab_index = -1
            self.tabs.setCurrentIndex(0)
            return

        hits = search_emojis(q)[:200]
        if self._results_tab_index < 0:
            self._results_tab_index = 0
            self.tabs.insertTab(0, self._make_scroll(), f"Resultados ({len(hits)})")
        else:
            self.tabs.setTabText(self._results_tab_index, f"Resultados ({len(hits)})")
            # Vaciar grid de resultados previo
            results_scroll = self.tabs.widget(self._results_tab_index)
            results_container = results_scroll.widget()
            results_container.deleteLater()

        scroll = self.tabs.widget(self._results_tab_index)
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(4)
        grid.setContentsMargins(6, 6, 6, 6)
        scroll.setWidget(widget)

        if not hits:
            empty = QLabel("Sin resultados 😕")
            empty.setAlignment(Qt.AlignCenter)
            grid.addWidget(empty, 0, 0, 1, 12)
        else:
            for idx, emoji in enumerate(hits):
                btn = _EmojiButton(emoji, 26)
                btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
                grid.addWidget(btn, idx // 12, idx % 12)
                self._buttons[emoji] = btn
            prewarm_all = [e for e in hits if not self._buttons.get(e)]
            for e in prewarm_all[:50]:
                prewarm(e, 26)

        self.tabs.setCurrentIndex(self._results_tab_index)

    def select_emoji(self, emoji):
        self.selected_emoji = emoji
        add_recent(emoji)
        self.accept()


# --- Fallback de tema si gui.theme no está disponible ---

class _DEFAULT_THEME:
    BG_DEEP = "#000000"
    SURFACE = "#0a0a0a"
    SURFACE_ALT = "#111111"
    SURFACE_RAISED = "#1a1a1a"
    HOVER = "#202030"
    ACTIVE = "#2d2f52"
    ACCENT = "#7c5cfc"
    ACCENT_HOVER = "#9178ff"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#9aa0b0"
    BORDER = "#333333"
    BORDER_STRONG = "#45475a"


def _build_picker_qss(c) -> str:
    return f"""
        QDialog {{
            background-color: {c.BG_DEEP};
            border-radius: 12px;
        }}
        QLabel {{
            color: {c.TEXT_PRIMARY};
            background: transparent;
            padding: 0;
        }}
        QLineEdit {{
            background-color: {c.SURFACE_ALT};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {c.ACCENT};
        }}
        QTabWidget::pane {{
            background-color: {c.SURFACE};
            border: 1px solid {c.BORDER};
            border-radius: 8px;
            padding: 4px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {c.TEXT_SECONDARY};
            padding: 6px 12px;
            margin: 2px;
            border-radius: 6px;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{
            background-color: {c.HOVER};
            color: {c.TEXT_PRIMARY};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: rgba(45, 47, 82, 0.5);
        }}
        QScrollBar:vertical {{
            background: {c.SURFACE};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {c.BORDER};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QPushButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            color: {c.TEXT_PRIMARY};
        }}
        QPushButton:hover {{
            background-color: {c.HOVER};
            border: 1px solid {c.BORDER};
        }}
        QPushButton:pressed {{
            background-color: {c.ACCENT};
        }}
    """