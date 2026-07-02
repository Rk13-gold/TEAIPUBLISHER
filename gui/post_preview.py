import re

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTextEdit, QScrollArea, QFrame, QSizePolicy
from PySide6.QtGui import QPixmap, QTextCursor, QTextImageFormat, QImage, QTextDocument
from PySide6.QtCore import Qt, QUrl

from gui.emoji_renderer import render_emoji

# Regex to match emoji characters (most Unicode emoji ranges)
_EMOJI_RE = re.compile(
    '[\U0001F000-\U0001FFFF\U00002700-\U000027BF\U00002600-\U000026FF'
    '\U00002B00-\U00002BFF\U00002300-\U000023FF\U0000FE00-\U0000FE0F'
    '\U00002000-\U0000206F\U00002100-\U0000214F\u00A9\u00AE\u203C\u2049'
    '\u2122\u2139\u2194-\u2199\u21A9\u21AA\u231A\u231B\u2328\u23CF'
    '\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE'
    '\u2600-\u27BF\u2934\u2935\u2B05\u2B06\u2B07\u2B1B\u2B1C\u2B50'
    '\u2B55\u3030\u303D\u3297\u3299]+'
)

class PostPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(350)
        self.setStyleSheet("""
            QWidget#PreviewFrame {
                background: #23272b;
                border-radius: 5px;
                border: 1px solid #444;
            }
            QLabel#ImageLabel {
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                background: #181c20;
            }
            QTextEdit#TextPreview {
                background: #23272b;
                color: #e0e0e0;
                border: none;
                font-size: 15px;
                padding: 8px 12px 8px 12px;
            }
            QFrame#ButtonBox {
                background: #23272b;
                border-top: 1px solid #444;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                padding: 8px 8px 8px 8px;
            }
            QPushButton {
                background: #0078d7;
                color: #fff;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background: #005fa3;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.frame = QFrame()
        self.frame.setObjectName("PreviewFrame")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Imagen
        self.image_label = QLabel()
        self.image_label.setObjectName("ImageLabel")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(120)
        self.image_label.setMaximumHeight(220)
        self.image_label.setScaledContents(True)
        frame_layout.addWidget(self.image_label)

        # Scroll para texto y botones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        # Texto preformateado (igual que edición)
        self.text_preview = QTextEdit()
        self.text_preview.setObjectName("TextPreview")
        self.text_preview.setReadOnly(True)
        self.text_preview.setLineWrapMode(QTextEdit.WidgetWidth)
        scroll_layout.addWidget(self.text_preview)

        # Caja de botones
        self.button_box = QFrame()
        self.button_box.setObjectName("ButtonBox")
        self.button_box_layout = QVBoxLayout(self.button_box)
        self.button_box_layout.setContentsMargins(0, 0, 0, 0)
        self.button_box_layout.setSpacing(4)
        scroll_layout.addWidget(self.button_box)

        scroll.setWidget(scroll_widget)
        frame_layout.addWidget(scroll)
        main_layout.addWidget(self.frame)

        self.set_image(None)
        self.set_text("")
        self.set_buttons([], "row")

    def set_image(self, image_path):
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                w = self.width() if self.width() > 0 else 350
                pixmap = pixmap.scaled(w, 220, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.image_label.setPixmap(pixmap)
                self.image_label.setVisible(True)
                return
        self.image_label.clear()
        self.image_label.setVisible(False)

    def set_text(self, text):
        doc = self.text_preview.document()
        doc.clear()
        cursor = QTextCursor(doc)
        emoji_size = 13
        pos = 0
        idx = 0
        for m in _EMOJI_RE.finditer(text):
            if m.start() > pos:
                cursor.insertText(text[pos:m.start()])
            emoji = m.group()
            pix = render_emoji(emoji, emoji_size)
            if pix and not pix.isNull():
                pix = pix.scaled(emoji_size, emoji_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img = pix.toImage()
                name = f'pv_{idx}'
                doc.addResource(QTextDocument.ImageResource, QUrl(name), img)
                fmt = QTextImageFormat()
                fmt.setName(name)
                fmt.setWidth(emoji_size)
                fmt.setHeight(emoji_size)
                cursor.insertImage(fmt)
            else:
                cursor.insertText(emoji)
            pos = m.end()
            idx += 1
        if pos < len(text):
            cursor.insertText(text[pos:])

    def set_html(self, html):
        # Replace emoji characters in HTML with <img> placeholders
        emoji_size = 13
        parts = []
        idx = 0
        pos = 0
        for m in _EMOJI_RE.finditer(html):
            if m.start() > pos:
                parts.append(html[pos:m.start()])
            parts.append(f'<img src="emoji_{idx}" width="{emoji_size}" height="{emoji_size}">')
            pos = m.end()
            idx += 1
        if pos < len(html):
            parts.append(html[pos:])
        modified_html = ''.join(parts)
        doc = self.text_preview.document()
        doc.setHtml(modified_html)
        # Add image resources for each placeholder
        idx = 0
        for m in _EMOJI_RE.finditer(html):
            emoji = m.group()
            pix = render_emoji(emoji, emoji_size)
            if pix and not pix.isNull():
                pix = pix.scaled(emoji_size, emoji_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img = pix.toImage()
                doc.addResource(QTextDocument.ImageResource, QUrl(f'emoji_{idx}'), img)
            idx += 1

    def set_buttons(self, buttons, layout_type="row"):
        # Limpia botones previos
        for i in reversed(range(self.button_box_layout.count())):
            item = self.button_box_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
        # Añade filas de botones ajustando el ancho
        for row in buttons:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(0, 0, 0, 0)
            # --- Para que cada botón ocupe el mismo ancho, calcula el stretch ---
            num_btns = len(row)
            for btn in row:
                b = QPushButton(btn["text"])
                b.setCursor(Qt.PointingHandCursor)
                b.setEnabled(False)
                b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                b.setMinimumHeight(40)
                row_layout.addWidget(b, stretch=1)
            # --- Si hay menos de 1 botón, igual ocupa todo el ancho ---
            if num_btns == 1:
                row_layout.setStretch(0, 1)
            self.button_box_layout.addWidget(row_widget)
        # No agregues addStretch aquí, así el cajón se ajusta a la cantidad de filas

    def resizeEvent(self, event):
        if self.image_label.pixmap():
            self.set_image(self.image_label.pixmap())
        super().resizeEvent(event)