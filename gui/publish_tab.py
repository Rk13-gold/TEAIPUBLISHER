from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QSizePolicy
)

# Import unified theme system
try:
    from gui.telegram_theme import TelegramTheme
except ImportError:
    TelegramTheme = None
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import requests
import json
import re

from gui.post_preview import PostPreviewWidget
from gui.emoji_picker import EmojiPicker
from gui.button_config_dialog import ButtonConfigDialog
from gui.file_upload_widget import FileUploadWidget
from gui.call_to_action_widget import CallToActionWidget
from gui.hashtag_suggester_widget import HashtagSuggesterWidget

# --- Estilo global para los botones de emoji ---
EMOJI_BTN_STYLE = """
QPushButton {
    background: none;
    border: none;
    font-size: 22px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    padding: 0;
}
QPushButton:hover {
    background: #222;
}
"""

class PublishTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        # Apply unified theme
        if TelegramTheme:
            TelegramTheme.apply_theme_to_widget(self)
        self.config = config
        self.setWindowTitle("Publicar en Telegram")

        self.presentation_media_path = None  # Imagen/video/gif principal
        self.presentation_media_type = None  # "photo", "video", "animation"
        self.telegram_buttons = [[]]

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        # --------- LADO IZQUIERDO: EDICIÓN ---------
        left_side = QVBoxLayout()
        left_side.setSpacing(12)

        # --- Título, emoji y botón de presentación arriba ---
        title_img_layout = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título del post")
        self.title_edit.textChanged.connect(self.update_preview)
        title_img_layout.addWidget(QLabel("Título:"))
        title_img_layout.addWidget(self.title_edit, 2)

        # Botón de emoji para título
        self.title_emoji_btn = QPushButton("🛸")
        self.title_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        title_img_layout.addWidget(self.title_emoji_btn, 0)

        # Botón de presentación (imagen/video/gif)
        self.presentation_btn = QPushButton("📷/🎬 Presentación")
        self.presentation_btn.setToolTip("Seleccionar imagen, video o gif de presentación")
        self.presentation_btn.clicked.connect(self.select_presentation_media)
        title_img_layout.addWidget(self.presentation_btn, 0)

        left_side.addLayout(title_img_layout)

        # --- Edición y Envío a Telegram ---
        edit_group = QGroupBox("Edición y Envío a Telegram")
        edit_layout = QVBoxLayout()
        edit_layout.setSpacing(8)

        self.edit_area = QTextEdit()
        self.edit_area.setPlaceholderText("Aquí puedes editar el copy antes de enviarlo a Telegram...")
        edit_layout.addWidget(self.edit_area)

        buttons_row = QHBoxLayout()
        self.button_config_btn = QPushButton("Agregar botones")
        self.button_config_btn.clicked.connect(self.open_button_config)
        buttons_row.addWidget(self.button_config_btn)

        self.emoji_btn = QPushButton("🛸")
        self.emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.emoji_btn.clicked.connect(self.insert_emoji)
        buttons_row.addWidget(self.emoji_btn)
        buttons_row.addStretch(1)
        edit_layout.addLayout(buttons_row)

        # --- Botón Enviar debajo de la edición ---
        send_row = QHBoxLayout()
        send_row.addStretch(1)
        self.publish_button = QPushButton("Enviar")
        self.publish_button.clicked.connect(self.publish_post)
        send_row.addWidget(self.publish_button)
        edit_layout.addLayout(send_row)

        edit_group.setLayout(edit_layout)
        edit_group.setMinimumWidth(320)
        left_side.addWidget(edit_group, 2)

        main_layout.addLayout(left_side, 2)

        # --------- CENTRO: PREVISUALIZADOR ---------
        self.post_preview = PostPreviewWidget()
        self.post_preview.setMinimumWidth(350)
        self.post_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.post_preview, 2)

        # --------- DERECHA: SUBIDA Y EXTRAS ---------
        right_side = QVBoxLayout()
        right_side.setSpacing(12)

        # Sección 1: Archivos adicionales
        self.file_upload_widget = FileUploadWidget()
        right_side.addWidget(self.file_upload_widget)

        # Sección 2: Llamado a la acción (con emoji)
        cta_row = QHBoxLayout()
        self.cta_widget = CallToActionWidget()
        cta_row.addWidget(self.cta_widget)
        self.cta_emoji_btn = QPushButton("🛸")
        self.cta_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.cta_emoji_btn.clicked.connect(self.insert_emoji_cta)
        cta_row.addWidget(self.cta_emoji_btn)
        right_side.addLayout(cta_row)

        # Sección 3: Hashtags sugeridos
        self.hashtag_widget = HashtagSuggesterWidget()
        right_side.addWidget(self.hashtag_widget)

        main_layout.addLayout(right_side, 2)

        # Eventos para actualizar preview
        self.edit_area.textChanged.connect(self.update_preview)
        self.title_edit.textChanged.connect(self.update_preview)
        self.cta_widget.cta_edit.textChanged.connect(self.update_preview)
        self.post_preview.image_label.mousePressEvent = self.post_preview_select_media

        self.update_preview()

    # --- Emoji picker para título ---
    def insert_emoji_title(self):
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor = self.title_edit.cursorPosition()
                text = self.title_edit.text()
                self.title_edit.setText(text[:cursor] + emoji + text[cursor:])
                self.title_edit.setCursorPosition(cursor + len(emoji))

    # --- Emoji picker para edición ---
    def insert_emoji(self):
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor = self.edit_area.textCursor()
                cursor.insertText(emoji)

    # --- Emoji picker para CTA ---
    def insert_emoji_cta(self):
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor = self.cta_widget.cta_edit.textCursor()
                cursor.insertText(emoji)

    # --- Seleccionar imagen/video/gif de presentación ---
    def select_presentation_media(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen, video o gif de presentación",
            "",
            "Imágenes/Videos/GIF (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.gif)"
        )
        if file:
            ext = file.lower().split('.')[-1]
            if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                self.presentation_media_type = "photo"
            elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                self.presentation_media_type = "video"
            elif ext == 'gif':
                self.presentation_media_type = "animation"
            else:
                self.presentation_media_type = None
            self.presentation_media_path = file
            self.update_preview()

    def post_preview_select_media(self, event):
        self.select_presentation_media()

    # --- Actualizar previsualización ---
    def update_preview(self):
        title = self.title_edit.text().strip()
        text = self.edit_area.toPlainText()
        cta = self.cta_widget.get_call_to_action()
        hashtags = self.hashtag_widget.get_hashtags()
        files = self.file_upload_widget.get_files()

        # Estructura estricta: presentación, título, contenido, archivos, CTA, hashtags, botones
        preview_html = ""
        # 1. Presentación
        if self.presentation_media_path and self.presentation_media_type == "photo":
            self.post_preview.set_image(self.presentation_media_path)
        else:
            self.post_preview.set_image(None)
        # 2. Título
        if title:
            preview_html += f"<b>{title}</b><br>"
        # 3. Contenido
        preview_html += self.format_telegram_post(text) + "<br>"
        # 4. Archivos adicionales
        if files:
            preview_html += "<b>Archivos adjuntos:</b><br>"
            for f in files:
                preview_html += f"{f}<br>"
        # 5. CTA
        if cta:
            preview_html += f"<br><b>{cta}</b><br>"
        # 6. Hashtags
        if hashtags:
            preview_html += f"<br>{hashtags}<br>"
        self.post_preview.set_html(preview_html)
        # 7. Botones
        keyboard = []
        if self.telegram_buttons and any(self.telegram_buttons):
            for row in self.telegram_buttons:
                row_buttons = []
                for btn in row:
                    if isinstance(btn, dict) and "text" in btn and "url" in btn:
                        row_buttons.append({"text": btn["text"], "url": btn["url"]})
                if row_buttons:
                    keyboard.append(row_buttons)
        self.post_preview.set_buttons(keyboard, "row")

    def format_telegram_post(self, text):
        lines = text.splitlines()
        formatted = []
        in_code_block = False
        for line in lines:
            stripped = line.rstrip()
            # Detectar inicio/fin de bloque de código con ```
            if stripped.startswith("```"):
                if not in_code_block:
                    formatted.append("<pre>")
                    in_code_block = True
                else:
                    formatted.append("</pre>")
                    in_code_block = False
                continue
            # Detectar líneas con sangría (4 espacios) como bloque de código
            if not in_code_block and (line.startswith("    ") or line.startswith("\t")):
                formatted.append("<pre>")
                in_code_block = True
            if in_code_block and not (line.startswith("    ") or line.startswith("\t")) and not stripped.startswith("```"):
                formatted.append("</pre>")
                in_code_block = False
            if in_code_block:
                formatted.append(stripped)
                continue
            if stripped.startswith("Título:") or (stripped.isupper() and len(stripped) > 3):
                title = stripped.replace("Título:", "").strip()
                if title:
                    formatted.append(f"<b>{title}</b>")
                continue
            if stripped.startswith("Subtítulo:"):
                subtitle = stripped.replace("Subtítulo:", "").strip()
                if subtitle:
                    formatted.append(f"<b>{subtitle}</b>")
                continue
            if stripped.startswith("- ") or stripped.startswith("* "):
                formatted.append(f"• {stripped[2:]}")
                continue
            if "http://" in stripped or "https://" in stripped:
                url_pattern = r'(https?://\S+)'
                def repl(m):
                    url = m.group(1)
                    return f'<a href="{url}">{url}</a>'
                line = re.sub(url_pattern, repl, stripped)
                formatted.append(line)
                continue
            if not stripped:
                formatted.append("")
                continue
            formatted.append(stripped)
        if in_code_block:
            formatted.append("</pre>")
        return "<br>".join(formatted)

    def open_button_config(self):
        dlg = ButtonConfigDialog(self, self.telegram_buttons)
        if dlg.exec():
            self.telegram_buttons = dlg.get_values()
            self.update_preview()

    def publish_post(self):
        token = self.config.telegram_token
        chat_id = self.config.telegram_chat_id
        reply_markup = None
        keyboard = []
        if self.telegram_buttons and any(self.telegram_buttons):
            for row in self.telegram_buttons:
                row_buttons = []
                for btn in row:
                    if isinstance(btn, dict) and "text" in btn and "url" in btn:
                        row_buttons.append({"text": btn["text"], "url": btn["url"]})
                if row_buttons:
                    keyboard.append(row_buttons)
        if keyboard:
            reply_markup = json.dumps({"inline_keyboard": keyboard})

        title = self.title_edit.text().strip()
        text = self.edit_area.toPlainText().strip()
        cta = self.cta_widget.get_call_to_action()
        hashtags = self.hashtag_widget.get_hashtags()
        files = self.file_upload_widget.get_files()

        # 1. Título + contenido
        main_content = ""
        if title:
            main_content += f"<b>{title}</b>\n\n"
        main_content += text

        # 2. Enviar presentación (caption solo si <= 1024) - SIN reply_markup
        if self.presentation_media_path and self.presentation_media_type:
            caption = main_content if len(main_content) <= 1024 else main_content[:1020] + "..."
            if self.presentation_media_type == "photo":
                self.send_telegram_photo(token, chat_id, self.presentation_media_path, caption, None)
            elif self.presentation_media_type == "video":
                self.send_telegram_video(token, chat_id, self.presentation_media_path, caption, None)
            elif self.presentation_media_type == "animation":
                self.send_telegram_animation(token, chat_id, self.presentation_media_path, caption, None)
        else:
            # Si no hay presentación, enviar el texto principal como mensaje SIN reply_markup
            self.send_telegram_message(token, chat_id, main_content, None)

        # 3. Archivos adicionales (sin caption, SIN reply_markup)
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                self.send_telegram_photo(token, chat_id, f, "", None)
            elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                self.send_telegram_video(token, chat_id, f, "", None)
            elif ext == 'gif':
                self.send_telegram_animation(token, chat_id, f, "", None)
            else:
                self.send_telegram_document(token, chat_id, f, "", None)

        # 4. CTA + hashtags (en un solo mensaje, AQUÍ SÍ reply_markup)
        cta_hashtags = ""
        if cta:
            cta_hashtags += f"{cta}\n"
        if hashtags:
            cta_hashtags += hashtags
        if cta_hashtags.strip():
            self.send_telegram_message(token, chat_id, cta_hashtags, reply_markup)

    def send_telegram_message(self, token, chat_id, text, reply_markup):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        try:
            response = requests.post(url, data=data)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Error al publicar mensaje en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar mensaje: {e}")

    def send_telegram_photo(self, token, chat_id, file_path, caption, reply_markup):
        try:
            files = {"photo": open(file_path, "rb")}
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Error al publicar imagen en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar imagen: {e}")

    def send_telegram_video(self, token, chat_id, file_path, caption, reply_markup):
        try:
            files = {"video": open(file_path, "rb")}
            url = f"https://api.telegram.org/bot{token}/sendVideo"
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Error al publicar video en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar video: {e}")

    def send_telegram_animation(self, token, chat_id, file_path, caption, reply_markup):
        try:
            files = {"animation": open(file_path, "rb")}
            url = f"https://api.telegram.org/bot{token}/sendAnimation"
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Error al publicar GIF en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar GIF: {e}")

    def send_telegram_document(self, token, chat_id, file_path, caption, reply_markup):
        try:
            files = {"document": open(file_path, "rb")}
            url = f"https://api.telegram.org/bot{token}/sendDocument"
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            if not result.get("ok"):
                error_msg = result.get("description", "Error al publicar archivo en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar archivo: {e}")