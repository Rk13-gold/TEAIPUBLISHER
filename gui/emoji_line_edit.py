import re

from PySide6.QtWidgets import QTextEdit, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QKeyEvent

from gui.emoji_text_helper import insert_emoji_textedit, emoji_document_to_plaintext

_EMOJI_RE = re.compile(
    '[\U0001F000-\U0001FFFF\U00002700-\U000027BF\U00002600-\U000026FF'
    '\U00002B00-\U00002BFF\U00002300-\U000023FF\U0000FE00-\U0000FE0F'
    '\U00002000-\U0000206F\U00002100-\U0000214F\u00A9\u00AE\u203C\u2049'
    '\u2122\u2139\u2194-\u2199\u21A9\u21AA\u231A\u231B\u2328\u23CF'
    '\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE'
    '\u2600-\u27BF\u2934\u2935\u2B05\u2B06\u2B07\u2B1B\u2B1C\u2B50'
    '\u2B55\u3030\u303D\u3297\u3299]+'
)


class EmojiLineEdit(QTextEdit):
    """QTextEdit that looks and behaves like a single-line edit with emoji support."""

    textChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #333;
                border-radius: 4px;
                padding: 2px 6px;
                background: transparent;
                color: #fff;
                selection-background-color: #7c5cfc;
            }
            QTextEdit:focus {
                border: 1px solid #7c5cfc;
            }
        """)
        self.document().contentsChanged.connect(self._emit_text_changed)
        self._suppress = False
        self._adjust_height()

    def _emit_text_changed(self):
        if not self._suppress:
            self.textChanged.emit()

    def _adjust_height(self):
        fm = QFontMetrics(self.font())
        self.setFixedHeight(max(fm.height() + 8, 28))

    # --- QLineEdit-compatible API ---

    def text(self) -> str:
        return emoji_document_to_plaintext(self.document())

    def setText(self, text: str):
        self._suppress = True
        self.setPlainText(text)
        self._suppress = False
        self.textChanged.emit()

    def cursorPosition(self) -> int:
        return self.textCursor().position()

    def setCursorPosition(self, pos: int):
        c = self.textCursor()
        c.setPosition(pos)
        self.setTextCursor(c)

    # --- Single-line behavior ---

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
            return
        super().keyPressEvent(event)
