from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QSizePolicy, QProgressBar,
    QComboBox, QFrame, QFormLayout, QApplication
)

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import requests
import json
import os
import time
import re
from datetime import datetime

# Professional imports for production-ready functionality
try:
    from gui.post_preview import PostPreviewWidget
except ImportError:
    PostPreviewWidget = None

try:
    from gui.emoji_picker import EmojiPicker
except ImportError:
    EmojiPicker = None

try:
    from gui.button_config_dialog import ButtonConfigDialog
except ImportError:
    ButtonConfigDialog = None

try:
    from services.voice_notes import convert_audio_to_ogg, get_audio_quality_settings
except ImportError:
    # Fallback audio conversion functions
    def convert_audio_to_ogg(input_path, output_path, quality="high", title="", artist="", album=""):
        """Fallback audio conversion - copies file if conversion not available"""
        import shutil
        if not output_path.endswith('.ogg'):
            output_path = output_path.rsplit('.', 1)[0] + '.ogg'
        shutil.copy2(input_path, output_path)
        return True
    
    def get_audio_quality_settings():
        """Fallback quality settings"""
        return {
            "low": {"bitrate": "64k", "name": "Estándar (64k)"},
            "medium": {"bitrate": "128k", "name": "Alta (128k)"},
            "high": {"bitrate": "256k", "name": "Premium (256k)"},
            "ultra": {"bitrate": "320k", "name": "Ultra (320k)"}
        }

class FileUploadWidget:
    """Widget para manejar archivos adicionales"""
    def __init__(self):
        self.files = []
    
    def get_files(self):
        return self.files
    
    def add_file(self, file_path):
        if file_path not in self.files:
            self.files.append(file_path)
    
    def clear_files(self):
        self.files.clear()

class PublishWorker(QThread):
    """Professional worker for step-by-step Telegram publishing"""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # Success, final message
    
    def __init__(self, post_data, config):
        super().__init__()
        self.post_data = post_data
        self.config = config
        
    def run(self):
        try:
            token = self.config.telegram_token
            chat_id = self.config.telegram_chat_id
            
            # Step 1: Send premium voice note if exists
            if self.post_data.get('voice_file'):
                self.progress.emit("🎵 Procesando nota de voz premium...")
                success = self.send_voice_note(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar nota de voz")
                    return
                time.sleep(1)
            
            # Step 2: Send main presentation
            if self.post_data.get('presentation_path'):
                self.progress.emit("📸 Enviando contenido principal...")
                success = self.send_presentation(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar presentación")
                    return
                time.sleep(1)
            elif self.post_data.get('main_content'):
                self.progress.emit("📝 Enviando mensaje principal...")
                success = self.send_main_message(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar mensaje")
                    return
                time.sleep(1)
            
            # Step 3: Send additional files
            if self.post_data.get('additional_files'):
                self.progress.emit("📎 Enviando archivos adicionales...")
                success = self.send_additional_files(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar archivos")
                    return
                time.sleep(1)
            
            # Step 4: Send CTA and hashtags with buttons
            if self.post_data.get('cta_hashtags'):
                self.progress.emit("🎯 Enviando llamada a la acción...")
                success = self.send_cta_hashtags(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar CTA")
                    return
            
            self.progress.emit("✅ Post publicado exitosamente")
            self.finished.emit(True, "Post enviado correctamente a Telegram")
            
        except Exception as e:
            self.finished.emit(False, f"Error inesperado: {str(e)}")
    
    def send_voice_note(self, token, chat_id):
        """Send premium voice note with high quality conversion"""
        try:
            voice_file = self.post_data['voice_file']
            voice_title = self.post_data.get('voice_title', '')
            voice_description = self.post_data.get('voice_description', '')
            quality = self.post_data.get('voice_quality', 'high')
            
            self.progress.emit("🔄 Convirtiendo audio a formato optimizado...")
            
            # Convert to OGG for best Telegram compatibility
            ext = os.path.splitext(voice_file)[1].lower()
            ogg_path = voice_file
            
            if ext != '.ogg':
                try:
                    ogg_path = voice_file.rsplit('.', 1)[0] + '_telegram.ogg'
                    success = convert_audio_to_ogg(
                        voice_file, 
                        ogg_path,
                        quality=quality,
                        title=voice_title or "Audio Premium",
                        artist="Canal Premium",
                        album="Contenido Exclusivo"
                    )
                    if success:
                        self.progress.emit("✅ Audio convertido exitosamente")
                    else:
                        self.progress.emit("⚠️ Usando archivo original")
                        ogg_path = voice_file
                except Exception as e:
                    self.progress.emit(f"⚠️ Error en conversión: {e}")
                    ogg_path = voice_file
            
            # Create caption
            caption = ""
            if voice_title:
                caption += f"👑 {voice_title}\n\n"
            if voice_description:
                caption += f"{voice_description}\n\n"
            caption += "💎 Contenido Premium Exclusivo 🔒"
            
            self.progress.emit("📤 Enviando nota de voz...")
            
            # Send voice note
            with open(ogg_path, "rb") as voice:
                url = f"https://api.telegram.org/bot{token}/sendVoice"
                files = {"voice": voice}
                data = {"chat_id": chat_id, "caption": caption}
                response = requests.post(url, data=data, files=files)
                
            # Clean up temporary file
            if ogg_path != voice_file and os.path.exists(ogg_path):
                os.remove(ogg_path)
                
            result = response.json()
            if result.get("ok"):
                self.progress.emit("✅ Nota de voz enviada correctamente")
                return True
            else:
                self.progress.emit(f"❌ Error: {result.get('description', 'Error desconocido')}")
                return False
            
        except Exception as e:
            self.progress.emit(f"❌ Error en nota de voz: {e}")
            return False
    
    def send_presentation(self, token, chat_id):
        """Send main presentation media"""
        try:
            file_path = self.post_data['presentation_path']
            media_type = self.post_data['presentation_type']
            caption = self.post_data.get('main_content', '')
            
            # Limit caption to 1024 characters for media posts
            if len(caption) > 1024:
                caption = caption[:1020] + "..."
            
            if media_type == "photo":
                return self.send_photo(token, chat_id, file_path, caption)
            elif media_type == "video":
                return self.send_video(token, chat_id, file_path, caption)
            elif media_type == "animation":
                return self.send_animation(token, chat_id, file_path, caption)
            
            return False
            
        except Exception as e:
            self.progress.emit(f"❌ Error en presentación: {e}")
            return False
    
    def send_main_message(self, token, chat_id):
        """Send text-only main message"""
        try:
            text = self.post_data['main_content']
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            response = requests.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                self.progress.emit("✅ Mensaje principal enviado")
                return True
            else:
                self.progress.emit(f"❌ Error: {result.get('description', 'Error desconocido')}")
                return False
        except Exception as e:
            self.progress.emit(f"❌ Error en mensaje: {e}")
            return False
    
    def send_additional_files(self, token, chat_id):
        """Send additional files"""
        try:
            files = self.post_data['additional_files']
            for i, file_path in enumerate(files, 1):
                self.progress.emit(f"📎 Enviando archivo {i}/{len(files)}: {os.path.basename(file_path)}")
                
                ext = file_path.lower().split('.')[-1]
                
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                    success = self.send_photo(token, chat_id, file_path, "")
                elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                    success = self.send_video(token, chat_id, file_path, "")
                elif ext == 'gif':
                    success = self.send_animation(token, chat_id, file_path, "")
                else:
                    success = self.send_document(token, chat_id, file_path, "")
                
                if not success:
                    return False
                
                time.sleep(0.5)  # Small delay between files
            
            self.progress.emit("✅ Todos los archivos enviados correctamente")
            return True
        except Exception as e:
            self.progress.emit(f"❌ Error en archivos: {e}")
            return False
    
    def send_cta_hashtags(self, token, chat_id):
        """Send CTA and hashtags with buttons"""
        try:
            text = self.post_data['cta_hashtags']
            reply_markup = self.post_data.get('reply_markup')
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            
            if reply_markup:
                data["reply_markup"] = reply_markup
                self.progress.emit("🔗 Agregando botones interactivos...")
                
            response = requests.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                self.progress.emit("✅ CTA y hashtags enviados")
                return True
            else:
                self.progress.emit(f"❌ Error: {result.get('description', 'Error desconocido')}")
                return False
        except Exception as e:
            self.progress.emit(f"❌ Error en CTA: {e}")
            return False
    
    def send_photo(self, token, chat_id, file_path, caption):
        """Send photo"""
        try:
            with open(file_path, "rb") as photo:
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                files = {"photo": photo}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                response = requests.post(url, data=data, files=files)
            return response.json().get("ok", False)
        except:
            return False
    
    def send_video(self, token, chat_id, file_path, caption):
        """Send video"""
        try:
            with open(file_path, "rb") as video:
                url = f"https://api.telegram.org/bot{token}/sendVideo"
                files = {"video": video}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                response = requests.post(url, data=data, files=files)
            return response.json().get("ok", False)
        except:
            return False
    
    def send_animation(self, token, chat_id, file_path, caption):
        """Send GIF/animation"""
        try:
            with open(file_path, "rb") as animation:
                url = f"https://api.telegram.org/bot{token}/sendAnimation"
                files = {"animation": animation}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                response = requests.post(url, data=data, files=files)
            return response.json().get("ok", False)
        except:
            return False
    
    def send_document(self, token, chat_id, file_path, caption):
        """Send document"""
        try:
            with open(file_path, "rb") as document:
                url = f"https://api.telegram.org/bot{token}/sendDocument"
                files = {"document": document}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                response = requests.post(url, data=data, files=files)
            return response.json().get("ok", False)
        except:
            return False

class PublishTab(QWidget):
    """Professional Telegram Publisher with AI Generator-inspired design"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("🚀 Publicar en Telegram")

        # State variables
        self.presentation_media_path = None
        self.presentation_media_type = None
        self.telegram_buttons = [[]]
        self.worker = None
        self.voice_selected_file = None
        self.file_upload_widget = FileUploadWidget()
        
        # Audio quality settings
        self.audio_quality_settings = get_audio_quality_settings()
        
        # Main layout using AI Generator structure
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        # Left side: Content creation and controls
        self.setup_left_content_section(main_layout)
        
        # Right side: Preview and publishing
        self.setup_right_preview_section(main_layout)
        
        # Connect events
        self.connect_all_events()

    def setup_left_content_section(self, main_layout):
        """Setup left content creation section similar to AI Generator"""
        content_group = QGroupBox("📝 Contenido para Telegram")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)

        # Title and media selection (top row)
        self.setup_title_media_row(content_layout)
        
        # Main content area
        self.setup_main_content_area(content_layout)
        
        # Voice note section (premium feature)
        self.setup_voice_note_section(content_layout)
        
        # Additional files section
        self.setup_additional_files_section(content_layout)
        
        # CTA and hashtags section
        self.setup_cta_hashtags_section(content_layout)
        
        # Publishing controls
        self.setup_publishing_controls(content_layout)

        content_group.setLayout(content_layout)
        content_group.setMinimumWidth(450)
        content_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(content_group, 2)

    def setup_title_media_row(self, layout):
        """Setup title and media selection row"""
        title_media_layout = QHBoxLayout()
        
        # Title input
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título del post...")
        title_media_layout.addWidget(QLabel("📝 Título:"))
        title_media_layout.addWidget(self.title_edit, 2)

        # Emoji button for title
        self.title_emoji_btn = QPushButton("🛸")
        self.title_emoji_btn.setFixedWidth(24)
        self.title_emoji_btn.setFont(QFont("Segoe UI Emoji", 18))
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        title_media_layout.addWidget(self.title_emoji_btn, 0)

        # Media selection button
        self.media_btn = QPushButton("📷 Media")
        self.media_btn.setToolTip("Seleccionar imagen/video/GIF para el post")
        self.media_btn.clicked.connect(self.select_presentation_media)
        title_media_layout.addWidget(self.media_btn, 0)

        layout.addLayout(title_media_layout)
        
        # Media status label
        self.media_status_label = QLabel("Sin media seleccionado")
        self.media_status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.media_status_label)

    def setup_main_content_area(self, layout):
        """Setup main content editing area"""
        content_group = QGroupBox("✍️ Contenido Principal")
        content_group_layout = QVBoxLayout()
        
        # Main text area
        self.edit_area = QTextEdit()
        self.edit_area.setPlaceholderText(
            "Escribe aquí el contenido principal del post...\n\n"
            "💡 Tips profesionales:\n"
            "• Usa títulos en MAYÚSCULAS o con **negrita**\n"
            "• Incluye listas con - o •\n"
            "• Agrega emojis relevantes 🚀\n"
            "• Mantén párrafos cortos para mejor lectura"
        )
        self.edit_area.setMinimumHeight(200)
        content_group_layout.addWidget(self.edit_area)

        # Content tools row
        tools_layout = QHBoxLayout()
        
        # Button configuration
        self.button_config_btn = QPushButton("🔗 Botones")
        self.button_config_btn.clicked.connect(self.open_button_config)
        tools_layout.addWidget(self.button_config_btn)

        # Emoji picker for content
        self.content_emoji_btn = QPushButton("🛸")
        self.content_emoji_btn.setFixedWidth(24)
        self.content_emoji_btn.setFont(QFont("Segoe UI Emoji", 18))
        self.content_emoji_btn.clicked.connect(self.insert_emoji_content)
        tools_layout.addWidget(self.content_emoji_btn)
        
        # Character counter
        self.char_counter = QLabel("0 caracteres")
        self.char_counter.setStyleSheet("color: gray; font-size: 11px;")
        tools_layout.addWidget(self.char_counter)
        
        tools_layout.addStretch()
        content_group_layout.addLayout(tools_layout)
        
        content_group.setLayout(content_group_layout)
        layout.addWidget(content_group)

    def setup_voice_note_section(self, layout):
        """Setup professional voice note section"""
        voice_group = QGroupBox("🎵 Nota de Voz Premium (Opcional)")
        voice_layout = QVBoxLayout()
        
        # Voice quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Calidad:"))
        self.voice_quality_combo = QComboBox()
        for key, setting in self.audio_quality_settings.items():
            self.voice_quality_combo.addItem(setting["name"], key)
        self.voice_quality_combo.setCurrentText("Alta (128k)")
        quality_layout.addWidget(self.voice_quality_combo)
        quality_layout.addStretch()
        voice_layout.addLayout(quality_layout)
        
        # Voice file selection
        voice_file_layout = QHBoxLayout()
        self.voice_select_btn = QPushButton("🎤 Seleccionar Audio")
        self.voice_select_btn.clicked.connect(self.select_voice_file)
        voice_file_layout.addWidget(self.voice_select_btn)
        
        self.voice_file_label = QLabel("Ningún archivo seleccionado")
        self.voice_file_label.setStyleSheet("color: gray; font-style: italic;")
        voice_file_layout.addWidget(self.voice_file_label)
        voice_layout.addLayout(voice_file_layout)
        
        # Voice metadata
        metadata_layout = QFormLayout()
        self.voice_title_edit = QLineEdit()
        self.voice_title_edit.setPlaceholderText("Título del audio (opcional)")
        metadata_layout.addRow("Título:", self.voice_title_edit)
        
        self.voice_description_edit = QTextEdit()
        self.voice_description_edit.setPlaceholderText("Descripción del audio (opcional)")
        self.voice_description_edit.setMaximumHeight(60)
        metadata_layout.addRow("Descripción:", self.voice_description_edit)
        voice_layout.addLayout(metadata_layout)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

    def setup_additional_files_section(self, layout):
        """Setup additional files section"""
        files_group = QGroupBox("📎 Archivos Adicionales (Opcional)")
        files_layout = QVBoxLayout()
        
        # File selection controls
        file_controls = QHBoxLayout()
        self.add_file_btn = QPushButton("📁 Agregar Archivo")
        self.add_file_btn.clicked.connect(self.add_additional_file)
        file_controls.addWidget(self.add_file_btn)
        
        self.clear_files_btn = QPushButton("🗑️ Limpiar")
        self.clear_files_btn.clicked.connect(self.clear_additional_files)
        file_controls.addWidget(self.clear_files_btn)
        file_controls.addStretch()
        files_layout.addLayout(file_controls)
        
        # Files list
        self.files_list_label = QLabel("No hay archivos adicionales")
        self.files_list_label.setStyleSheet("color: gray; font-style: italic;")
        self.files_list_label.setWordWrap(True)
        files_layout.addWidget(self.files_list_label)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

    def setup_cta_hashtags_section(self, layout):
        """Setup CTA and hashtags section"""
        engagement_group = QGroupBox("🎯 Engagement y Hashtags")
        engagement_layout = QVBoxLayout()
        
        # CTA section
        cta_layout = QHBoxLayout()
        cta_layout.addWidget(QLabel("💬 CTA:"))
        self.cta_edit = QLineEdit()
        self.cta_edit.setPlaceholderText("¡Comparte si te gustó! 👍")
        cta_layout.addWidget(self.cta_edit)
        
        self.cta_emoji_btn = QPushButton("😊")
        self.cta_emoji_btn.setFixedWidth(24)
        self.cta_emoji_btn.clicked.connect(self.insert_emoji_cta)
        cta_layout.addWidget(self.cta_emoji_btn)
        engagement_layout.addLayout(cta_layout)
        
        # Hashtags section
        hashtags_layout = QHBoxLayout()
        hashtags_layout.addWidget(QLabel("🏷️ Tags:"))
        self.hashtags_edit = QLineEdit()
        self.hashtags_edit.setPlaceholderText("#viral #trending #content")
        hashtags_layout.addWidget(self.hashtags_edit)
        engagement_layout.addLayout(hashtags_layout)
        
        engagement_group.setLayout(engagement_layout)
        layout.addWidget(engagement_group)

    def setup_publishing_controls(self, layout):
        """Setup publishing controls and progress"""
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_log = QTextEdit()
        self.progress_log.setMaximumHeight(100)
        self.progress_log.setReadOnly(True)
        self.progress_log.setVisible(False)
        self.progress_log.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px;")
        layout.addWidget(self.progress_log)
        
        # Publishing button
        publish_layout = QHBoxLayout()
        publish_layout.addStretch()
        
        self.publish_button = QPushButton("🚀 PUBLICAR EN TELEGRAM")
        self.publish_button.setMinimumHeight(50)
        self.publish_button.setMinimumWidth(200)
        self.publish_button.clicked.connect(self.publish_post)
        publish_layout.addWidget(self.publish_button)
        
        publish_layout.addStretch()
        layout.addLayout(publish_layout)

    def setup_right_preview_section(self, main_layout):
        """Setup right preview section using PostPreviewWidget"""
        if PostPreviewWidget:
            self.post_preview = PostPreviewWidget()
            self.post_preview.setMinimumWidth(350)
            self.post_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Enable image selection from preview
            self.post_preview.image_label.mousePressEvent = self.post_preview_select_media
            
            main_layout.addWidget(self.post_preview, 2)
        else:
            # Fallback preview
            preview_group = QGroupBox("📱 Vista Previa")
            preview_layout = QVBoxLayout()
            
            self.preview_area = QTextEdit()
            self.preview_area.setReadOnly(True)
            self.preview_area.setPlaceholderText("Vista previa del post...")
            preview_layout.addWidget(self.preview_area)
            
            preview_group.setLayout(preview_layout)
            preview_group.setMinimumWidth(350)
            main_layout.addWidget(preview_group, 2)

    def connect_all_events(self):
        """Connect all UI events"""
        self.title_edit.textChanged.connect(self.update_preview)
        self.edit_area.textChanged.connect(self.update_preview)
        self.edit_area.textChanged.connect(self.update_character_counter)
        self.cta_edit.textChanged.connect(self.update_preview)
        self.hashtags_edit.textChanged.connect(self.update_preview)

    # ==================== UI EVENT HANDLERS ====================
    
    def insert_emoji_title(self):
        """Insert emoji into title field"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.title_edit.cursorPosition()
                    text = self.title_edit.text()
                    self.title_edit.setText(text[:cursor] + emoji + text[cursor:])
                    self.title_edit.setCursorPosition(cursor + len(emoji))
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def insert_emoji_content(self):
        """Insert emoji into content area"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.edit_area.textCursor()
                    cursor.insertText(emoji)
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def insert_emoji_cta(self):
        """Insert emoji into CTA field"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.cta_edit.cursorPosition()
                    text = self.cta_edit.text()
                    self.cta_edit.setText(text[:cursor] + emoji + text[cursor:])
                    self.cta_edit.setCursorPosition(cursor + len(emoji))
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def select_presentation_media(self):
        """Select presentation media (image, video, GIF)"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Media",
            "",
            "Todos los medios (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.gif);;Imágenes (*.png *.jpg *.jpeg *.webp *.bmp);;Videos (*.mp4 *.mov *.avi *.mkv);;GIFs (*.gif)"
        )
        if file:
            self.presentation_media_path = file
            ext = file.lower().split('.')[-1]
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                self.presentation_media_type = "photo"
                icon = "📷"
            elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                self.presentation_media_type = "video"
                icon = "🎬"
            elif ext == 'gif':
                self.presentation_media_type = "animation"
                icon = "🎞️"
            else:
                self.presentation_media_type = "document"
                icon = "📎"
            
            filename = os.path.basename(file)
            self.media_status_label.setText(f"{icon} {filename}")
            self.media_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.update_preview()

    def post_preview_select_media(self, event):
        """Select media from preview area click"""
        self.select_presentation_media()

    def select_voice_file(self):
        """Select voice file for premium audio"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Audio Premium",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac *.wma *.aac);;All Files (*)"
        )
        if file:
            self.voice_selected_file = file
            filename = os.path.basename(file)
            file_size = os.path.getsize(file) / (1024 * 1024)  # MB
            self.voice_file_label.setText(f"🎵 {filename} ({file_size:.1f} MB)")
            self.voice_file_label.setStyleSheet("color: green; font-weight: bold;")

    def add_additional_file(self):
        """Add additional file to the post"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo Adicional",
            "",
            "Todos los archivos (*.*);;Imágenes (*.png *.jpg *.jpeg *.webp *.bmp);;Videos (*.mp4 *.mov *.avi *.mkv);;Documentos (*.pdf *.doc *.docx *.txt)"
        )
        if file:
            self.file_upload_widget.add_file(file)
            self.update_files_display()

    def clear_additional_files(self):
        """Clear all additional files"""
        self.file_upload_widget.clear_files()
        self.update_files_display()

    def update_files_display(self):
        """Update the files display"""
        files = self.file_upload_widget.get_files()
        if not files:
            self.files_list_label.setText("No hay archivos adicionales")
            self.files_list_label.setStyleSheet("color: gray; font-style: italic;")
        else:
            file_names = []
            for file_path in files:
                filename = os.path.basename(file_path)
                ext = file_path.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                    icon = "📷"
                elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                    icon = "🎬"
                elif ext == 'gif':
                    icon = "🎞️"
                elif ext in ['pdf', 'doc', 'docx']:
                    icon = "📄"
                else:
                    icon = "📎"
                file_names.append(f"{icon} {filename}")
            
            self.files_list_label.setText("\n".join(file_names))
            self.files_list_label.setStyleSheet("color: black; font-weight: normal;")

    def open_button_config(self):
        """Open button configuration dialog"""
        if ButtonConfigDialog:
            dlg = ButtonConfigDialog(self, self.telegram_buttons)
            if dlg.exec():
                self.telegram_buttons = dlg.get_values()
                self.update_preview()
        else:
            QMessageBox.information(self, "Info", "Configuración de botones no disponible")

    def update_character_counter(self):
        """Update character counter for content"""
        text = self.edit_area.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        
        # Telegram message limit is 4096 characters
        max_chars = 4096
        
        if char_count > max_chars:
            self.char_counter.setText(f"⚠️ {char_count}/{max_chars} caracteres ({word_count} palabras)")
            self.char_counter.setStyleSheet("color: red; font-weight: bold;")
        elif char_count > max_chars * 0.9:
            self.char_counter.setText(f"⚠️ {char_count}/{max_chars} caracteres ({word_count} palabras)")
            self.char_counter.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.char_counter.setText(f"{char_count} caracteres ({word_count} palabras)")
            self.char_counter.setStyleSheet("color: gray; font-size: 11px;")

    def update_preview(self):
        """Update preview using PostPreviewWidget or fallback"""
        title = self.title_edit.text().strip()
        content = self.edit_area.toPlainText().strip()
        cta = self.cta_edit.text().strip()
        hashtags = self.hashtags_edit.text().strip()
        
        # Build preview content
        preview_text = ""
        if title:
            preview_text += f"<b>{title}</b><br><br>"
        
        if content:
            formatted_content = self.format_telegram_post(content)
            preview_text += formatted_content + "<br><br>"
        
        if cta:
            preview_text += f"<b>🎯 {cta}</b><br><br>"
        
        if hashtags:
            preview_text += f"<span style='color: #0088cc;'>{hashtags}</span>"
        
        # Update preview widget
        if PostPreviewWidget and hasattr(self, 'post_preview') and self.post_preview:
            self.post_preview.set_html(preview_text)
            if self.presentation_media_path:
                self.post_preview.set_image(self.presentation_media_path)
            else:
                self.post_preview.set_image(None)
            
            # Set buttons
            if self.telegram_buttons and any(self.telegram_buttons):
                self.post_preview.set_buttons(self.telegram_buttons, "row")
            else:
                self.post_preview.set_buttons([], "row")
        elif hasattr(self, 'preview_area'):
            self.preview_area.setHtml(preview_text)

    def format_telegram_post(self, text):
        """Format text for Telegram preview - borrowed from AI Generator"""
        lines = text.splitlines()
        formatted = []
        in_code_block = False
        
        for line in lines:
            stripped = line.rstrip()
            
            # Detect code blocks with ```
            if stripped.startswith("```"):
                if not in_code_block:
                    formatted.append("<pre>")
                    in_code_block = True
                else:
                    formatted.append("</pre>")
                    in_code_block = False
                continue
            
            # Detect indented lines as code (4 spaces or tab)
            if not in_code_block and (line.startswith("    ") or line.startswith("\t")):
                formatted.append("<pre>")
                in_code_block = True
            
            if in_code_block and not (line.startswith("    ") or line.startswith("\t")) and not stripped.startswith("```"):
                formatted.append("</pre>")
                in_code_block = False
            
            if in_code_block:
                formatted.append(stripped)
                continue
            
            # Title formatting
            if stripped.startswith("Título:") or (stripped.isupper() and len(stripped) > 3):
                title = stripped.replace("Título:", "").strip()
                if title:
                    formatted.append(f"<b>{title}</b>")
                continue
            
            # Subtitle formatting
            if stripped.startswith("Subtítulo:"):
                subtitle = stripped.replace("Subtítulo:", "").strip()
                if subtitle:
                    formatted.append(f"<b>{subtitle}</b>")
                continue
            
            # List formatting
            if stripped.startswith("- ") or stripped.startswith("* "):
                formatted.append(f"• {stripped[2:]}")
                continue
            
            # URL formatting
            if "http://" in stripped or "https://" in stripped:
                url_pattern = r'(https?://\S+)'
                def repl(m):
                    url = m.group(1)
                    return f'<a href="{url}">{url}</a>'
                line = re.sub(url_pattern, repl, stripped)
                formatted.append(line)
                continue
            
            # Empty line
            if not stripped:
                formatted.append("")
                continue
            
            # Normal text
            formatted.append(stripped)
        
        if in_code_block:
            formatted.append("</pre>")
        
        return "<br>".join(formatted)

    # ==================== PUBLISHING LOGIC ====================
    
    def publish_post(self):
        """Professional publishing with detailed progress logging"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Aviso", "Ya hay una publicación en proceso")
            return
        
        # Validate content
        title = self.title_edit.text().strip()
        content = self.edit_area.toPlainText().strip()
        
        if not title and not content:
            QMessageBox.warning(self, "Error", "Debes escribir al menos un título o contenido")
            return
        
        # Validate Telegram configuration
        if not self.config.telegram_token or not self.config.telegram_chat_id:
            QMessageBox.critical(self, "Error", "Configura primero el token y chat ID de Telegram")
            return
        
        # Prepare post data
        post_data = self.prepare_post_data()
        
        # Show progress and disable button
        self.show_progress(True)
        self.publish_button.setEnabled(False)
        
        # Create and start worker
        self.worker = PublishWorker(post_data, self.config)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_publish_finished)
        self.worker.start()

    def prepare_post_data(self):
        """Prepare all post data for publishing"""
        title = self.title_edit.text().strip()
        content = self.edit_area.toPlainText().strip()
        cta = self.cta_edit.text().strip()
        hashtags = self.hashtags_edit.text().strip()
        
        # Main content
        main_content = ""
        if title:
            main_content += f"<b>{title}</b>\n\n"
        if content:
            main_content += content
        
        # CTA and hashtags
        cta_hashtags = ""
        if cta:
            cta_hashtags += f"🎯 {cta}\n\n"
        if hashtags:
            cta_hashtags += hashtags
        
        # Button markup
        reply_markup = None
        if self.telegram_buttons and any(self.telegram_buttons):
            keyboard = []
            for row in self.telegram_buttons:
                row_buttons = []
                for btn in row:
                    if isinstance(btn, dict) and "text" in btn and "url" in btn:
                        row_buttons.append({"text": btn["text"], "url": btn["url"]})
                if row_buttons:
                    keyboard.append(row_buttons)
            if keyboard:
                reply_markup = json.dumps({"inline_keyboard": keyboard})
        
        # Voice data
        voice_data = {}
        if self.voice_selected_file:
            voice_data.update({
                'voice_file': self.voice_selected_file,
                'voice_title': self.voice_title_edit.text().strip(),
                'voice_description': self.voice_description_edit.toPlainText().strip(),
                'voice_quality': self.voice_quality_combo.currentData()
            })
        
        return {
            'main_content': main_content.strip(),
            'presentation_path': self.presentation_media_path,
            'presentation_type': self.presentation_media_type,
            'additional_files': self.file_upload_widget.get_files(),
            'cta_hashtags': cta_hashtags.strip(),
            'reply_markup': reply_markup,
            **voice_data
        }

    def show_progress(self, show):
        """Show/hide progress indicators"""
        self.progress_bar.setVisible(show)
        self.progress_log.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_log.clear()
            self.log_message("🚀 Iniciando publicación...")

    def log_message(self, message):
        """Add message to progress log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        if hasattr(self, 'progress_log'):
            self.progress_log.append(formatted_message)
            # Auto-scroll
            scrollbar = self.progress_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def on_progress(self, message):
        """Handle progress updates"""
        self.log_message(message)

    def on_publish_finished(self, success, message):
        """Handle publishing completion"""
        self.show_progress(False)
        self.publish_button.setEnabled(True)
        
        if success:
            self.log_message("✅ Publicación completada exitosamente")
            QMessageBox.information(self, "✅ Éxito", message)
            self.clear_form_after_success()
        else:
            self.log_message(f"❌ Error en publicación: {message}")
            QMessageBox.critical(self, "❌ Error", message)

    def clear_form_after_success(self):
        """Clear form after successful publishing"""
        reply = QMessageBox.question(
            self, 
            "Limpiar Formulario", 
            "¿Deseas limpiar el formulario para crear un nuevo post?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.title_edit.clear()
            self.edit_area.clear()
            self.cta_edit.clear()
            self.hashtags_edit.clear()
            
            # Clear media
            self.presentation_media_path = None
            self.presentation_media_type = None
            self.media_status_label.setText("Sin media seleccionado")
            self.media_status_label.setStyleSheet("color: gray; font-style: italic;")
            
            # Clear voice
            self.voice_selected_file = None
            self.voice_title_edit.clear()
            self.voice_description_edit.clear()
            self.voice_file_label.setText("Ningún archivo seleccionado")
            self.voice_file_label.setStyleSheet("color: gray; font-style: italic;")
            
            # Clear additional files
            self.file_upload_widget.clear_files()
            self.update_files_display()
            
            # Clear buttons
            self.telegram_buttons = [[]]
            
            # Update preview
            self.update_preview()
