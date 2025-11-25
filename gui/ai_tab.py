from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QTextEdit, QLineEdit,
    QPushButton, QProgressBar, QMessageBox, QSizePolicy, QLabel, QToolButton, QDialog, QDialogButtonBox,
    QFileDialog
)

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIntValidator, QFont
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import requests
import json
import re

from ai_integration.groq_client import GroqClient
from gui.post_preview import PostPreviewWidget
from gui.emoji_picker import EmojiPicker
from gui.button_config_dialog import ButtonConfigDialog

# --- Worker para la IA ---
class GroqWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, client, messages):
        super().__init__()
        self.client = client
        self.messages = messages

    def run(self):
        try:
            result = self.client.chat(self.messages)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# --- Diálogo de configuración IA ---
class AIConfigDialog(QDialog):
    def __init__(self, parent=None, base_prompt="", emoji_count=0, copy_options=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de la IA")
        layout = QFormLayout(self)

        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlainText(base_prompt)
        layout.addRow("Prompt base:", self.instructions_edit)

        self.emoji_count_edit = QLineEdit(str(emoji_count))
        self.emoji_count_edit.setValidator(QIntValidator(0, 20))
        layout.addRow("Cantidad de emojis:", self.emoji_count_edit)

        self.copy_options_edit = QTextEdit()
        self.copy_options_edit.setPlaceholderText("Un copy por línea. Ejemplo:\n¡Nuevo post!\nDescubre más aquí...")
        if copy_options:
            self.copy_options_edit.setPlainText("\n".join(copy_options))
        layout.addRow("Copys a elegir:", self.copy_options_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def get_values(self):
        return (
            self.instructions_edit.toPlainText().strip(),
            int(self.emoji_count_edit.text() or "0"),
            [line.strip() for line in self.copy_options_edit.toPlainText().splitlines() if line.strip()]
        )

# --- TAB PRINCIPAL ---
class AITab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Generador IA para Telegram")

        # Estado
        self.base_prompt = "Eres un asistente experto en generación de textos para Telegram. Responde solo con el texto del post, sin saludos ni despedidas."
        self.emoji_count = 0
        self.copy_options = []
        self.last_ai_response = ""
        self.telegram_image_path = None
        self.telegram_buttons = [[]]
        self.prompt_template = self._load_prompt_template()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        # --------- LADO IZQUIERDO: CHAT IA ---------
        chat_group = QGroupBox("Chat IA (orientado a Telegram)")
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(8)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("🔥 Describe un post viral que necesitas, completa el brief y genera")
        chat_layout.addWidget(self.chat_history)

        # Brief rápido para tema + instrucciones
        brief_group = QGroupBox("Brief creativo")
        brief_form = QFormLayout()

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Tema principal del post (ej. 'Growth en Telegram')")
        brief_form.addRow("Tema:", self.topic_input)

        self.brief_instructions = QTextEdit()
        self.brief_instructions.setPlaceholderText("Indicaciones específicas: tono, formato, CTA, etc.")
        self.brief_instructions.setFixedHeight(80)
        brief_form.addRow("Instrucciones:", self.brief_instructions)

        brief_group.setLayout(brief_form)
        chat_layout.addWidget(brief_group)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Escribe tu mensaje para la IA...")
        self.input_line.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("🌐 GENERAR")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        # --- Botón de configuración IA debajo de "Generar" ---
        self.config_button = QToolButton()
        self.config_button.setText("⚙️ Configuración IA")
        self.config_button.clicked.connect(self.open_ai_config)
        chat_layout.addWidget(self.config_button, 0, Qt.AlignLeft)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        chat_layout.addWidget(self.progress_bar)

        chat_group.setLayout(chat_layout)
        chat_group.setMinimumWidth(400)
        chat_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(chat_group, 2)

        # --------- LADO DERECHO: CONFIG, EDICIÓN Y PREVISUALIZACIÓN ---------
        right_side = QVBoxLayout()
        right_side.setSpacing(12)

        # --- Título, emoji y botón de imagen arriba ---
        title_img_layout = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título del post")
        self.title_edit.textChanged.connect(self.update_preview)
        title_img_layout.addWidget(QLabel("Título:"))
        title_img_layout.addWidget(self.title_edit, 2)

        # Botón de emoji para título (corregido)
        self.title_emoji_btn = QPushButton("🛸")
        self.title_emoji_btn.setFixedSize(34, 34)
        self.title_emoji_btn.setFont(QFont("Segoe UI Emoji", 22))
        self.title_emoji_btn.setProperty("class", "emoji-btn")
        self.title_emoji_btn.setStyleSheet("color: none; background: none; border: none;")
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        title_img_layout.addWidget(self.title_emoji_btn, 0)

        # Botón de imagen
        self.image_btn = QPushButton("📷 Imagen")
        self.image_btn.setToolTip("Seleccionar imagen para previsualización")
        self.image_btn.clicked.connect(self.select_image_for_preview)
        title_img_layout.addWidget(self.image_btn, 0)

        right_side.addLayout(title_img_layout)

        # --- Edición y Envío a Telegram + Previsualización tipo Telegram ---
        edit_and_preview_layout = QHBoxLayout()
        edit_and_preview_layout.setSpacing(16)

        # Edición y envío
        edit_group = QGroupBox("Edición y Envío a Telegram")
        edit_layout = QVBoxLayout()
        edit_layout.setSpacing(8)

        self.edit_area = QTextEdit()
        self.edit_area.setPlaceholderText("Aquí puedes editar el copy generado antes de enviarlo a Telegram...")
        edit_layout.addWidget(self.edit_area)

        # Botón para agregar botones y botón de emoji juntos
        buttons_row = QHBoxLayout()
        self.button_config_btn = QPushButton("Agregar botones")
        self.button_config_btn.clicked.connect(self.open_button_config)
        buttons_row.addWidget(self.button_config_btn)

        # Botón de emoji para el área de edición (corregido)
        self.emoji_btn = QPushButton("🛸")
        self.emoji_btn.setFixedSize(34, 34)
        self.emoji_btn.setFont(QFont("Segoe UI Emoji", 22))
        self.emoji_btn.setProperty("class", "emoji-btn")
        self.emoji_btn.setStyleSheet("color: none; background: none; border: none;")
        self.emoji_btn.clicked.connect(self.insert_emoji)
        buttons_row.addWidget(self.emoji_btn)

        buttons_row.addStretch(1)
        edit_layout.addLayout(buttons_row)

        import_layout = QHBoxLayout()
        self.import_button = QPushButton("I-CONT IA")
        self.import_button.clicked.connect(self.import_response)
        self.publish_button = QPushButton("Enviar")
        self.publish_button.clicked.connect(self.publish_post)
        import_layout.addWidget(self.import_button)
        import_layout.addWidget(self.publish_button)
        edit_layout.addLayout(import_layout)

        edit_group.setLayout(edit_layout)
        edit_group.setMinimumWidth(320)
        edit_and_preview_layout.addWidget(edit_group, 2)

        # --- Previsualizador sincronizado y profesional ---
        self.post_preview = PostPreviewWidget()
        self.post_preview.setMinimumWidth(350)
        self.post_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        edit_and_preview_layout.addWidget(self.post_preview, 2)

        right_side.addLayout(edit_and_preview_layout, 2)

        self.edit_area.textChanged.connect(self.update_preview)
        self.title_edit.textChanged.connect(self.update_preview)

        main_layout.addLayout(right_side, 2)

        self.groq_client = GroqClient(
            api_key=getattr(self.config, "groq_api_key", ""),
            model=getattr(self.config, "groq_model", "mixtral-8x7b-32768")
        )

        # Imagen: seleccionar desde el botón de imagen o desde el preview
        self.post_preview.image_label.mousePressEvent = self.post_preview_select_image

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

    # --- Nuevo método para seleccionar imagen desde el botón ---
    def select_image_for_preview(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if file:
            self.telegram_image_path = file
            self.update_preview()

    # --- Actualizar previsualización ---
    def update_preview(self):
        title = self.title_edit.text().strip()
        text = self.edit_area.toPlainText()
        preview_text = self.format_telegram_post(f"{title}\n\n{text}" if title else text)
        preview_html = preview_text.replace("\n", "<br>")
        self.post_preview.set_html(preview_html)
        self.post_preview.set_image(self.telegram_image_path)
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

    # --- Imagen en previsualización (clic en imagen) ---
    def post_preview_select_image(self, event):
        self.select_image_for_preview()

    # --- Formateo profesional para Telegram ---
    def format_telegram_post(self, text):
        lines = text.splitlines()
        formatted = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            # Título: primera línea, o línea en mayúsculas, o que empieza con "Título:"
            if idx == 0 or stripped.startswith("Título:") or (stripped.isupper() and len(stripped) > 3):
                title = stripped.replace("Título:", "").strip()
                if title:
                    formatted.append(f"<b>{title}</b>")
                continue
            # Subtítulo: línea que empieza con "Subtítulo:"
            if stripped.startswith("Subtítulo:"):
                subtitle = stripped.replace("Subtítulo:", "").strip()
                if subtitle:
                    formatted.append(f"<b>{subtitle}</b>")
                continue
            # Listas: líneas que empiezan con "- " o "* "
            if stripped.startswith("- ") or stripped.startswith("* "):
                formatted.append(f"• {stripped[2:]}")
                continue
            # Enlaces: http/https
            if "http://" in stripped or "https://" in stripped:
                url_pattern = r'(https?://\S+)'
                def repl(m):
                    url = m.group(1)
                    return f'<a href="{url}">{url}</a>'
                line = re.sub(url_pattern, repl, stripped)
                formatted.append(line)
                continue
            # Línea vacía
            if not stripped:
                formatted.append("")
                continue
            # Código: empieza con 4 espacios o ```
            if stripped.startswith("```") or stripped.startswith("    "):
                code = stripped.replace("```", "").strip()
                formatted.append(f"<code>{code}</code>")
                continue
            # Por defecto, texto normal
            formatted.append(stripped)
        return "\n".join(formatted)

    # --- Métodos de configuración ---
    def open_ai_config(self):
        dlg = AIConfigDialog(self, self.base_prompt, self.emoji_count, self.copy_options)
        if dlg.exec():
            self.base_prompt, self.emoji_count, self.copy_options = dlg.get_values()

    def open_button_config(self):
        dlg = ButtonConfigDialog(self, self.telegram_buttons)
        if dlg.exec():
            self.telegram_buttons = dlg.get_values()
            self.update_preview()

    # --- Emoji picker para edición ---
    def insert_emoji(self):
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor = self.edit_area.textCursor()
                cursor.insertText(emoji)

    # --- Métodos de IA ---
    def build_prompt_messages(self, topic, instructions, user_message):
        template = self.prompt_template or {}
        system_message = self._compose_system_message(template)
        payload = self._compose_user_payload(template, topic, instructions, user_message)
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": content}
        ]

    def send_message(self):
        if not getattr(self.config, "groq_api_key", ""):
            QMessageBox.warning(self, "Groq", "Configura tu API Key de Groq en config.json para generar contenido.")
            return

        user_message = self.input_line.text().strip()
        topic = self.topic_input.text().strip()
        instructions = self.brief_instructions.toPlainText().strip()

        if not topic:
            QMessageBox.warning(self, "Brief incompleto", "Ingresa al menos un tema principal para el post.")
            return

        if not user_message and not instructions:
            QMessageBox.warning(self, "Brief incompleto", "Agrega instrucciones o un mensaje para la IA.")
            return

        messages = self.build_prompt_messages(topic, instructions, user_message)
        resumen = f"<b>Tema:</b> {topic}"
        if instructions:
            resumen += f"<br><i>Brief:</i> {instructions}"
        if user_message:
            resumen += f"<br><i>Mensaje:</i> {user_message}"
        self.chat_history.append(f"<b style='color:#0078d7'>Brief enviado:</b><br>{resumen}")
        self.input_line.clear()
        self.send_button.setEnabled(False)
        self.input_line.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = GroqWorker(self.groq_client, messages)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()

    def on_ai_response(self, response):
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        self.input_line.setEnabled(True)
        self.input_line.setFocus()
        if "error" in response:
            self.chat_history.append(f"<b style='color:#e53935'>IA (error):</b> {response['error']}")
            self.last_ai_response = ""
        else:
            raw_text = response.get("text", "")
            text = self._normalize_markdown_bold(raw_text)
            self.last_ai_response = text
            self.chat_history.append(f"<b style='color:#009688'>IA:</b> {text}")

    def on_ai_error(self, message):
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        self.input_line.setEnabled(True)
        self.input_line.setFocus()
        self.chat_history.append(f"<b style='color:#e53935'>IA (error):</b> {message}")

    def import_response(self):
        if not self.last_ai_response:
            QMessageBox.warning(self, "Error", "No hay respuesta de IA para importar.")
            return
        formatted = self.format_telegram_post(self.last_ai_response)
        self.edit_area.setPlainText(formatted)

    # --- Publicar en Telegram ---
    def publish_post(self):
        content = self.edit_area.toPlainText().strip()
        title = self.title_edit.text().strip()
        if title:
            content = f"<b>{title}</b>\n\n{content}"
        content = self._prepare_content_for_telegram(content)
        if not content:
            QMessageBox.warning(self, "Error", "El contenido a publicar no puede estar vacío.")
            return

        token = self.config.telegram_token
        chat_id = self.config.telegram_chat_id

        # Adjuntar botones si existen (corregido para lista de filas)
        keyboard = []
        if self.telegram_buttons and any(self.telegram_buttons):
            for row in self.telegram_buttons:
                row_buttons = []
                for btn in row:
                    if isinstance(btn, dict) and "text" in btn and "url" in btn:
                        row_buttons.append({"text": btn["text"], "url": btn["url"]})
                if row_buttons:
                    keyboard.append(row_buttons)
        reply_markup = json.dumps({"inline_keyboard": keyboard}) if keyboard else None

        # Si hay imagen y el texto es <= 1024, usa sendPhoto, si no, primero manda la foto y luego el texto
        if self.telegram_image_path:
            if len(content) <= 1024:
                try:
                    files = {"photo": open(self.telegram_image_path, "rb")}
                    photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    payload = {
                        "chat_id": chat_id,
                        "caption": content,
                        "parse_mode": "HTML"
                    }
                    if reply_markup:
                        payload["reply_markup"] = reply_markup
                    response = requests.post(photo_url, data=payload, files=files)
                    result = response.json()
                    if result.get("ok"):
                        QMessageBox.information(self, "Éxito", "¡Post con imagen enviado a Telegram!")
                    else:
                        error_msg = result.get("description", "Error al publicar en Telegram.")
                        QMessageBox.critical(self, "Error", error_msg)
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al enviar imagen: {e}")
                    return
            else:
                # Enviar imagen sin caption, luego el texto como mensaje normal
                try:
                    files = {"photo": open(self.telegram_image_path, "rb")}
                    photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    payload = {
                        "chat_id": chat_id
                    }
                    response = requests.post(photo_url, data=payload, files=files)
                    # Ahora enviar el texto como mensaje normal
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": content,
                        "parse_mode": "HTML"
                    }
                    if reply_markup:
                        data["reply_markup"] = reply_markup
                    response = requests.post(url, data=data)
                    result = response.json()
                    if result.get("ok"):
                        QMessageBox.information(self, "Éxito", "¡Imagen y texto enviados a Telegram!")
                    else:
                        error_msg = result.get("description", "Error al publicar en Telegram.")
                        QMessageBox.critical(self, "Error", error_msg)
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al enviar imagen y texto: {e}")
                    return

        # Si no hay imagen, enviar solo el texto
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        try:
            response = requests.post(url, data=data)
            result = response.json()
            if result.get("ok"):
                QMessageBox.information(self, "Éxito", "¡Post enviado a Telegram!")
            else:
                error_msg = result.get("description", "Error al publicar en Telegram.")
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar el post: {e}")

    # --- Prompt helpers ---
    def _prepare_content_for_telegram(self, content: str) -> str:
        """Normaliza saltos de línea y permite solo etiquetas HTML válidas para Telegram."""
        normalized = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
        normalized = re.sub(r"<br\s*/?>", "\n", normalized, flags=re.IGNORECASE)
        sanitizer = _TelegramHTMLSanitizer()
        sanitizer.feed(normalized)
        sanitizer.close()
        return sanitizer.get_data().strip()

    def _normalize_markdown_bold(self, text: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    def _load_prompt_template(self):
        template_path = getattr(self.config, "groq_prompt_template", "")
        if not template_path:
            return {}
        path = Path(template_path)
        if not path.is_absolute():
            base_dir = getattr(self.config, "base_dir", Path(__file__).resolve().parents[1])
            path = Path(base_dir) / template_path
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception as exc:
            print(f"⚠️ No se pudo cargar el template de prompt ({path}): {exc}")
            return {}

    def _compose_system_message(self, template):
        parts = [template.get("system_instruction", self.base_prompt)]
        persona = template.get("persona", {})
        if persona:
            parts.append(
                f"Actúa como {persona.get('nombre', 'un estratega')} con habilidades en "
                f"{', '.join(persona.get('habilidades', []))}. Objetivo: {persona.get('objetivo', '')}."
            )
        defaults = template.get("defaults", {})
        if defaults:
            parts.append(
                f"Tono: {defaults.get('tono', 'profesional')}. Audiencia: {defaults.get('audiencia', 'usuarios de Telegram')}"
            )
        if self.copy_options:
            parts.append("Copys sugeridos: " + " | ".join(self.copy_options))
        if self.emoji_count:
            parts.append(f"Incluye aproximadamente {self.emoji_count} emojis.")
        if self.base_prompt:
            parts.append(self.base_prompt)
        return "\n".join([p for p in parts if p])

    def _compose_user_payload(self, template, topic, instructions, user_message):
        framework = template.get("virality_framework", {})
        output = template.get("output_format", {})
        defaults = template.get("defaults", {})
        return {
            "tema": topic,
            "instrucciones": instructions or user_message,
            "mensaje_chat": user_message,
            "contexto": {
                "framework": framework,
                "output_format": output,
                "defaults": defaults,
            }
        }


class _TelegramHTMLSanitizer(HTMLParser):
    allowed_tags = {
        "b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "code", "pre", "a"
    }
    allowed_attrs = {"a": {"href"}}

    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in self.allowed_tags:
            return
        attr_text = ""
        if attrs and tag in self.allowed_attrs:
            filtered = []
            for name, value in attrs:
                if name in self.allowed_attrs[tag] and value:
                    if tag == "a" and not value.lower().startswith(("http://", "https://")):
                        continue
                    filtered.append((name, escape(value, quote=True)))
            if filtered:
                attr_text = " " + " ".join(f'{k}="{v}"' for k, v in filtered)
        self._chunks.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.allowed_tags:
            self._chunks.append(f"</{tag}>")

    def handle_data(self, data):
        if data:
            self._chunks.append(escape(data, quote=False))

    def handle_entityref(self, name):
        self._chunks.append(f"&{name};")

    def handle_charref(self, name):
        self._chunks.append(f"&#{name};")

    def get_data(self) -> str:
        return "".join(self._chunks)