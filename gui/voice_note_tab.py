from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QFileDialog, QProgressBar,
                               QMessageBox, QGroupBox, QFormLayout, QLineEdit,
                               QTabWidget, QScrollArea, QGridLayout, QComboBox,
                               QSpinBox, QCheckBox, QSlider, QFrame, QSplitter)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon
import os
import asyncio
from services.voice_notes import convert_mp3_to_ogg, send_voice_note
from services.config_voice import VOICE_DEST_CHANNEL_ID
from telegram import Bot
from core.config import Config

class MediaUploadWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, file_path, caption, title, bot_token, channel_id, media_type="voice"):
        super().__init__()
        self.file_path = file_path
        self.caption = caption
        self.title = title
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.media_type = media_type
    
    def run(self):
        try:
            bot = Bot(token=self.bot_token)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.media_type == "voice":
                self.progress.emit("🎵 Iniciando conversión de audio...")
                
                file_name = os.path.basename(self.file_path)
                # Usar el título como nombre base si existe
                base_name = self.title if self.title else file_name.split('.')[0]
                temp_ogg = f"temp_{base_name.replace(' ', '_')}.ogg"
                
                self.progress.emit("🔄 Convirtiendo a formato de nota de voz...")
                self.progress.emit("📝 Agregando metadata personalizada...")
                
                # Llamar a convert_mp3_to_ogg con metadata
                convert_mp3_to_ogg(
                    self.file_path, 
                    temp_ogg,
                    title=self.title if self.title else "Audio Premium",
                    artist="Canal Premium",
                    album="Contenido Exclusivo"
                )
                
                self.progress.emit("📤 Enviando nota de voz al canal premium...")
                loop.run_until_complete(
                    send_voice_note(bot, self.channel_id, temp_ogg, self.caption, self.title)
                )
                
                if os.path.exists(temp_ogg):
                    os.remove(temp_ogg)
                    
            elif self.media_type == "photo":
                self.progress.emit("📷 Enviando imagen al canal premium...")
                with open(self.file_path, "rb") as photo:
                    loop.run_until_complete(
                        bot.send_photo(
                            chat_id=self.channel_id,
                            photo=photo,
                            caption=self.caption,
                            parse_mode="HTML"
                        )
                    )
                    
            elif self.media_type == "video":
                self.progress.emit("🎬 Enviando video al canal premium...")
                with open(self.file_path, "rb") as video:
                    loop.run_until_complete(
                        bot.send_video(
                            chat_id=self.channel_id,
                            video=video,
                            caption=self.caption,
                            parse_mode="HTML"
                        )
                    )
            
            loop.close()
            self.progress.emit("✅ ¡Contenido enviado exitosamente al canal premium!")
            self.finished.emit(True, f"{self.media_type.capitalize()} enviado al canal premium")
            
        except Exception as e:
            self.progress.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False, str(e))

class VoiceNoteTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.selected_files = {"voice": None, "photo": None, "video": None}
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Header Premium
        self.create_premium_header(main_layout)
        
        # Tabs para diferentes tipos de contenido
        content_tabs = QTabWidget()
        
        # Tab 1: Notas de Voz Premium
        voice_tab = self.create_voice_tab()
        content_tabs.addTab(voice_tab, "🎵 Notas de Voz Premium")
        
        # Tab 2: Imágenes Premium
        photo_tab = self.create_photo_tab()
        content_tabs.addTab(photo_tab, "📷 Imágenes Premium")
        
        # Tab 3: Videos Premium
        video_tab = self.create_video_tab()
        content_tabs.addTab(video_tab, "🎬 Videos Premium")
        
        main_layout.addWidget(content_tabs)
        
        # Progress y Log
        self.create_progress_section(main_layout)
        
        self.setLayout(main_layout)
    
    def create_premium_header(self, layout):
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        
        # Título Premium
        title_label = QLabel("👑 CANAL PREMIUM - CONTENT MANAGER")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Info del canal
        channel_info = QLabel(f"📢 Canal: {VOICE_DEST_CHANNEL_ID}\n🔒 Contenido Exclusivo Premium")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(channel_info)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
    
    def create_voice_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Configuración de Audio Premium
        config_group = QGroupBox("🎛️ Configuración de Audio Premium")
        config_layout = QGridLayout()
        
        # Selector de calidad
        config_layout.addWidget(QLabel("🎚️ Calidad de Audio:"), 0, 0)
        self.audio_quality = QComboBox()
        self.audio_quality.addItems(["Premium (64k)", "Ultra (128k)", "Studio (256k)"])
        config_layout.addWidget(self.audio_quality, 0, 1)
        
        # Duración máxima
        config_layout.addWidget(QLabel("⏱️ Duración Máxima:"), 1, 0)
        self.max_duration = QSpinBox()
        self.max_duration.setRange(30, 3600)
        self.max_duration.setValue(300)
        self.max_duration.setSuffix(" segundos")
        config_layout.addWidget(self.max_duration, 1, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Upload de Audio
        upload_group = QGroupBox("🎵 Subir Audio Premium")
        upload_layout = QVBoxLayout()
        
        # Botón de selección
        select_layout = QHBoxLayout()
        self.voice_select_btn = QPushButton("🎼 Seleccionar Audio Premium")
        self.voice_select_btn.clicked.connect(lambda: self.select_file("voice"))
        
        self.voice_file_label = QLabel("Ningún archivo seleccionado")
        
        select_layout.addWidget(self.voice_select_btn)
        select_layout.addWidget(self.voice_file_label)
        upload_layout.addLayout(select_layout)
        
        # Título del contenido
        upload_layout.addWidget(QLabel("📝 Título Premium:"))
        self.voice_title = QLineEdit()
        self.voice_title.setPlaceholderText("Título exclusivo para suscriptores premium...")
        upload_layout.addWidget(self.voice_title)
        
        # Descripción premium
        upload_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.voice_description = QTextEdit()
        self.voice_description.setPlaceholderText("Descripción detallada del contenido premium...\n\n💎 Contenido exclusivo para suscriptores\n🔒 Acceso limitado\n⭐ Calidad premium")
        self.voice_description.setMaximumHeight(120)
        upload_layout.addWidget(self.voice_description)
        
        # Botón de envío
        self.voice_upload_btn = QPushButton("🚀 PUBLICAR EN CANAL PREMIUM")
        self.voice_upload_btn.clicked.connect(lambda: self.upload_content("voice"))
        self.voice_upload_btn.setEnabled(False)
        upload_layout.addWidget(self.voice_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_photo_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Upload de Imagen
        upload_group = QGroupBox("📷 Subir Imagen Premium")
        upload_layout = QVBoxLayout()
        
        # Selección de imagen
        select_layout = QHBoxLayout()
        self.photo_select_btn = QPushButton("🖼️ Seleccionar Imagen Premium")
        self.photo_select_btn.clicked.connect(lambda: self.select_file("photo"))
        
        self.photo_file_label = QLabel("Ninguna imagen seleccionada")
        
        select_layout.addWidget(self.photo_select_btn)
        select_layout.addWidget(self.photo_file_label)
        upload_layout.addLayout(select_layout)
        
        # Preview de imagen
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(200, 200)
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setText("Vista previa\nde imagen")
        upload_layout.addWidget(self.photo_preview)
        
        # Título
        upload_layout.addWidget(QLabel("📝 Título Premium:"))
        self.photo_title = QLineEdit()
        self.photo_title.setPlaceholderText("Título exclusivo para la imagen premium...")
        upload_layout.addWidget(self.photo_title)
        
        # Descripción
        upload_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.photo_description = QTextEdit()
        self.photo_description.setPlaceholderText("Descripción de la imagen premium...\n\n📸 Contenido visual exclusivo\n💎 Solo para suscriptores premium")
        self.photo_description.setMaximumHeight(100)
        upload_layout.addWidget(self.photo_description)
        
        # Botón de envío
        self.photo_upload_btn = QPushButton("🚀 PUBLICAR IMAGEN PREMIUM")
        self.photo_upload_btn.clicked.connect(lambda: self.upload_content("photo"))
        self.photo_upload_btn.setEnabled(False)
        upload_layout.addWidget(self.photo_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_video_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Upload de Video
        upload_group = QGroupBox("🎬 Subir Video Premium")
        upload_layout = QVBoxLayout()
        
        # Selección de video
        select_layout = QHBoxLayout()
        self.video_select_btn = QPushButton("🎥 Seleccionar Video Premium")
        self.video_select_btn.clicked.connect(lambda: self.select_file("video"))
        
        self.video_file_label = QLabel("Ningún video seleccionado")
        
        select_layout.addWidget(self.video_select_btn)
        select_layout.addWidget(self.video_file_label)
        upload_layout.addLayout(select_layout)
        
        # Configuración de video
        config_layout = QGridLayout()
        config_layout.addWidget(QLabel("📐 Resolución máxima:"), 0, 0)
        self.video_resolution = QComboBox()
        self.video_resolution.addItems(["720p", "1080p", "4K"])
        config_layout.addWidget(self.video_resolution, 0, 1)
        
        config_layout.addWidget(QLabel("⏱️ Duración máxima:"), 1, 0)
        self.video_max_duration = QSpinBox()
        self.video_max_duration.setRange(60, 7200)
        self.video_max_duration.setValue(600)
        self.video_max_duration.setSuffix(" segundos")
        config_layout.addWidget(self.video_max_duration, 1, 1)
        
        upload_layout.addLayout(config_layout)
        
        # Título
        upload_layout.addWidget(QLabel("📝 Título Premium:"))
        self.video_title = QLineEdit()
        self.video_title.setPlaceholderText("Título exclusivo para el video premium...")
        upload_layout.addWidget(self.video_title)
        
        # Descripción
        upload_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.video_description = QTextEdit()
        self.video_description.setPlaceholderText("Descripción del video premium...\n\n🎬 Contenido audiovisual exclusivo\n💎 Calidad premium\n🔒 Solo para suscriptores")
        self.video_description.setMaximumHeight(100)
        upload_layout.addWidget(self.video_description)
        
        # Botón de envío
        self.video_upload_btn = QPushButton("🚀 PUBLICAR VIDEO PREMIUM")
        self.video_upload_btn.clicked.connect(lambda: self.upload_content("video"))
        self.video_upload_btn.setEnabled(False)
        upload_layout.addWidget(self.video_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_progress_section(self, layout):
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log premium
        log_group = QGroupBox("📊 Log de Actividad Premium")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        self.log_text.append("👑 Content Manager Premium iniciado")
        self.log_text.append("🔒 Conexión al canal premium establecida")
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
    
    def select_file(self, media_type):
        if media_type == "voice":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Audio Premium", "",
                "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac *.wma);;All Files (*)"
            )
            if file_path:
                self.selected_files["voice"] = file_path
                self.voice_file_label.setText(f"🎵 {os.path.basename(file_path)}")
                self.voice_upload_btn.setEnabled(True)
                self.log_text.append(f"🎵 Audio premium seleccionado: {os.path.basename(file_path)}")
                
        elif media_type == "photo":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Imagen Premium", "",
                "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
            )
            if file_path:
                self.selected_files["photo"] = file_path
                self.photo_file_label.setText(f"📷 {os.path.basename(file_path)}")
                self.photo_upload_btn.setEnabled(True)
                
                # Mostrar preview
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.photo_preview.setPixmap(scaled_pixmap)
                
                self.log_text.append(f"📷 Imagen premium seleccionada: {os.path.basename(file_path)}")
                
        elif media_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Video Premium", "",
                "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
            )
            if file_path:
                self.selected_files["video"] = file_path
                self.video_file_label.setText(f"🎬 {os.path.basename(file_path)}")
                self.video_upload_btn.setEnabled(True)
                self.log_text.append(f"🎬 Video premium seleccionado: {os.path.basename(file_path)}")
    
    def upload_content(self, content_type):
        if not self.selected_files[content_type]:
            QMessageBox.warning(self, "Advertencia", f"Por favor selecciona un {content_type}")
            return
        
        # Obtener datos según el tipo
        if content_type == "voice":
            title = self.voice_title.text().strip()
            description = self.voice_description.toPlainText().strip()
            file_path = self.selected_files["voice"]
        elif content_type == "photo":
            title = self.photo_title.text().strip()
            description = self.photo_description.toPlainText().strip()
            file_path = self.selected_files["photo"]
        elif content_type == "video":
            title = self.video_title.text().strip()
            description = self.video_description.toPlainText().strip()
            file_path = self.selected_files["video"]
        
        # Crear caption premium
        caption = ""
        if title:
            caption += f"<b>👑 {title}</b>\n\n"
        if description:
            caption += f"{description}\n\n"
        caption += f"💎 <i>Contenido Premium Exclusivo</i>\n🔒 <i>Solo para suscriptores premium</i>"
        
        # Deshabilitar botones
        self.set_upload_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Crear worker
        self.worker = MediaUploadWorker(
            file_path, caption, title,
            self.config.telegram_token,
            VOICE_DEST_CHANNEL_ID,
            content_type
        )
        
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def set_upload_buttons_enabled(self, enabled):
        self.voice_upload_btn.setEnabled(enabled and bool(self.selected_files["voice"]))
        self.photo_upload_btn.setEnabled(enabled and bool(self.selected_files["photo"]))
        self.video_upload_btn.setEnabled(enabled and bool(self.selected_files["video"]))
    
    def on_progress(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def on_finished(self, success, message):
        self.set_upload_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_text.append(f"✅ {message}")
            QMessageBox.information(self, "Éxito Premium", "Contenido publicado en el canal premium exitosamente!")
            self.clear_current_form()
        else:
            self.log_text.append(f"❌ Error: {message}")
            QMessageBox.critical(self, "Error Premium", f"Error al publicar contenido:\n{message}")
    
    def clear_current_form(self):
        # Limpiar formularios después del éxito
        for key in self.selected_files:
            self.selected_files[key] = None
        
        # Reset UI elements
        self.voice_file_label.setText("Ningún archivo seleccionado")
        self.voice_title.clear()
        self.voice_description.clear()
        self.voice_upload_btn.setEnabled(False)
        
        self.photo_file_label.setText("Ninguna imagen seleccionada")
        self.photo_title.clear()
        self.photo_description.clear()
        self.photo_upload_btn.setEnabled(False)
        self.photo_preview.clear()
        self.photo_preview.setText("Vista previa\nde imagen")
        
        self.video_file_label.setText("Ningún video seleccionado")
        self.video_title.clear()
        self.video_description.clear()
        self.video_upload_btn.setEnabled(False)