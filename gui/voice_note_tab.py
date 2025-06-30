from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QProgressBar,
    QMessageBox, QGroupBox, QFormLayout, QLineEdit, QTabWidget, QScrollArea, QGridLayout, QComboBox,
    QSpinBox, QCheckBox, QSlider, QFrame, QSplitter, QSizePolicy
)

# Import modern styles system
try:
    from gui.voice_note_premium_styles import VoiceNotePremiumStyles
except ImportError:
    VoiceNotePremiumStyles = None

# Import unified theme system
try:
    from gui.telegram_theme import TelegramTheme
except ImportError:
    TelegramTheme = None
    
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QRect
from PySide6.QtGui import QFont, QPixmap, QIcon, QFontMetrics
import os
import asyncio
import time
from datetime import datetime
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
        # Apply modern premium styles
        self.apply_modern_styles()
        
        self.config = Config()
        self.selected_files = {"voice": None, "photo": None, "video": None}
        self.worker = None
        self.current_size = "medium"  # Para responsive design
        
        # Configurar responsive behavior
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.init_ui()
        
        # Timer para responsive updates
        self.resize_timer = QTimer()
        self.resize_timer.timeout.connect(self.update_responsive_layout)
        self.resize_timer.setSingleShot(True)
    
    def apply_modern_styles(self):
        """Aplicar estilos modernos y responsivos"""
        if VoiceNotePremiumStyles:
            style = VoiceNotePremiumStyles.get_main_styles()
            # Agregar estilos de animación si están disponibles
            try:
                style += VoiceNotePremiumStyles.get_animation_styles()
            except AttributeError:
                pass  # Método no disponible, continuar sin él
            self.setStyleSheet(style)
        elif TelegramTheme:
            TelegramTheme.apply_theme_to_widget(self)
    
    def resizeEvent(self, event):
        """Handle responsive resize"""
        super().resizeEvent(event)
        # Debounce resize events
        self.resize_timer.start(100)
    
    def update_responsive_layout(self):
        """Update layout based on current size"""
        width = self.width()
        
        # Determine size category
        if width < 800:
            new_size = "small"
        elif width < 1200:
            new_size = "medium"
        else:
            new_size = "large"
        
        if new_size != self.current_size:
            self.current_size = new_size
            self.apply_responsive_styles()
    
    def apply_responsive_styles(self):
        """Apply responsive styles based on current size"""
        if VoiceNotePremiumStyles:
            if self.current_size == "small":
                try:
                    additional_style = VoiceNotePremiumStyles.get_responsive_mobile_styles()
                    self.setStyleSheet(self.styleSheet() + additional_style)
                except AttributeError:
                    pass  # Método no disponible, continuar sin él
    
    def init_ui(self):
        # Main scroll area para responsividad
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget principal
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header Premium con animación
        self.create_premium_header(main_layout)
        
        # Tabs para diferentes tipos de contenido
        self.content_tabs = QTabWidget()
        self.content_tabs.setObjectName("premium_tabs")
        
        # Tab 1: Notas de Voz Premium
        voice_tab = self.create_voice_tab()
        self.content_tabs.addTab(voice_tab, "🎵 Notas de Voz Premium")
        
        # Tab 2: Imágenes Premium
        photo_tab = self.create_photo_tab()
        self.content_tabs.addTab(photo_tab, "📷 Imágenes Premium")
        
        # Tab 3: Videos Premium
        video_tab = self.create_video_tab()
        self.content_tabs.addTab(video_tab, "🎬 Videos Premium")
        
        main_layout.addWidget(self.content_tabs)
        
        # Progress y Log
        self.create_progress_section(main_layout)
        
        # Set scroll widget
        scroll_area.setWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
    
    def create_premium_header(self, layout):
        """Crear header premium con efectos visuales"""
        header_frame = QFrame()
        header_frame.setObjectName("premium_header")
        header_frame.setFixedHeight(100)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Título Premium con animación
        title_label = QLabel("👑 CANAL PREMIUM - CONTENT MANAGER")
        title_label.setObjectName("premium_title")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Info del canal
        channel_info = QLabel(f"📢 Canal: {VOICE_DEST_CHANNEL_ID}\n🔒 Contenido Exclusivo Premium")
        channel_info.setObjectName("channel_info")
        channel_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(channel_info)
        
        layout.addWidget(header_frame)
        
        # Añadir animación de entrada
        self.animate_widget_entrance(header_frame)
    
    def animate_widget_entrance(self, widget):
        """Añadir animación de entrada suave"""
        try:
            # Animación de opacidad y escala
            self.opacity_animation = QPropertyAnimation(widget, b"geometry")
            self.opacity_animation.setDuration(800)
            self.opacity_animation.setEasingCurve(QEasingCurve.OutBounce)
            
            # Get current geometry for animation
            start_rect = widget.geometry()
            end_rect = start_rect
            start_rect.setHeight(0)
            
            self.opacity_animation.setStartValue(start_rect)
            self.opacity_animation.setEndValue(end_rect)
            self.opacity_animation.start()
        except:
            pass  # Fallback si no se pueden crear animaciones
    
    def create_voice_tab(self):
        """Crear tab de notas de voz con diseño responsivo"""
        tab = QWidget()
        
        # Scroll area para el contenido del tab
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Configuración de Audio Premium
        config_group = QGroupBox("🎛️ Configuración de Audio Premium")
        config_layout = QGridLayout()
        config_layout.setSpacing(15)
        
        # Selector de calidad con contador de caracteres
        config_layout.addWidget(QLabel("🎚️ Calidad de Audio:"), 0, 0)
        self.audio_quality = QComboBox()
        self.audio_quality.addItems(["Premium (64k)", "Ultra (128k)", "Studio (256k)"])
        self.audio_quality.setMinimumHeight(35)
        config_layout.addWidget(self.audio_quality, 0, 1)
        
        # Duración máxima
        config_layout.addWidget(QLabel("⏱️ Duración Máxima:"), 1, 0)
        self.max_duration = QSpinBox()
        self.max_duration.setRange(30, 3600)
        self.max_duration.setValue(300)
        self.max_duration.setSuffix(" segundos")
        self.max_duration.setMinimumHeight(35)
        config_layout.addWidget(self.max_duration, 1, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Upload de Audio con efectos visuales
        upload_group = QGroupBox("🎵 Subir Audio Premium")
        upload_layout = QVBoxLayout()
        upload_layout.setSpacing(15)
        
        # Área de selección con drag & drop visual
        select_frame = QFrame()
        select_frame.setObjectName("upload_zone")
        select_layout = QVBoxLayout(select_frame)
        
        # Botón de selección premium
        self.voice_select_btn = QPushButton("🎼 Seleccionar Audio Premium")
        self.voice_select_btn.setObjectName("premium_upload")
        self.voice_select_btn.clicked.connect(lambda: self.select_file("voice"))
        self.voice_select_btn.setMinimumHeight(50)
        
        self.voice_file_label = QLabel("📁 Arrastra aquí tu archivo o haz clic para seleccionar")
        self.voice_file_label.setObjectName("file_label")
        self.voice_file_label.setAlignment(Qt.AlignCenter)
        self.voice_file_label.setMinimumHeight(60)
        
        select_layout.addWidget(self.voice_select_btn)
        select_layout.addWidget(self.voice_file_label)
        upload_layout.addWidget(select_frame)
        
        # Título del contenido con contador
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 Título Premium:"))
        self.voice_title_counter = QLabel("0/100")
        self.voice_title_counter.setStyleSheet("color: #888888; font-size: 10px;")
        title_layout.addStretch()
        title_layout.addWidget(self.voice_title_counter)
        upload_layout.addLayout(title_layout)
        
        self.voice_title = QLineEdit()
        self.voice_title.setPlaceholderText("🎵 Título exclusivo para suscriptores premium...")
        self.voice_title.setMinimumHeight(40)
        self.voice_title.textChanged.connect(lambda: self.update_counter(self.voice_title, self.voice_title_counter, 100))
        upload_layout.addWidget(self.voice_title)
        
        # Descripción premium con contador
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.voice_desc_counter = QLabel("0/500")
        self.voice_desc_counter.setStyleSheet("color: #888888; font-size: 10px;")
        desc_layout.addStretch()
        desc_layout.addWidget(self.voice_desc_counter)
        upload_layout.addLayout(desc_layout)
        
        self.voice_description = QTextEdit()
        self.voice_description.setPlaceholderText("📝 Descripción detallada del contenido premium...\n\n💎 Contenido exclusivo para suscriptores\n🔒 Acceso limitado\n⭐ Calidad premium")
        self.voice_description.setMaximumHeight(120)
        self.voice_description.textChanged.connect(lambda: self.update_text_counter(self.voice_description, self.voice_desc_counter, 500))
        upload_layout.addWidget(self.voice_description)
        
        # Botón de envío con efectos
        self.voice_upload_btn = QPushButton("🚀 PUBLICAR EN CANAL PREMIUM")
        self.voice_upload_btn.setObjectName("premium_upload")
        self.voice_upload_btn.clicked.connect(lambda: self.upload_content("voice"))
        self.voice_upload_btn.setEnabled(False)
        self.voice_upload_btn.setMinimumHeight(50)
        upload_layout.addWidget(self.voice_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Set scroll content
        scroll.setWidget(content_widget)
        
        # Tab layout
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
    
    def create_photo_tab(self):
        """Crear tab de imágenes con diseño responsivo"""
        tab = QWidget()
        
        # Scroll area para responsividad
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Upload de Imagen con preview mejorado
        upload_group = QGroupBox("📷 Subir Imagen Premium")
        upload_layout = QVBoxLayout()
        upload_layout.setSpacing(15)
        
        # Área de selección visual
        select_frame = QFrame()
        select_frame.setObjectName("upload_zone")
        select_layout = QVBoxLayout(select_frame)
        
        # Botón de selección
        self.photo_select_btn = QPushButton("🖼️ Seleccionar Imagen Premium")
        self.photo_select_btn.setObjectName("premium_upload")
        self.photo_select_btn.clicked.connect(lambda: self.select_file("photo"))
        self.photo_select_btn.setMinimumHeight(50)
        
        self.photo_file_label = QLabel("📁 Arrastra aquí tu imagen o haz clic para seleccionar")
        self.photo_file_label.setObjectName("file_label")
        self.photo_file_label.setAlignment(Qt.AlignCenter)
        self.photo_file_label.setMinimumHeight(60)
        
        select_layout.addWidget(self.photo_select_btn)
        select_layout.addWidget(self.photo_file_label)
        upload_layout.addWidget(select_frame)
        
        # Preview de imagen mejorado
        preview_frame = QFrame()
        preview_frame.setObjectName("preview_frame")
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_label = QLabel("📸 Vista Previa")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("font-weight: bold; color: #ffd700; padding: 5px;")
        
        self.photo_preview = QLabel()
        self.photo_preview.setObjectName("preview")
        self.photo_preview.setFixedSize(280, 200)
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setText("🖼️\nVista previa de imagen\nse mostrará aquí")
        self.photo_preview.setScaledContents(True)
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.photo_preview, 0, Qt.AlignCenter)
        upload_layout.addWidget(preview_frame)
        
        # Título con contador
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 Título Premium:"))
        self.photo_title_counter = QLabel("0/100")
        self.photo_title_counter.setStyleSheet("color: #888888; font-size: 10px;")
        title_layout.addStretch()
        title_layout.addWidget(self.photo_title_counter)
        upload_layout.addLayout(title_layout)
        
        self.photo_title = QLineEdit()
        self.photo_title.setPlaceholderText("📷 Título exclusivo para la imagen premium...")
        self.photo_title.setMinimumHeight(40)
        self.photo_title.textChanged.connect(lambda: self.update_counter(self.photo_title, self.photo_title_counter, 100))
        upload_layout.addWidget(self.photo_title)
        
        # Descripción con contador
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.photo_desc_counter = QLabel("0/500")
        self.photo_desc_counter.setStyleSheet("color: #888888; font-size: 10px;")
        desc_layout.addStretch()
        desc_layout.addWidget(self.photo_desc_counter)
        upload_layout.addLayout(desc_layout)
        
        self.photo_description = QTextEdit()
        self.photo_description.setPlaceholderText("📝 Descripción de la imagen premium...\n\n📸 Contenido visual exclusivo\n💎 Solo para suscriptores premium")
        self.photo_description.setMaximumHeight(100)
        self.photo_description.textChanged.connect(lambda: self.update_text_counter(self.photo_description, self.photo_desc_counter, 500))
        upload_layout.addWidget(self.photo_description)
        
        # Botón de envío
        self.photo_upload_btn = QPushButton("🚀 PUBLICAR IMAGEN PREMIUM")
        self.photo_upload_btn.setObjectName("premium_upload")
        self.photo_upload_btn.clicked.connect(lambda: self.upload_content("photo"))
        self.photo_upload_btn.setEnabled(False)
        self.photo_upload_btn.setMinimumHeight(50)
        upload_layout.addWidget(self.photo_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Set scroll content
        scroll.setWidget(content_widget)
        
        # Tab layout
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
    
    def create_video_tab(self):
        """Crear tab de videos con diseño responsivo"""
        tab = QWidget()
        
        # Scroll area para responsividad
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Upload de Video
        upload_group = QGroupBox("🎬 Subir Video Premium")
        upload_layout = QVBoxLayout()
        upload_layout.setSpacing(15)
        
        # Área de selección
        select_frame = QFrame()
        select_frame.setObjectName("upload_zone")
        select_layout = QVBoxLayout(select_frame)
        
        self.video_select_btn = QPushButton("🎥 Seleccionar Video Premium")
        self.video_select_btn.setObjectName("premium_upload")
        self.video_select_btn.clicked.connect(lambda: self.select_file("video"))
        self.video_select_btn.setMinimumHeight(50)
        
        self.video_file_label = QLabel("📁 Arrastra aquí tu video o haz clic para seleccionar")
        self.video_file_label.setObjectName("file_label")
        self.video_file_label.setAlignment(Qt.AlignCenter)
        self.video_file_label.setMinimumHeight(60)
        
        select_layout.addWidget(self.video_select_btn)
        select_layout.addWidget(self.video_file_label)
        upload_layout.addWidget(select_frame)
        
        # Configuración de video en grid responsivo
        config_group = QGroupBox("⚙️ Configuración de Video")
        config_layout = QGridLayout()
        config_layout.setSpacing(15)
        
        config_layout.addWidget(QLabel("📐 Resolución máxima:"), 0, 0)
        self.video_resolution = QComboBox()
        self.video_resolution.addItems(["720p", "1080p", "4K"])
        self.video_resolution.setMinimumHeight(35)
        config_layout.addWidget(self.video_resolution, 0, 1)
        
        config_layout.addWidget(QLabel("⏱️ Duración máxima:"), 1, 0)
        self.video_max_duration = QSpinBox()
        self.video_max_duration.setRange(60, 7200)
        self.video_max_duration.setValue(600)
        self.video_max_duration.setSuffix(" segundos")
        self.video_max_duration.setMinimumHeight(35)
        config_layout.addWidget(self.video_max_duration, 1, 1)
        
        config_group.setLayout(config_layout)
        upload_layout.addWidget(config_group)
        
        # Título con contador
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 Título Premium:"))
        self.video_title_counter = QLabel("0/100")
        self.video_title_counter.setStyleSheet("color: #888888; font-size: 10px;")
        title_layout.addStretch()
        title_layout.addWidget(self.video_title_counter)
        upload_layout.addLayout(title_layout)
        
        self.video_title = QLineEdit()
        self.video_title.setPlaceholderText("🎬 Título exclusivo para el video premium...")
        self.video_title.setMinimumHeight(40)
        self.video_title.textChanged.connect(lambda: self.update_counter(self.video_title, self.video_title_counter, 100))
        upload_layout.addWidget(self.video_title)
        
        # Descripción con contador
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("📋 Descripción Premium:"))
        self.video_desc_counter = QLabel("0/500")
        self.video_desc_counter.setStyleSheet("color: #888888; font-size: 10px;")
        desc_layout.addStretch()
        desc_layout.addWidget(self.video_desc_counter)
        upload_layout.addLayout(desc_layout)
        
        self.video_description = QTextEdit()
        self.video_description.setPlaceholderText("📝 Descripción del video premium...\n\n🎬 Contenido audiovisual exclusivo\n💎 Calidad premium\n🔒 Solo para suscriptores")
        self.video_description.setMaximumHeight(100)
        self.video_description.textChanged.connect(lambda: self.update_text_counter(self.video_description, self.video_desc_counter, 500))
        upload_layout.addWidget(self.video_description)
        
        # Botón de envío
        self.video_upload_btn = QPushButton("🚀 PUBLICAR VIDEO PREMIUM")
        self.video_upload_btn.setObjectName("premium_upload")
        self.video_upload_btn.clicked.connect(lambda: self.upload_content("video"))
        self.video_upload_btn.setEnabled(False)
        self.video_upload_btn.setMinimumHeight(50)
        upload_layout.addWidget(self.video_upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Set scroll content
        scroll.setWidget(content_widget)
        
        # Tab layout
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
    
    def create_progress_section(self, layout):
        """Crear sección de progreso y logs mejorada"""
        # Barra de progreso mejorada
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # Log premium con scroll
        log_group = QGroupBox("📊 Log de Actividad Premium")
        log_layout = QVBoxLayout()
        
        # Crear scroll para logs
        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        log_scroll.setMaximumHeight(150)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        
        # Mensajes iniciales mejorados
        self.log_text.append("👑 Content Manager Premium iniciado")
        self.log_text.append("🔒 Conexión al canal premium establecida")
        self.log_text.append("🎨 Interface moderna cargada exitosamente")
        self.log_text.append("✨ Listo para crear contenido viral")
        
        log_scroll.setWidget(self.log_text)
        log_layout.addWidget(log_scroll)
        
        # Botones de control de logs
        log_controls = QHBoxLayout()
        
        clear_log_btn = QPushButton("🧹 Limpiar Log")
        clear_log_btn.clicked.connect(self.clear_log)
        clear_log_btn.setMaximumWidth(120)
        
        export_log_btn = QPushButton("💾 Exportar Log")
        export_log_btn.clicked.connect(self.export_log)
        export_log_btn.setMaximumWidth(120)
        
        log_controls.addWidget(clear_log_btn)
        log_controls.addWidget(export_log_btn)
        log_controls.addStretch()
        
        log_layout.addLayout(log_controls)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
    
    def update_counter(self, input_widget, counter_label, max_chars):
        """Actualizar contador de caracteres para inputs"""
        current_length = len(input_widget.text())
        counter_label.setText(f"{current_length}/{max_chars}")
        
        # Cambiar color según proximidad al límite
        if current_length > max_chars * 0.9:
            counter_label.setStyleSheet("color: #ff6b6b; font-size: 10px; font-weight: bold;")
        elif current_length > max_chars * 0.7:
            counter_label.setStyleSheet("color: #ffd700; font-size: 10px; font-weight: bold;")
        else:
            counter_label.setStyleSheet("color: #888888; font-size: 10px;")
    
    def update_text_counter(self, text_widget, counter_label, max_chars):
        """Actualizar contador de caracteres para text areas"""
        current_length = len(text_widget.toPlainText())
        counter_label.setText(f"{current_length}/{max_chars}")
        
        # Cambiar color según proximidad al límite
        if current_length > max_chars * 0.9:
            counter_label.setStyleSheet("color: #ff6b6b; font-size: 10px; font-weight: bold;")
        elif current_length > max_chars * 0.7:
            counter_label.setStyleSheet("color: #ffd700; font-size: 10px; font-weight: bold;")
        else:
            counter_label.setStyleSheet("color: #888888; font-size: 10px;")
    
    def clear_log(self):
        """Limpiar el log de actividad"""
        self.log_text.clear()
        self.log_text.append("👑 Log limpiado - Content Manager Premium")
        self.log_text.append("✨ Listo para nueva actividad")
    
    def export_log(self):
        """Exportar log a archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Log Premium", 
                f"premium_log_{timestamp}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log_text.append(f"💾 Log exportado a: {os.path.basename(file_path)}")
        except Exception as e:
            self.log_text.append(f"❌ Error al exportar log: {str(e)}")
    
    def select_file(self, media_type):
        """Seleccionar archivos con feedback visual mejorado"""
        if media_type == "voice":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Audio Premium", "",
                "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac *.wma);;All Files (*)"
            )
            if file_path:
                self.selected_files["voice"] = file_path
                file_name = os.path.basename(file_path)
                file_size = self.get_file_size_string(file_path)
                
                self.voice_file_label.setText(f"🎵 {file_name}\n📊 {file_size}")
                self.voice_file_label.setStyleSheet("color: #00ff88; font-weight: bold; background-color: rgba(0, 255, 136, 0.1); border: 2px solid #00ff88; border-radius: 8px; padding: 10px;")
                self.voice_upload_btn.setEnabled(True)
                self.log_text.append(f"🎵 Audio premium seleccionado: {file_name} ({file_size})")
                
                # Animar botón de upload
                self.animate_button(self.voice_upload_btn)
                
        elif media_type == "photo":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Imagen Premium", "",
                "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*)"
            )
            if file_path:
                self.selected_files["photo"] = file_path
                file_name = os.path.basename(file_path)
                file_size = self.get_file_size_string(file_path)
                
                self.photo_file_label.setText(f"📷 {file_name}\n📊 {file_size}")
                self.photo_file_label.setStyleSheet("color: #00ff88; font-weight: bold; background-color: rgba(0, 255, 136, 0.1); border: 2px solid #00ff88; border-radius: 8px; padding: 10px;")
                self.photo_upload_btn.setEnabled(True)
                
                # Mostrar preview mejorado
                self.show_image_preview(file_path)
                
                self.log_text.append(f"📷 Imagen premium seleccionada: {file_name} ({file_size})")
                self.animate_button(self.photo_upload_btn)
                
        elif media_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Video Premium", "",
                "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.webm);;All Files (*)"
            )
            if file_path:
                self.selected_files["video"] = file_path
                file_name = os.path.basename(file_path)
                file_size = self.get_file_size_string(file_path)
                
                self.video_file_label.setText(f"🎬 {file_name}\n📊 {file_size}")
                self.video_file_label.setStyleSheet("color: #00ff88; font-weight: bold; background-color: rgba(0, 255, 136, 0.1); border: 2px solid #00ff88; border-radius: 8px; padding: 10px;")
                self.video_upload_btn.setEnabled(True)
                self.log_text.append(f"🎬 Video premium seleccionado: {file_name} ({file_size})")
                
                self.animate_button(self.video_upload_btn)
    
    def get_file_size_string(self, file_path):
        """Obtener tamaño de archivo en formato legible"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Tamaño desconocido"
    
    def show_image_preview(self, file_path):
        """Mostrar preview de imagen mejorado"""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Escalar manteniendo aspecto
                scaled_pixmap = pixmap.scaled(
                    280, 200, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.photo_preview.setPixmap(scaled_pixmap)
                self.photo_preview.setStyleSheet("border: 2px solid #ffd700; border-radius: 8px; background-color: #16213e;")
            else:
                self.photo_preview.setText("❌\nError al cargar\npreview")
                self.photo_preview.setStyleSheet("border: 2px solid #ff6b6b; border-radius: 8px; color: #ff6b6b;")
        except Exception as e:
            self.photo_preview.setText(f"❌\nError: {str(e)[:20]}...")
            self.photo_preview.setStyleSheet("border: 2px solid #ff6b6b; border-radius: 8px; color: #ff6b6b;")
    
    def animate_button(self, button):
        """Animar botón con efecto de éxito"""
        try:
            # Animación de escala
            self.button_animation = QPropertyAnimation(button, b"geometry")
            self.button_animation.setDuration(300)
            self.button_animation.setEasingCurve(QEasingCurve.OutBounce)
            
            original_geometry = button.geometry()
            expanded_geometry = QRect(
                original_geometry.x() - 5,
                original_geometry.y() - 2,
                original_geometry.width() + 10,
                original_geometry.height() + 4
            )
            
            self.button_animation.setStartValue(original_geometry)
            self.button_animation.setKeyValueAt(0.5, expanded_geometry)
            self.button_animation.setEndValue(original_geometry)
            self.button_animation.start()
        except:
            pass  # Fallback si no se puede animar
    
    def upload_content(self, content_type):
        """Subir contenido con validaciones mejoradas"""
        if not self.selected_files[content_type]:
            QMessageBox.warning(self, "⚠️ Advertencia Premium", f"Por favor selecciona un {content_type} premium")
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
        
        # Validaciones mejoradas
        if not title:
            QMessageBox.warning(
                self, "⚠️ Validación Premium", 
                "Por favor ingresa un título para el contenido premium"
            )
            return
        
        if len(title) > 100:
            QMessageBox.warning(
                self, "⚠️ Validación Premium", 
                "El título no puede exceder 100 caracteres"
            )
            return
        
        if len(description) > 500:
            QMessageBox.warning(
                self, "⚠️ Validación Premium", 
                "La descripción no puede exceder 500 caracteres"
            )
            return
        
        # Crear caption premium mejorado
        caption = f"<b>👑 {title}</b>\n\n"
        if description:
            caption += f"{description}\n\n"
        
        # Añadir footer premium
        caption += "💎 <i>Contenido Premium Exclusivo</i>\n"
        caption += "🔒 <i>Solo para suscriptores premium</i>\n"
        caption += "⭐ <i>Calidad garantizada</i>"
        
        # Verificar tamaño de archivo
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB limit for Telegram
        
        if file_size > max_size:
            QMessageBox.warning(
                self, "⚠️ Archivo muy grande", 
                f"El archivo excede el límite de 50MB.\nTamaño actual: {self.get_file_size_string(file_path)}"
            )
            return
        
        # Mostrar confirmación
        reply = QMessageBox.question(
            self, "🚀 Confirmar Publicación Premium",
            f"¿Estás seguro de publicar este {content_type} premium?\n\n"
            f"📝 Título: {title}\n"
            f"📊 Tamaño: {self.get_file_size_string(file_path)}\n"
            f"📢 Canal: {VOICE_DEST_CHANNEL_ID}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Deshabilitar botones y mostrar progreso
        self.set_upload_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("🚀 Preparando publicación premium...")
        
        # Log inicio
        self.log_text.append(f"🚀 Iniciando publicación de {content_type} premium...")
        self.log_text.append(f"📝 Título: {title}")
        self.log_text.append(f"📊 Tamaño: {self.get_file_size_string(file_path)}")
        
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
        """Controlar estado de botones de upload"""
        self.voice_upload_btn.setEnabled(enabled and bool(self.selected_files["voice"]))
        self.photo_upload_btn.setEnabled(enabled and bool(self.selected_files["photo"]))
        self.video_upload_btn.setEnabled(enabled and bool(self.selected_files["video"]))
    
    def on_progress(self, message):
        """Manejar actualizaciones de progreso"""
        self.log_text.append(message)
        self.progress_bar.setFormat(message)
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_finished(self, success, message):
        """Manejar finalización de upload"""
        self.set_upload_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_text.append(f"✅ {message}")
            self.log_text.append("🎉 Publicación completada exitosamente!")
            
            # Mostrar mensaje de éxito viral
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("🎉 ¡Éxito Premium!")
            msg_box.setText("¡Contenido publicado en el canal premium exitosamente!")
            msg_box.setDetailedText(f"Detalles:\n{message}\n\nEl contenido ya está disponible para tus suscriptores premium.")
            msg_box.setStyleSheet("""
                QMessageBox { 
                    background-color: #1a1a2e; 
                    color: #ffffff; 
                }
                QMessageBox QPushButton {
                    background-color: #ffd700;
                    color: #1a1a2e;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 5px;
                }
            """)
            msg_box.exec()
            
            self.clear_current_form()
        else:
            self.log_text.append(f"❌ Error: {message}")
            
            # Mostrar mensaje de error detallado
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("❌ Error Premium")
            error_msg.setText("Error al publicar contenido premium")
            error_msg.setDetailedText(f"Error detallado:\n{message}\n\nIntenta nuevamente o verifica la configuración.")
            error_msg.setStyleSheet("""
                QMessageBox { 
                    background-color: #1a1a2e; 
                    color: #ffffff; 
                }
                QMessageBox QPushButton {
                    background-color: #ff6b6b;
                    color: #ffffff;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 5px;
                }
            """)
            error_msg.exec()
    
    def clear_current_form(self):
        """Limpiar formularios después del éxito con animaciones"""
        # Limpiar archivos seleccionados
        for key in self.selected_files:
            self.selected_files[key] = None
        
        # Reset UI elements del tab de voz
        self.voice_file_label.setText("📁 Arrastra aquí tu archivo o haz clic para seleccionar")
        self.voice_file_label.setStyleSheet("")  # Reset style
        self.voice_title.clear()
        self.voice_description.clear()
        self.voice_upload_btn.setEnabled(False)
        self.voice_title_counter.setText("0/100")
        self.voice_desc_counter.setText("0/500")
        
        # Reset UI elements del tab de foto
        self.photo_file_label.setText("📁 Arrastra aquí tu imagen o haz clic para seleccionar")
        self.photo_file_label.setStyleSheet("")  # Reset style
        self.photo_title.clear()
        self.photo_description.clear()
        self.photo_upload_btn.setEnabled(False)
        self.photo_preview.clear()
        self.photo_preview.setText("🖼️\nVista previa de imagen\nse mostrará aquí")
        self.photo_preview.setStyleSheet("")  # Reset style
        self.photo_title_counter.setText("0/100")
        self.photo_desc_counter.setText("0/500")
        
        # Reset UI elements del tab de video
        self.video_file_label.setText("📁 Arrastra aquí tu video o haz clic para seleccionar")
        self.video_file_label.setStyleSheet("")  # Reset style
        self.video_title.clear()
        self.video_description.clear()
        self.video_upload_btn.setEnabled(False)
        self.video_title_counter.setText("0/100")
        self.video_desc_counter.setText("0/500")
        
        # Log de limpieza
        self.log_text.append("🧹 Formularios limpiados - Listo para nuevo contenido premium")
        self.log_text.append("✨ Sistema preparado para la próxima publicación viral")