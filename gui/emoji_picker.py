from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QScrollArea, QWidget, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# --- Lista de emojis por categoría (puedes ampliarla aún más si lo deseas) ---
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
    "Símbolos": [
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

class EmojiPicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar emoji")
        self.setMinimumWidth(480)
        self.selected_emoji = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar emoji...")
        main_layout.addWidget(self.search_edit)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        self.emoji_grids = {}
        self.emoji_widgets = {}

        for cat, emojis in EMOJIS.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            widget = QWidget()
            grid = QGridLayout(widget)
            grid.setSpacing(2)
            grid.setContentsMargins(8, 8, 8, 8)
            scroll.setWidget(widget)
            self.emoji_grids[cat] = grid
            self.emoji_widgets[cat] = widget
            self.tabs.addTab(scroll, cat)
            self.populate_emojis(cat, emojis)

        self.search_edit.textChanged.connect(self.filter_emojis)

    def populate_emojis(self, category, emojis):
        grid = self.emoji_grids[category]
        # Limpiar grid
        for i in reversed(range(grid.count())):
            widget = grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # Agregar emojis
        columns = 14 if category != "Banderas" else 8
        for idx, emoji in enumerate(emojis):
            btn = QPushButton(emoji)
            btn.setFixedSize(32, 32)
            btn.setFont(QFont("Segoe UI Emoji", 18))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("class", "emoji-btn")  # Para que el QSS global no afecte el color
            btn.setStyleSheet("color: none; background: none; border: none;")  # Refuerzo para evitar herencia
            btn.clicked.connect(lambda _, e=emoji: self.select_emoji(e))
            grid.addWidget(btn, idx // columns, idx % columns)

    def filter_emojis(self, text):
        text = text.strip().lower()
        for cat, emojis in EMOJIS.items():
            if not text:
                filtered = emojis
            else:
                filtered = [e for e in emojis if text in e]
            self.populate_emojis(cat, filtered)

    def select_emoji(self, emoji):
        self.selected_emoji = emoji
        self.accept()