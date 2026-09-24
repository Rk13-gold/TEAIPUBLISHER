from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QGroupBox, QScrollArea, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont, QIcon
from gui.emoji_picker import EmojiPicker
from gui.emoji_renderer import render_emoji
from gui import theme

class ButtonConfigDialog(QDialog):
    def __init__(self, parent=None, buttons=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar botones de Telegram")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.buttons = buttons if buttons else [[]]  # Lista de filas, cada fila es lista de dicts

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # Scroll para muchas filas
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll, 1)

        # --- Fila de botones: Agregar fila + Emoji ---
        row_btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("Agregar otra fila")
        add_row_btn.clicked.connect(self.add_row)
        row_btn_layout.addWidget(add_row_btn, 0, Qt.AlignLeft)

        # Botón de emoji para insertar en el texto de los botones
        self.emoji_btn = QPushButton()
        self.emoji_btn.setFixedSize(38, 38)
        _pix = render_emoji("😊", 24)
        if _pix and not _pix.isNull():
            self.emoji_btn.setIcon(QIcon(_pix))
            self.emoji_btn.setIconSize(_pix.size())
        else:
            self.emoji_btn.setText(":)")
        self.emoji_btn.setToolTip("Insertar emoji en el campo de texto activo")
        self.emoji_btn.clicked.connect(self.insert_emoji_to_active)
        self.emoji_btn.setStyleSheet(theme.emoji_button_qss())
        row_btn_layout.addWidget(self.emoji_btn, 0, Qt.AlignLeft)

        row_btn_layout.addStretch(1)
        main_layout.addLayout(row_btn_layout)

        # Botones OK/Cancel
        btns = QHBoxLayout()
        ok_btn = QPushButton("Aceptar")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        main_layout.addLayout(btns)

        self.row_widgets = []
        self.active_text_field = None  # Para saber dónde insertar el emoji
        self.populate_rows()

    def populate_rows(self):
        # Limpiar
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
        self.row_widgets = []
        for row_idx, row in enumerate(self.buttons):
            self.add_row_widget(row_idx, row)

    def add_row(self):
        self.buttons.append([])
        self.add_row_widget(len(self.buttons) - 1, [])

    def add_row_widget(self, row_idx, row_buttons):
        group = QGroupBox(f"Fila {row_idx + 1}")
        layout = QVBoxLayout(group)
        # Selector de cantidad de botones en la fila
        btn_count_layout = QHBoxLayout()
        btn_count_layout.addWidget(QLabel("Cantidad de botones en esta fila:"))
        btn_count = QSpinBox()
        btn_count.setMinimum(1)
        btn_count.setMaximum(8)
        btn_count.setValue(len(row_buttons) if row_buttons else 1)
        btn_count_layout.addWidget(btn_count)
        layout.addLayout(btn_count_layout)

        # Área de edición de botones
        edits_layout = QHBoxLayout()
        edits = []
        for i in range(btn_count.value()):
            name_edit = QLineEdit(row_buttons[i]["text"] if i < len(row_buttons) else "")
            name_edit.setPlaceholderText("Texto")
            url_edit = QLineEdit(row_buttons[i]["url"] if i < len(row_buttons) else "")
            url_edit.setPlaceholderText("URL")
            # --- Ajuste para que los campos ocupen todo el ancho ---
            name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            url_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            edits_layout.addWidget(name_edit)
            edits_layout.addWidget(url_edit)
            edits.append((name_edit, url_edit))

            # --- Guardar el campo activo para el emoji ---
            name_edit.installEventFilter(self)
        layout.addLayout(edits_layout)

        # Sincronizar cantidad de botones
        def update_btn_fields():
            while len(edits) < btn_count.value():
                name_edit = QLineEdit()
                name_edit.setPlaceholderText("Texto")
                url_edit = QLineEdit()
                url_edit.setPlaceholderText("URL")
                name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                url_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                edits_layout.addWidget(name_edit)
                edits_layout.addWidget(url_edit)
                edits.append((name_edit, url_edit))
                name_edit.installEventFilter(self)
            while len(edits) > btn_count.value():
                name_edit, url_edit = edits.pop()
                name_edit.deleteLater()
                url_edit.deleteLater()

        btn_count.valueChanged.connect(update_btn_fields)

        self.scroll_layout.addWidget(group)
        self.row_widgets.append((btn_count, edits))

    def eventFilter(self, obj, event):
        # Guardar el QLineEdit de texto activo para el emoji
        if event.type() == QEvent.FocusIn and isinstance(obj, QLineEdit):
            self.active_text_field = obj
        return super().eventFilter(obj, event)

    def insert_emoji_to_active(self):
        if self.active_text_field is not None:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor_pos = self.active_text_field.cursorPosition()
                    text = self.active_text_field.text()
                    self.active_text_field.setText(text[:cursor_pos] + emoji + text[cursor_pos:])
                    self.active_text_field.setCursorPosition(cursor_pos + len(emoji))

    def get_values(self):
        result = []
        for btn_count, edits in self.row_widgets:
            row = []
            for i in range(btn_count.value()):
                name_edit, url_edit = edits[i]
                text = name_edit.text().strip()
                url = url_edit.text().strip()
                if text and url:
                    row.append({"text": text, "url": url})
            if row:
                result.append(row)
        return result