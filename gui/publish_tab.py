from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QSizePolicy, QProgressBar,
    QComboBox, QTabWidget, QFrame, QSpacerItem, QCheckBox, QScrollArea, QGridLayout,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)

# Import unified theme system
try:
    from gui.telegram_theme import TelegramTheme
except ImportError:
    TelegramTheme = None

# Import modern styles
try:
    from gui.modern_styles import ModernStyles
except ImportError:
    ModernStyles = None

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPixmap
import requests
import json
import re
import os
import time

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

class PublishWorker(QThread):
    """Worker para manejar el envío sincronizado paso a paso"""
    progress = Signal(str)  # Mensaje de progreso
    finished = Signal(bool, str)  # Éxito, mensaje final
    
    def __init__(self, post_data, config):
        super().__init__()
        self.post_data = post_data
        self.config = config
        
    def run(self):
        try:
            token = self.config.telegram_token
            chat_id = self.config.telegram_chat_id
            
            # Paso 1: Enviar nota de voz premium si existe
            if self.post_data.get('voice_file'):
                self.progress.emit("🎵 Preparando nota de voz premium...")
                success = self.send_voice_note(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar nota de voz")
                    return
                time.sleep(1)  # Pausa entre envíos
            
            # Paso 2: Enviar presentación principal
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
            
            # Paso 3: Enviar archivos adicionales
            if self.post_data.get('additional_files'):
                self.progress.emit("📎 Enviando archivos adicionales...")
                success = self.send_additional_files(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar archivos")
                    return
                time.sleep(1)
            
            # Paso 4: Enviar CTA y hashtags con botones
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
        try:
            voice_file = self.post_data['voice_file']
            voice_title = self.post_data.get('voice_title', '')
            voice_desc = self.post_data.get('voice_desc', '')
            
            # Convertir a ogg si es necesario
            ext = os.path.splitext(voice_file)[1].lower()
            ogg_path = voice_file
            
            if ext != '.ogg':
                try:
                    from services.voice_notes import convert_mp3_to_ogg
                    ogg_path = voice_file.rsplit('.', 1)[0] + '_premium.ogg'
                    convert_mp3_to_ogg(
                        voice_file, ogg_path,
                        title=voice_title or "Audio Premium",
                        artist="Canal Premium",
                        album="Contenido Exclusivo"
                    )
                except Exception as e:
                    self.progress.emit(f"⚠️ Error al convertir audio: {e}")
                    return False
            
            # Crear caption sin HTML
            caption = ""
            if voice_title:
                caption += f"👑 {voice_title}\n\n"
            if voice_desc:
                caption += f"{voice_desc}\n\n"
            caption += "💎 Contenido Premium Exclusivo 🔒 Solo para suscriptores premium"
            
            # Enviar nota de voz
            with open(ogg_path, "rb") as voice:
                url = f"https://api.telegram.org/bot{token}/sendVoice"
                files = {"voice": voice}
                data = {"chat_id": chat_id, "caption": caption}
                response = requests.post(url, data=data, files=files)
                
            if ogg_path != voice_file and os.path.exists(ogg_path):
                os.remove(ogg_path)
                
            return response.json().get("ok", False)
            
        except Exception as e:
            self.progress.emit(f"❌ Error en nota de voz: {e}")
            return False
    
    def send_presentation(self, token, chat_id):
        try:
            file_path = self.post_data['presentation_path']
            media_type = self.post_data['presentation_type']
            caption = self.post_data.get('main_content', '')
            
            # Limitar caption a 1024 caracteres
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
        try:
            text = self.post_data['main_content']
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            response = requests.post(url, data=data)
            return response.json().get("ok", False)
        except Exception as e:
            self.progress.emit(f"❌ Error en mensaje: {e}")
            return False
    
    def send_additional_files(self, token, chat_id):
        try:
            files = self.post_data['additional_files']
            for file_path in files:
                ext = file_path.lower().split('.')[-1]
                
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                    if not self.send_photo(token, chat_id, file_path, ""):
                        return False
                elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                    if not self.send_video(token, chat_id, file_path, ""):
                        return False
                elif ext == 'gif':
                    if not self.send_animation(token, chat_id, file_path, ""):
                        return False
                else:
                    if not self.send_document(token, chat_id, file_path, ""):
                        return False
                
                time.sleep(0.5)  # Pausa entre archivos
            return True
        except Exception as e:
            self.progress.emit(f"❌ Error en archivos: {e}")
            return False
    
    def send_cta_hashtags(self, token, chat_id):
        try:
            text = self.post_data['cta_hashtags']
            reply_markup = self.post_data.get('reply_markup')
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            
            if reply_markup:
                data["reply_markup"] = reply_markup
                
            response = requests.post(url, data=data)
            return response.json().get("ok", False)
        except Exception as e:
            self.progress.emit(f"❌ Error en CTA: {e}")
            return False
    
    def send_photo(self, token, chat_id, file_path, caption):
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
    def setup_voice_note_section(self, parent_layout):
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QFileDialog
        from gui.emoji_picker import EmojiPicker
        self.voice_note_group = QGroupBox("Notas de Voz Premium")
        layout = QVBoxLayout()

        # Calidad de audio
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Calidad de Audio:")
        self.voice_quality_combo = QComboBox()
        self.voice_quality_combo.addItems(["Premium (64k)", "Ultra (128k)", "Studio (256k)"])
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.voice_quality_combo)
        layout.addLayout(quality_layout)

        # Título con emoji
        title_layout = QHBoxLayout()
        title_label = QLabel("Título:")
        self.voice_title_edit = QLineEdit()
        self.voice_title_edit.setPlaceholderText("Título premium...")
        title_emoji_btn = QPushButton("🛸")
        title_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        def insert_emoji_title():
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.voice_title_edit.cursorPosition()
                    text = self.voice_title_edit.text()
                    self.voice_title_edit.setText(text[:cursor] + emoji + text[cursor:])
                    self.voice_title_edit.setCursorPosition(cursor + len(emoji))
        title_emoji_btn.clicked.connect(insert_emoji_title)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.voice_title_edit)
        title_layout.addWidget(title_emoji_btn)
        layout.addLayout(title_layout)

        # Descripción con emoji
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Descripción:")
        self.voice_desc_edit = QTextEdit()
        self.voice_desc_edit.setPlaceholderText("Descripción premium...")
        desc_emoji_btn = QPushButton("🛸")
        desc_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        def insert_emoji_desc():
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.voice_desc_edit.textCursor()
                    cursor.insertText(emoji)
        desc_emoji_btn.clicked.connect(insert_emoji_desc)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.voice_desc_edit)
        desc_layout.addWidget(desc_emoji_btn)
        layout.addLayout(desc_layout)

        # Selección de archivo
        file_layout = QHBoxLayout()
        self.voice_file_label = QLabel("Ningún archivo seleccionado")
        select_btn = QPushButton("Seleccionar Audio")
        self.voice_selected_file = None
        def select_file():
            file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Audio Premium", "", "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac *.wma);;All Files (*)")
            if file_path:
                self.voice_selected_file = file_path
                self.voice_file_label.setText(f"🎵 {file_path.split('/')[-1]}")
        select_btn.clicked.connect(select_file)
        file_layout.addWidget(select_btn)
        file_layout.addWidget(self.voice_file_label)
        layout.addLayout(file_layout)

        self.voice_note_group.setLayout(layout)
        parent_layout.addWidget(self.voice_note_group)
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.setWindowTitle("✨ Publicar Post Viral")
        self.setObjectName("publish_tab")

        # Variables de estado
        self.presentation_media_path = None
        self.presentation_media_type = None
        self.telegram_buttons = [[]]
        self.worker = None
        self.animations = []

        # Aplicar estilos modernos
        self.setup_modern_ui()
        
        # Configurar responsividad
        self.setup_responsive_layout()
        
        # Aplicar animaciones
        self.setup_animations()

    def setup_modern_ui(self):
        """Configurar UI moderna y atractiva"""
        if ModernStyles:
            # Aplicar estilos modernos
            self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
        # Configurar el layout principal responsivo
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)

        # ========== COLUMNA IZQUIERDA: CREACIÓN ==========
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(20)

        # Selector de tipo de post con estilo viral
        self.setup_viral_post_selector(left_layout)
        
        # Título y presentación con efectos visuales
        self.setup_enhanced_title_section(left_layout)
        
        # Área de edición principal mejorada
        self.setup_enhanced_editing_section(left_layout)
        
        # Progreso y envío con estilo moderno
        self.setup_modern_progress_section(left_layout)

        left_scroll.setWidget(left_widget)
        left_scroll.setMinimumWidth(400)
        left_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(left_scroll, 2)

        # ========== COLUMNA CENTRO: PREVIEW ==========
        self.setup_enhanced_preview_section(main_layout)

        # ========== COLUMNA DERECHA: COMPLEMENTOS ==========
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(20)

        # Archivos adicionales mejorados
        self.file_upload_widget = FileUploadWidget()
        self.add_visual_effects(self.file_upload_widget)
        right_layout.addWidget(self.file_upload_widget)

        # Notas de Voz Premium mejoradas
        self.setup_enhanced_voice_section(right_layout)

        # CTA y Hashtags con estilo viral
        self.setup_viral_cta_section(right_layout)

        right_scroll.setWidget(right_widget)
        right_scroll.setMinimumWidth(350)
        right_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(right_scroll, 2)

        self.setLayout(main_layout)

    def setup_viral_post_selector(self, layout):
        """Selector de tipo de post con diseño viral"""
        type_group = QGroupBox("🚀 Tipo de Post Viral")
        type_group.setObjectName("viral_group")
        type_layout = QVBoxLayout()
        
        # ComboBox con estilos mejorados
        self.post_type_combo = QComboBox()
        self.post_type_combo.addItems([
            "📝 Post Simple - Engagement directo",
            "🎯 Copy Persuasivo - Máxima conversión", 
            "👑 Post Premium - Contenido exclusivo",
            "🔥 Post Viral - Máximo alcance"
        ])
        self.post_type_combo.setObjectName("viral_combo")
        self.post_type_combo.currentIndexChanged.connect(self.on_post_type_changed)
        
        # Descripción del tipo seleccionado
        self.type_description = QLabel("Selecciona el tipo de post para optimizar el engagement")
        self.type_description.setObjectName("subtitle_label")
        self.type_description.setWordWrap(True)
        
        type_layout.addWidget(self.post_type_combo)
        type_layout.addWidget(self.type_description)
        
        type_group.setLayout(type_layout)
        self.add_visual_effects(type_group)
        layout.addWidget(type_group)

    def setup_enhanced_title_section(self, layout):
        """Título y presentación con efectos visuales mejorados"""
        title_group = QGroupBox("✨ Título y Presentación Viral")
        title_layout = QVBoxLayout()
        
        # Título con efectos especiales
        title_container = QFrame()
        title_container_layout = QHBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        
        title_container_layout.addWidget(QLabel("🎯 Título:"))
        
        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("title_edit")
        self.title_edit.setPlaceholderText("Título que capte la atención instantáneamente...")
        title_container_layout.addWidget(self.title_edit, 2)
        
        # Botón emoji con efectos hover
        self.title_emoji_btn = QPushButton("🛸")
        self.title_emoji_btn.setObjectName("emoji_button")
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        self.title_emoji_btn.setToolTip("Agregar emoji viral")
        title_container_layout.addWidget(self.title_emoji_btn)
        
        title_layout.addWidget(title_container)
        
        # Contador de caracteres
        self.title_counter = QLabel("0/100 caracteres")
        self.title_counter.setObjectName("hashtags_display")
        self.title_edit.textChanged.connect(self.update_title_counter)
        title_layout.addWidget(self.title_counter)
        
        # Presentación con preview mejorado
        presentation_container = QFrame()
        presentation_layout = QHBoxLayout(presentation_container)
        
        self.presentation_btn = QPushButton("📸 Seleccionar Media Viral")
        self.presentation_btn.clicked.connect(self.select_presentation_media)
        presentation_layout.addWidget(self.presentation_btn)
        
        self.presentation_label = QLabel("Sin presentación")
        self.presentation_label.setObjectName("subtitle_label")
        presentation_layout.addWidget(self.presentation_label)
        
        title_layout.addWidget(presentation_container)
        
        title_group.setLayout(title_layout)
        self.add_visual_effects(title_group)
        layout.addWidget(title_group)

    def setup_enhanced_editing_section(self, layout):
        """Área de edición principal mejorada"""
        edit_group = QGroupBox("✍️ Contenido Persuasivo")
        edit_layout = QVBoxLayout()
        
        # Área de texto mejorada
        self.edit_area = QTextEdit()
        self.edit_area.setPlaceholderText(
            "💡 Escribe contenido que genere engagement:\n\n"
            "• Usa preguntas que generen respuestas\n"
            "• Incluye call-to-actions claros\n" 
            "• Agrega valor real al lector\n"
            "• Mantén un tono conversacional\n\n"
            "¡Haz que cada palabra cuente! 🚀"
        )
        self.edit_area.setMinimumHeight(200)
        edit_layout.addWidget(self.edit_area)
        
        # Herramientas de edición
        tools_frame = QFrame()
        tools_layout = QHBoxLayout(tools_frame)
        
        # Botones de herramientas con iconos
        self.button_config_btn = QPushButton("🔗 Botones CTA")
        self.button_config_btn.clicked.connect(self.open_button_config)
        tools_layout.addWidget(self.button_config_btn)
        
        self.emoji_btn = QPushButton("🛸")
        self.emoji_btn.setObjectName("emoji_button")
        self.emoji_btn.clicked.connect(self.insert_emoji)
        self.emoji_btn.setToolTip("Emojis virales")
        tools_layout.addWidget(self.emoji_btn)
        
        # Contador de palabras
        self.word_counter = QLabel("0 palabras")
        self.word_counter.setObjectName("hashtags_display")
        self.edit_area.textChanged.connect(self.update_word_counter)
        tools_layout.addWidget(self.word_counter)
        
        tools_layout.addStretch()
        edit_layout.addWidget(tools_frame)
        
        edit_group.setLayout(edit_layout)
        self.add_visual_effects(edit_group)
        layout.addWidget(edit_group, 2)

    def setup_modern_progress_section(self, layout):
        """Progreso y botón de envío moderno"""
        # Espaciador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(8)
        layout.addWidget(self.progress_bar)
        
        # Log de progreso
        self.progress_log = QTextEdit()
        self.progress_log.setObjectName("progress_log")
        self.progress_log.setMaximumHeight(100)
        self.progress_log.setReadOnly(True)
        self.progress_log.setVisible(False)
        layout.addWidget(self.progress_log)
        
        # Botón de envío viral
        publish_container = QFrame()
        publish_layout = QHBoxLayout(publish_container)
        publish_layout.addStretch()
        
        self.publish_button = QPushButton("🚀 PUBLICAR POST VIRAL")
        self.publish_button.setObjectName("publish_button")
        self.publish_button.setMinimumHeight(60)
        self.publish_button.setMinimumWidth(250)
        self.publish_button.clicked.connect(self.publish_post)
        
        publish_layout.addWidget(self.publish_button)
        publish_layout.addStretch()
        
        layout.addWidget(publish_container)

    def setup_post_type_selector(self, layout):
        """Selector de tipo de post"""
        type_group = QGroupBox("🎯 Tipo de Post")
        type_layout = QVBoxLayout()
        
        self.post_type_combo = QComboBox()
        self.post_type_combo.addItems([
            "📝 Post Simple - Solo texto/imagen",
            "🎯 Copy Persuasivo - Con botones y CTA",
            "👑 Post Premium - Con nota de voz"
        ])
        self.post_type_combo.currentIndexChanged.connect(self.on_post_type_changed)
        type_layout.addWidget(self.post_type_combo)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

    def setup_title_presentation_section(self, layout):
        """Título y presentación"""
        title_group = QGroupBox("🎨 Título y Presentación")
        title_layout = QVBoxLayout()
        
        # Título
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Título:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título del post")
        title_row.addWidget(self.title_edit, 2)
        
        # Botón de emoji para título
        self.title_emoji_btn = QPushButton("🛸")
        self.title_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        title_row.addWidget(self.title_emoji_btn)
        
        title_layout.addLayout(title_row)
        
        # Presentación
        presentation_row = QHBoxLayout()
        self.presentation_btn = QPushButton("📷 Seleccionar Presentación")
        self.presentation_btn.clicked.connect(self.select_presentation_media)
        presentation_row.addWidget(self.presentation_btn)
        
        self.presentation_label = QLabel("Ninguna presentación")
        presentation_row.addWidget(self.presentation_label)
        title_layout.addLayout(presentation_row)
        
        title_group.setLayout(title_layout)
        layout.addWidget(title_group)

    def setup_main_editing_section(self, layout):
        """Área de edición principal"""
        edit_group = QGroupBox("✍️ Contenido Principal")
        edit_layout = QVBoxLayout()
        
        self.edit_area = QTextEdit()
        self.edit_area.setPlaceholderText("Escribe aquí el contenido principal del post...")
        edit_layout.addWidget(self.edit_area)
        
        # Botones de herramientas
        tools_row = QHBoxLayout()
        
        self.button_config_btn = QPushButton("🔗 Agregar Botones")
        self.button_config_btn.clicked.connect(self.open_button_config)
        tools_row.addWidget(self.button_config_btn)
        
        self.emoji_btn = QPushButton("🛸")
        self.emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.emoji_btn.clicked.connect(self.insert_emoji)
        tools_row.addWidget(self.emoji_btn)
        
        tools_row.addStretch()
        edit_layout.addLayout(tools_row)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group, 2)

    def setup_progress_and_send_section(self, layout):
        """Progreso y botón de envío"""
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log de progreso
        self.progress_log = QTextEdit()
        self.progress_log.setMaximumHeight(80)
        self.progress_log.setReadOnly(True)
        self.progress_log.setVisible(False)
        layout.addWidget(self.progress_log)
        
        # Botón de envío
        send_layout = QHBoxLayout()
        send_layout.addStretch()
        
        self.publish_button = QPushButton("🚀 PUBLICAR POST")
        self.publish_button.setMinimumHeight(50)
        self.publish_button.setStyleSheet("""
            QPushButton {
                background: #0088cc;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #006699;
            }
            QPushButton:disabled {
                background: #555;
                color: #999;
            }
        """)
        self.publish_button.clicked.connect(self.publish_post)
        send_layout.addWidget(self.publish_button)
        
        layout.addLayout(send_layout)

    def setup_cta_hashtags_section(self, layout):
        """CTA y Hashtags mejorados"""
        cta_group = QGroupBox("🎯 Llamada a la Acción")
        cta_layout = QVBoxLayout()
        
        # CTA
        cta_row = QHBoxLayout()
        self.cta_widget = CallToActionWidget()
        cta_row.addWidget(self.cta_widget)
        
        self.cta_emoji_btn = QPushButton("🛸")
        self.cta_emoji_btn.setStyleSheet(EMOJI_BTN_STYLE)
        self.cta_emoji_btn.clicked.connect(self.insert_emoji_cta)
        cta_row.addWidget(self.cta_emoji_btn)
        cta_layout.addLayout(cta_row)
        
        # Hashtags
        hashtags_row = QHBoxLayout()
        self.hashtag_widget = HashtagSuggesterWidget()
        hashtags_row.addWidget(self.hashtag_widget)
        cta_layout.addLayout(hashtags_row)
        
        # Mostrar hashtags
        self.hashtags_display = QLabel("Hashtags: Ninguno")
        self.hashtags_display.setWordWrap(True)
        self.hashtags_display.setStyleSheet("color: #0088cc; font-size: 12px;")
        cta_layout.addWidget(self.hashtags_display)
        
        cta_group.setLayout(cta_layout)
        layout.addWidget(cta_group)

    def connect_events(self):
        """Conectar todos los eventos"""
        self.edit_area.textChanged.connect(self.update_preview)
        self.title_edit.textChanged.connect(self.update_preview)
        self.cta_widget.cta_edit.textChanged.connect(self.update_preview)
        self.hashtag_widget.hashtags_edit.textChanged.connect(self.update_hashtags_display)
        self.post_preview.image_label.mousePressEvent = self.post_preview_select_media

    def update_hashtags_display(self):
        """Actualizar la visualización de hashtags"""
        hashtags = self.hashtag_widget.get_hashtags()
        if hashtags:
            self.hashtags_display.setText(f"Hashtags: {hashtags}")
        else:
            self.hashtags_display.setText("Hashtags: Ninguno")
        self.update_preview()

    def on_post_type_changed(self):
        """Cambiar configuración según tipo de post"""
        index = self.post_type_combo.currentIndex()
        
        descriptions = [
            "Post simple y directo - Enfoque en engagement inmediato",
            "Copy persuasivo - Optimizado para máxima conversión y ventas", 
            "Post premium - Contenido exclusivo con audio y botones avanzados",
            "Post viral - Diseñado para máximo alcance y viralización"
        ]
        
        # Actualizar descripción
        if hasattr(self, 'type_description'):
            self.type_description.setText(descriptions[index])
        
        if index == 0:  # Post Simple
            if hasattr(self, 'button_config_btn'):
                self.button_config_btn.setVisible(False)
            if hasattr(self, 'voice_note_group'):
                self.voice_note_group.setVisible(False)
        elif index == 1:  # Copy Persuasivo
            if hasattr(self, 'button_config_btn'):
                self.button_config_btn.setVisible(True)
            if hasattr(self, 'voice_note_group'):
                self.voice_note_group.setVisible(False)
        elif index == 2:  # Post Premium
            if hasattr(self, 'button_config_btn'):
                self.button_config_btn.setVisible(True)
            if hasattr(self, 'voice_note_group'):
                self.voice_note_group.setVisible(True)
        elif index == 3:  # Post Viral
            if hasattr(self, 'button_config_btn'):
                self.button_config_btn.setVisible(True)
            if hasattr(self, 'voice_note_group'):
                self.voice_note_group.setVisible(False)
        
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

    def select_presentation_media(self):
        """Seleccionar media de presentación mejorado"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar presentación",
            "",
            "Todos los medios (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.gif);;Imágenes (*.png *.jpg *.jpeg *.webp *.bmp);;Videos (*.mp4 *.mov *.avi *.mkv);;GIFs (*.gif)"
        )
        if file:
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
                self.presentation_media_type = None
                icon = "📎"
            
            self.presentation_media_path = file
            filename = os.path.basename(file)
            self.presentation_label.setText(f"{icon} {filename}")
            self.update_preview()

    def post_preview_select_media(self, event):
        """Seleccionar media desde el preview"""
        self.select_presentation_media()

    def update_preview(self):
        """Actualizar previsualización mejorada"""
        title = self.title_edit.text().strip()
        text = self.edit_area.toPlainText()
        cta = self.cta_widget.get_call_to_action()
        hashtags = self.hashtag_widget.get_hashtags()
        files = self.file_upload_widget.get_files()

        # Estructura del preview
        preview_html = ""
        
        # 1. Presentación
        if self.presentation_media_path and self.presentation_media_type == "photo":
            self.post_preview.set_image(self.presentation_media_path)
        else:
            self.post_preview.set_image(None)
            
        # 2. Título
        if title:
            preview_html += f"<b>{title}</b><br><br>"
            
        # 3. Contenido principal
        if text:
            preview_html += self.format_telegram_post(text) + "<br><br>"
            
        # 4. Archivos adicionales
        if files:
            preview_html += "<b>📎 Archivos adicionales:</b><br>"
            for f in files:
                filename = os.path.basename(f)
                ext = f.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                    icon = "📷"
                elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                    icon = "🎬"
                elif ext == 'gif':
                    icon = "🎞️"
                else:
                    icon = "📎"
                preview_html += f"{icon} {filename}<br>"
            preview_html += "<br>"
            
        # 5. CTA
        if cta:
            preview_html += f"<b>🎯 {cta}</b><br><br>"
            
        # 6. Hashtags
        if hashtags:
            preview_html += f"<span style='color: #0088cc;'>{hashtags}</span><br>"
            
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

    def publish_post(self):
        """Publicar post con sistema robusto paso a paso"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Aviso", "Ya hay una publicación en proceso")
            return
            
        # Validar contenido mínimo
        if not self.title_edit.text().strip() and not self.edit_area.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Debes escribir al menos un título o contenido")
            return
            
        # Preparar datos del post
        post_data = self.prepare_post_data()
        
        # Mostrar progreso
        self.show_progress(True)
        self.publish_button.setEnabled(False)
        
        # Crear y ejecutar worker
        self.worker = PublishWorker(post_data, self.config)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_publish_finished)
        self.worker.start()

    def prepare_post_data(self):
        """Preparar todos los datos del post"""
        title = self.title_edit.text().strip()
        text = self.edit_area.toPlainText().strip()
        cta = self.cta_widget.get_call_to_action()
        hashtags = self.hashtag_widget.get_hashtags()
        files = self.file_upload_widget.get_files()
        
        # Contenido principal
        main_content = ""
        if title:
            main_content += f"<b>{title}</b>\n\n"
        main_content += text
        
        # CTA y hashtags
        cta_hashtags = ""
        if cta:
            cta_hashtags += f"🎯 {cta}\n\n"
        if hashtags:
            cta_hashtags += hashtags
            
        # Reply markup para botones
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
        
        # Datos de nota de voz
        voice_data = {}
        if hasattr(self, 'voice_selected_file') and self.voice_selected_file:
            voice_data['voice_file'] = self.voice_selected_file
            voice_data['voice_title'] = self.voice_title_edit.text().strip() if hasattr(self, 'voice_title_edit') else ""
            voice_data['voice_desc'] = self.voice_desc_edit.toPlainText().strip() if hasattr(self, 'voice_desc_edit') else ""
        
        return {
            'main_content': main_content,
            'presentation_path': self.presentation_media_path,
            'presentation_type': self.presentation_media_type,
            'additional_files': files,
            'cta_hashtags': cta_hashtags.strip(),
            'reply_markup': reply_markup,
            **voice_data
        }

    def show_progress(self, show):
        """Mostrar/ocultar progreso"""
        self.progress_bar.setVisible(show)
        self.progress_log.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminado
            self.progress_log.clear()

    def on_progress(self, message):
        """Manejar progreso"""
        self.progress_log.append(message)
        # Auto-scroll
        scrollbar = self.progress_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_publish_finished(self, success, message):
        """Manejar finalización"""
        self.show_progress(False)
        self.publish_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "✅ Éxito", message)
            self.clear_form_after_success()
        else:
            QMessageBox.critical(self, "❌ Error", message)

    def clear_form_after_success(self):
        """Limpiar formulario después del éxito"""
        if QMessageBox.question(self, "Limpiar", "¿Deseas limpiar el formulario?") == QMessageBox.StandardButton.Yes:
            self.title_edit.clear()
            self.edit_area.clear()
            self.presentation_media_path = None
            self.presentation_media_type = None
            self.presentation_label.setText("Ninguna presentación")
            
            # Limpiar nota de voz
            if hasattr(self, 'voice_selected_file'):
                self.voice_selected_file = None
                if hasattr(self, 'voice_file_label'):
                    self.voice_file_label.setText("Ningún archivo seleccionado")
                if hasattr(self, 'voice_title_edit'):
                    self.voice_title_edit.clear()
                if hasattr(self, 'voice_desc_edit'):
                    self.voice_desc_edit.clear()
            
            # Limpiar CTA
            if hasattr(self.cta_widget, 'clear_cta'):
                self.cta_widget.clear_cta()
            else:
                self.cta_widget.cta_edit.clear()
            
            # Limpiar hashtags
            if hasattr(self.hashtag_widget, 'clear_hashtags'):
                self.hashtag_widget.clear_hashtags()
            else:
                self.hashtag_widget.hashtags_edit.clear()
            
            # Limpiar archivos
            self.file_upload_widget.clear_files()
            
            # Limpiar botones
            self.telegram_buttons = [[]]
            
            self.update_preview()
            self.update_hashtags_display()

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
        """Abrir configuración de botones"""
        dlg = ButtonConfigDialog(self, self.telegram_buttons)
        if dlg.exec():
            self.telegram_buttons = dlg.get_values()
            self.update_preview()