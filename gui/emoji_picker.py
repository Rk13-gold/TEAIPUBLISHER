from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QScrollArea,
    QWidget, QTabWidget, QLabel, QHBoxLayout, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

from gui.emoji_renderer import render_emoji

DARK_BG = "#000000"
DARK_SURFACE = "#0a0a0a"
DARK_HOVER = "#1a1a2e"
DARK_ACTIVE = "#2a2a4e"
ACCENT = "#7c5cfc"
ACCENT_HOVER = "#9178ff"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#888888"
BORDER = "#333333"
SEARCH_BG = "#111111"


EMOJIS = {
    "Caritas": [
        "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇","🥰","😍","🤩","😘","😗",
        "☺️","😚","😙","🥲","😋","😛","😜","🤪","😝","🤑","🤗","🤭","🤫","🤔","🤐","🤨","😐","😑",
        "😶","😶‍🌫️","😏","😒","🙄","😬","😮‍💨","🤥","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤮",
        "🤧","🥵","🥶","🥴","😵","😵‍💫","🤯","🤠","🥳","🥸","😎","🤓","🧐","😕","😟","🙁","☹️","😮",
        "😯","😲","😳","🥺","😦","😧","😨","😰","😥","😢","😭","😱","😖","😣","😞","😓","😩","😫",
        "🥱","😤","😡","😠","🤬","😈","👿","💀","☠️","💩","🤡","👻","👽","🤖"
    ],
    "Gestos": [
        "👋","🤚","🖐️","✋","🖖","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙","👈","👉","👆","🖕","👇",
        "☝️","👍","👎","👊","✊","🤛","🤜","👏","🙌","👐","🤲","🤝","🙏","✍️","💅","🤳","💪"
    ],
    "Animales": [
        "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🙈","🙉","🙊",
        "🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅","🦉","🦇","🐺","🐗","🐴","🦄"
    ],
    "Comida": [
        "🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🍒","🍑","🥭","🍍","🥥","🥝","🍅","🍆",
        "🥑","🥦","🥬","🥒","🌶️","🌽","🥕","🥔","🍠","🥐","🥖","🍞","🥨","🥯","🥞","🧇",
        "🥓","🥩","🍗","🍖","🌭","🍔","🍟","🍕","🥪","🥙","🌮","🌯","🥗","🥘","🍝","🍜",
        "🍲","🍛","🍣","🍱","🥟","🍤","🍙","🍚","🍘","🍥","🥠","🍢","🍡","🍧","🍨","🍦",
        "🥧","🧁","🍰","🎂","🍮","🍭","🍬","🍫","🍿","🍩","🍪"
    ],
    "Deportes": [
        "⚽","🏀","🏈","⚾","🥎","🎾","🏐","🏉","🎱","🏓","🏸","🏑","🏒","🥍","🏏","🥅","⛳","🏹",
        "🎣","🥊","🥋","🎽","🛹","🛼","⛸️","🥌","🎿","⛷️","🏂","🏋️","🤼","🤸","⛹️","🤺","🤾",
        "🏌️","🧘","🏄","🏊","🤽","🚣","🧗","🚵","🚴","🏆","🥇","🥈","🥉","🏅","🎖️"
    ],
    "Objetos": [
        "⌚","📱","💻","⌨️","🖥️","🖨️","🖱️","🕹️","💽","💾","💿","📷","📸","📹","🎥","📞","☎️",
        "📺","📻","🎙️","🎚️","🎛️","⏰","🕰️","⌛","⏳","📡","🔋","🔌","💡","🔦","🕯️","💸","💵",
        "💴","💶","💷","💰","💳","💎","🧰","🔧","🔨","🛠️","⛏️","🔩","⚙️","🔫","💣","🔪","🗡️",
        "🛡️","🚬","⚰️","🏺","🔮","📿","💈","🔭","🔬","🧬","🧫","🧪","🌡️","🧹","🧺","🧾","📃",
        "📄","📋","📊","📈","📉","📚","📖","📗","📘","📙","📓","📔","📒","📕","📰","📑","🔖",
        "🏷️","💰","🎁","🎀","🎊","🎉","🎈","🎄","🎃","🧧","🎎","🎏","🎐","🧨","✨","🎆","🎇"
    ],
    "Simbolos": [
        "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","❣️","💕","💞","💓","💗","💖","💘",
        "💝","💟","☮️","✝️","☪️","🕉️","☸️","✡️","🔯","🕎","☯️","☦️","🛐","♈","♉","♊",
        "♋","♌","♍","♎","♏","♐","♑","♒","♓","🆔","⚛️","☢️","☣️","📴","📳","🈶","🈚",
        "🈸","🈺","🈷️","✴️","🆚","💮","🉐","㊙️","㊗️","🈴","🈵","🈹","🈲","🅰️","🅱️","🆎",
        "🆑","🅾️","🆘","❌","⭕","🛑","⛔","📛","🚫","💯","💢","♨️","🚷","🚯","🚳","🚱","🔞",
        "📵","🚭","❗","❕","❓","❔","‼️","⁉️","🔅","🔆","⚠️","🚸","🔱","⚜️","🔰","♻️",
        "✅","🈯","💹","❇️","✳️","❎","🌐","💠","Ⓜ️","🌀","💤","🏧","🚾","♿","🅿️","🈳","🈂️",
        "🛂","🛃","🛄","🛅","🚹","🚺","🚼","⚧️","🚻","🚮","🎦","📶","🈁","🔣","ℹ️","🔤","🔡",
        "🔠","🆖","🆗","🆙","🆒","🆕","🆓","0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣",
        "9️⃣","🔟","🔢","#️⃣","*️⃣","⏏️","▶️","⏸️","⏯️","⏹️","⏺️","⏭️","⏮️","⏩","⏪","⏫",
        "⏬","◀️","🔼","🔽","➡️","⬅️","⬆️","⬇️","↗️","↘️","↙️","↖️","↕️","↔️","↪️","↩️",
        "⤴️","⤵️","🔀","🔁","🔂","🔄","🔃","🎵","🎶","➕","➖","➗","✖️","♾️","💲","💱",
        "™️","©️","®️","〰️","➰","➿","🔚","🔙","🔛","🔝","🔜","✔️","☑️","🔘","🔴","🟠",
        "🟡","🟢","🔵","🟣","⚫","⚪","🟤","🔺","🔻","🔸","🔹","🔶","🔷","🔳","🔲","▪️",
        "▫️","◾","◽","◼️","◻️","🟥","🟧","🟨","🟩","🟦","🟪","⬛","⬜","🟫","🔈","🔇",
        "🔉","🔊","🔔","🔕","📣","📢","💬","💭","🗯️","♠️","♣️","♥️","♦️","🃏","🎴",
        "🀄"
    ],
}


ANIMATED_EMOJIS = {
    "Premium": [
        "🎉","🎊","✨","🌟","💫","⭐","🔥","💥","💯","🎯","🚀","💎","👑","🏆","🥇","🔮",
        "🎭","🎪","🎨","🎵","🎶","🎤","🎸","🎹","🥳","😍","🤩","😎",
    ],
    "Efectos": [
        "🎆","🎇","✨","💫","🌟","⭐","💥","🔥","💯","🎊","🎉","🎈","🎁","🎀","🎂","🧨",
        "💎","👑","🏆","🥇","🎖️","🏅","🔮","💰","💸","💵","🎯","🚀","⚡","🌪️","🌈","🦄",
    ],
    "Virales": [
        "🔥","💯","🚀","💥","⚡","✨","🌟","💫","⭐","🎉","🎊","💎","👑","🏆","🥇","🎯",
        "💖","😍","🤩","😎","🥳","🤯","🤗","😂","🤣","💪","👌","🙌","👏","🔥","💯","🚀",
    ],
    "Celebracion": [
        "🎉","🎊","🥳","🍾","🥂","🍻","🍺","🎂","🧁","🍰","🎈","🎁","🎀","🎪","🎭","🎨",
        "🎵","🎶","🎤","🎸","🎹","🎺","🎻","🥁","💃","🕺","🤩","😍","😂","🤣","🥰","😘",
    ],
    "Amor": [
        "❤️","💕","💞","💓","💗","💖","💘","💝","♥️","💋","😍","🥰","😘","🤗","🥺",
        "😭","😢","🥹","😊","☺️","🙂","😌","😉","😚","😙","🤩","🥳","🔥","💯","✨","🌟",
    ]
}

EMOJIS.update(ANIMATED_EMOJIS)


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
        self.setToolTip(emoji)

    @property
    def emoji(self) -> str:
        return self._emoji


class EmojiPicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar emoji")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)
        self.selected_emoji = None
        self._queue: list[tuple[str, str]] = []
        self._buttons: dict[str, QPushButton] = {}
        self._grids: dict[str, QGridLayout] = {}

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_BG};
                border-radius: 12px;
            }}
            QLineEdit {{
                background-color: {SEARCH_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
            QTabWidget::pane {{
                background-color: {DARK_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                padding: 6px 12px;
                margin: 2px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {DARK_HOVER};
                color: {TEXT_PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: rgba(45, 47, 82, 0.5);
            }}
            QScrollBar:vertical {{
                background: {DARK_SURFACE};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ACCENT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {DARK_HOVER};
                border: 1px solid {BORDER};
            }}
            QPushButton:pressed {{
                background-color: {ACCENT};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("Emojis")
        header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold; padding: 0; background: transparent;")
        main_layout.addWidget(header)

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar emoji...")
        main_layout.addWidget(self.search_edit)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        for cat, emojis in EMOJIS.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet(f"background-color: {DARK_SURFACE}; border: none;")
            widget = QWidget()
            widget.setStyleSheet(f"background-color: {DARK_SURFACE};")
            grid = QGridLayout(widget)
            grid.setSpacing(4)
            grid.setContentsMargins(6, 6, 6, 6)
            scroll.setWidget(widget)
            self._grids[cat] = grid
            self.tabs.addTab(scroll, cat)
            self._queue.extend((cat, e) for e in emojis)

        self.search_edit.textChanged.connect(self.filter_emojis)

        self.tabs.setCurrentIndex(0)
        QTimer.singleShot(0, self._process_queue)

    def _process_queue(self):
        processed = 0
        while self._queue and processed < 30:
            cat, emoji = self._queue.pop(0)
            btn = _EmojiButton(emoji, 26)
            btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
            grid = self._grids[cat]
            count = grid.count()
            grid.addWidget(btn, count // 12, count % 12)
            self._buttons[emoji] = btn
            processed += 1
        if self._queue:
            QTimer.singleShot(10, self._process_queue)

    def filter_emojis(self, text):
        text = text.strip().lower()
        for cat, emojis in EMOJIS.items():
            grid = self._grids[cat]
            for i in reversed(range(grid.count())):
                w = grid.itemAt(i).widget()
                if w:
                    w.setParent(None)
            if text:
                filtered = [e for e in emojis if text in e]
            else:
                filtered = emojis
            for idx, emoji in enumerate(filtered):
                btn = self._buttons.get(emoji)
                if btn is None:
                    btn = _EmojiButton(emoji, 26)
                    btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
                    self._buttons[emoji] = btn
                grid.addWidget(btn, idx // 12, idx % 12)

    def select_emoji(self, emoji):
        self.selected_emoji = emoji
        self.accept()
