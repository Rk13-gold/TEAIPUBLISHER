from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QSizePolicy, QComboBox,
    QSpinBox, QCheckBox, QProgressBar, QScrollArea, QFrame
)

# Import unified theme system
try:
    from gui.telegram_theme_simple import TelegramThemeSimple as TelegramTheme
except ImportError:
    TelegramTheme = None

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
import os
import json
from pathlib import Path

from gui.emoji_picker import EmojiPicker
from gui.button_config_dialog import ButtonConfigDialog

# Theme system - using unified theme instead of custom styles

class PremiumContentTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.setWindowTitle("Contenido Premium")

        # Variables para archivos
        self.media_file_path = None  # Imagen/video/gif
        self.audio_file_path = None  # Archivo de audio
        self.media_type = None  # "photo", "video", "animation"
        self.telegram_buttons = [[]]

        self.init_ui()
        
        # Apply optimized theme AFTER UI is created
        if TelegramTheme:
            TelegramTheme.apply_simple_theme(self)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --------- ENCABEZADO COMPACTO ---------
        header_layout = QHBoxLayout()
        
        # Título Premium
        title_label = QLabel("TÍTULO PREMIUM:")
        title_label.setMinimumWidth(100)
        title_label.setMaximumWidth(100)
        header_layout.addWidget(title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título exclusivo para suscriptores premium...")
        self.title_edit.textChanged.connect(self.update_preview)
        self.title_edit.setMaximumHeight(28)
        header_layout.addWidget(self.title_edit)

        # Botón emoji compacto
        self.title_emoji_btn = QPushButton("👑")
        self.title_emoji_btn.setFixedSize(28, 28)
        self.title_emoji_btn.setToolTip("Agregar emoji")
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        header_layout.addWidget(self.title_emoji_btn)

        main_layout.addLayout(header_layout)

        # --------- SECCIÓN PRINCIPAL DIVIDIDA ---------
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # --- PANEL IZQUIERDO: CONTROLES ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        # Medios unificado
        media_group = QGroupBox("CONTENIDO VISUAL")
        media_layout = QVBoxLayout()
        media_layout.setSpacing(6)

        # Botones de medios en una sola fila compacta
        media_buttons_layout = QHBoxLayout()
        media_buttons_layout.setSpacing(4)
        
        self.select_media_btn = QPushButton("📁 SELECCIONAR ARCHIVO")
        self.select_media_btn.clicked.connect(self.select_media_unified)
        self.select_media_btn.setMaximumHeight(32)
        media_buttons_layout.addWidget(self.select_media_btn, 2)

        self.clear_media_btn = QPushButton("🗑️")
        self.clear_media_btn.clicked.connect(self.clear_media_file)
        self.clear_media_btn.setFixedSize(32, 32)
        self.clear_media_btn.setToolTip("Limpiar archivo")
        media_buttons_layout.addWidget(self.clear_media_btn)

        media_layout.addLayout(media_buttons_layout)

        # Status compacto
        self.media_status_label = QLabel("Ningún archivo seleccionado")
        self.media_status_label.setMaximumHeight(20)
        media_layout.addWidget(self.media_status_label)

        media_group.setLayout(media_layout)
        left_panel.addWidget(media_group)

        # Audio compacto
        audio_group = QGroupBox("AUDIO PREMIUM")
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(4)

        # Controles de audio en una fila
        audio_controls = QHBoxLayout()
        audio_controls.setSpacing(4)
        
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["Premium", "Ultra", "Máxima"])
        self.audio_quality_combo.setMaximumHeight(28)
        self.audio_quality_combo.setMaximumWidth(80)
        audio_controls.addWidget(self.audio_quality_combo)

        self.audio_duration_spin = QSpinBox()
        self.audio_duration_spin.setRange(30, 600)
        self.audio_duration_spin.setValue(300)
        self.audio_duration_spin.setSuffix("s")
        self.audio_duration_spin.setMaximumHeight(28)
        self.audio_duration_spin.setMaximumWidth(70)
        audio_controls.addWidget(self.audio_duration_spin)

        self.select_audio_btn = QPushButton("📁 AUDIO")
        self.select_audio_btn.clicked.connect(self.select_audio_file)
        self.select_audio_btn.setMaximumHeight(28)
        audio_controls.addWidget(self.select_audio_btn, 1)

        self.clear_audio_btn = QPushButton("🗑️")
        self.clear_audio_btn.clicked.connect(self.clear_audio_file)
        self.clear_audio_btn.setFixedSize(28, 28)
        audio_controls.addWidget(self.clear_audio_btn)

        audio_layout.addLayout(audio_controls)

        # Info de audio compacta
        self.audio_name_edit = QLineEdit()
        self.audio_name_edit.setPlaceholderText("Nombre del audio...")
        self.audio_name_edit.setMaximumHeight(24)
        audio_layout.addWidget(self.audio_name_edit)

        self.audio_desc_edit = QLineEdit()
        self.audio_desc_edit.setPlaceholderText("Descripción breve...")
        self.audio_desc_edit.setMaximumHeight(24)
        audio_layout.addWidget(self.audio_desc_edit)

        self.audio_status_label = QLabel("Ningún audio seleccionado")
        self.audio_status_label.setMaximumHeight(18)
        audio_layout.addWidget(self.audio_status_label)

        audio_group.setLayout(audio_layout)
        left_panel.addWidget(audio_group)

        # Contenido Premium compacto
        content_group = QGroupBox("CONTENIDO EXCLUSIVO")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Checkboxes en una fila
        options_layout = QHBoxLayout()
        options_layout.setSpacing(8)
        
        self.exclusive_content_cb = QCheckBox("💎 Exclusivo")
        self.exclusive_content_cb.setChecked(True)
        options_layout.addWidget(self.exclusive_content_cb)

        self.limited_access_cb = QCheckBox("🔒 Limitado")
        options_layout.addWidget(self.limited_access_cb)

        self.premium_quality_cb = QCheckBox("⭐ Premium")
        options_layout.addWidget(self.premium_quality_cb)

        content_layout.addLayout(options_layout)

        # Área de texto compacta
        self.premium_content_edit = QTextEdit()
        self.premium_content_edit.setPlaceholderText("Contenido exclusivo premium...")
        self.premium_content_edit.setMaximumHeight(120)
        self.premium_content_edit.textChanged.connect(self.update_preview)
        content_layout.addWidget(self.premium_content_edit)

        # Botón emoji para contenido
        emoji_layout = QHBoxLayout()
        self.content_emoji_btn = QPushButton("😊 EMOJI")
        self.content_emoji_btn.clicked.connect(self.insert_emoji_content)
        self.content_emoji_btn.setMaximumHeight(28)
        emoji_layout.addWidget(self.content_emoji_btn)
        emoji_layout.addStretch()
        content_layout.addLayout(emoji_layout)

        content_group.setLayout(content_layout)
        left_panel.addWidget(content_group)

        # Botones de Telegram compactos
        buttons_group = QGroupBox("BOTONES TELEGRAM")
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(4)

        self.config_buttons_btn = QPushButton("⚙️ CONFIGURAR BOTONES")
        self.config_buttons_btn.clicked.connect(self.configure_telegram_buttons)
        self.config_buttons_btn.setMaximumHeight(32)
        buttons_layout.addWidget(self.config_buttons_btn)

        self.buttons_status = QLabel("Botones: No configurados")
        self.buttons_status.setMaximumHeight(20)
        buttons_layout.addWidget(self.buttons_status)

        buttons_group.setLayout(buttons_layout)
        left_panel.addWidget(buttons_group)

        # Botón de publicación principal
        self.publish_btn = QPushButton("🚀 PUBLICAR EN CANAL PREMIUM")
        self.publish_btn.clicked.connect(self.publish_premium_content)
        self.publish_btn.setMinimumHeight(40)
        left_panel.addWidget(self.publish_btn)

        left_panel.addStretch()

        # --- PANEL DERECHO: VISTA PREVIA ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        preview_group = QGroupBox("VISTA PREVIA PREMIUM")
        preview_layout = QVBoxLayout()
        
        # Scroll area para preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(300)
        scroll_area.setMaximumWidth(400)
        
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setSpacing(8)
        
        scroll_area.setWidget(self.preview_widget)
        preview_layout.addWidget(scroll_area)

        # Log de actividad compacto
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(100)
        self.activity_log.setPlaceholderText("Log de actividad...")
        preview_layout.addWidget(self.activity_log)

        preview_group.setLayout(preview_layout)
        right_panel.addWidget(preview_group)

        # Agregar paneles al layout principal
        content_layout.addLayout(left_panel, 1)
        content_layout.addLayout(right_panel, 1)
        main_layout.addLayout(content_layout)

        # Inicializar preview
        self.update_preview()

        self.premium_quality_cb = QCheckBox("⭐ Calidad premium")
        self.premium_quality_cb.setChecked(True)
        content_types_layout.addWidget(self.premium_quality_cb)

        content_layout.addLayout(content_types_layout)

        # Área de texto libre para contenido
        content_layout.addWidget(QLabel("📝 Descripción del Contenido Premium:"))
        
        self.premium_content_edit = QTextEdit()
        self.premium_content_edit.setPlaceholderText(
            "Describe aquí el contenido premium exclusivo...\\n\\n"
            "Ejemplos:\\n"
            "• Tutorial avanzado paso a paso\\n"
            "• Contenido detrás de cámaras\\n"
            "• Análisis detallado\\n"
            "• Recursos exclusivos\\n"
            "• Plantillas premium\\n\\n"
            "¡Escribe lo que quieras para tus suscriptores premium!"
        )
        self.premium_content_edit.textChanged.connect(self.update_preview)
        content_layout.addWidget(self.premium_content_edit)

        # Botón de emoji para contenido
        emoji_layout = QHBoxLayout()
        emoji_layout.addStretch()
        self.content_emoji_btn = QPushButton("😀")
        # Aplicar tema unificado en lugar de estilo personalizado
        self.content_emoji_btn.setFixedSize(36, 36)
        self.content_emoji_btn.setToolTip("Agregar emoji al contenido")
        self.content_emoji_btn.clicked.connect(self.insert_emoji_content)
        emoji_layout.addWidget(self.content_emoji_btn)
        content_layout.addLayout(emoji_layout)

        content_group.setLayout(content_layout)
        left_side.addWidget(content_group)

        # --- Botones de Telegram ---
        buttons_group = QGroupBox("🔘 Botones de Telegram")
        buttons_layout = QVBoxLayout()

        self.button_config_btn = QPushButton("⚙️ Configurar Botones")
        self.button_config_btn.clicked.connect(self.open_button_config)
        buttons_layout.addWidget(self.button_config_btn)

        self.buttons_preview_label = QLabel("Botones: No configurados")
        # Aplicar tema unificado para labels secundarios
        buttons_layout.addWidget(self.buttons_preview_label)

        buttons_group.setLayout(buttons_layout)
        left_side.addWidget(buttons_group)

        # --- Botón de Publicación ---
        publish_layout = QHBoxLayout()
        
        self.publish_btn = QPushButton("🚀 PUBLICAR EN CANAL PREMIUM")
        # Aplicar tema unificado con estilo especial para botón premium
        self.publish_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6bbef4, stop:1 #5aa9d8);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                border-radius: 8px;
                border: none;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7cc5f6, stop:1 #6bb6da);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5ab7f2, stop:1 #4a9cd6);
            }}
        """)
        self.publish_btn.clicked.connect(self.publish_premium_content)
        publish_layout.addWidget(self.publish_btn)

        left_side.addLayout(publish_layout)

        # --------- LADO DERECHO: PREVIEW ---------
        right_side = QVBoxLayout()
        right_side.setSpacing(15)

        # --- Preview del contenido ---
        preview_group = QGroupBox("👀 Vista Previa Premium")
        preview_layout = QVBoxLayout()

        # Scroll area para el preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(400)
        scroll_area.setMinimumHeight(35)

        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setSpacing(12)
        
        scroll_area.setWidget(self.preview_widget)
        preview_layout.addWidget(scroll_area)

        preview_group.setLayout(preview_layout)
        right_side.addWidget(preview_group)

        # --- Log de actividad ---
        activity_group = QGroupBox("📋 Log de Actividad Premium")
        activity_layout = QVBoxLayout()

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(150)
        self.activity_log.setPlaceholderText("Aquí aparecerá el historial de publicaciones premium...")
        self.activity_log.setReadOnly(True)
        activity_layout.addWidget(self.activity_log)

        activity_group.setLayout(activity_layout)
        right_side.addWidget(activity_group)

        # --- Añadir layouts al layout principal ---
        main_layout.addLayout(left_side, 2)  # 2/3 del espacio
        main_layout.addLayout(right_side, 1)  # 1/3 del espacio

        # Actualizar preview inicial
        self.update_preview()
        self.log_activity("Content Manager Premium iniciado", "Conexión al canal premium establecida")

    def select_media_file(self, media_type):
        """Seleccionar archivo de imagen, video o GIF"""
        file_filters = {
            "image": "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp)",
            "video": "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)",
            "gif": "GIFs (*.gif)"
        }
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Seleccionar {media_type.title()}", 
            "", 
            file_filters[media_type]
        )
        
        if file_path:
            self.media_file_path = file_path
            self.media_type = media_type
            filename = os.path.basename(file_path)
            self.media_status_label.setText(f"📁 {media_type.title()}: {filename}")
            # Aplicar tema success para archivo seleccionado
            self.update_preview()

    def clear_media_file(self):
        """Limpiar archivo de medios seleccionado"""
        self.media_file_path = None
        self.media_type = None
        self.media_status_label.setText("📁 Ningún archivo seleccionado")
        # Aplicar tema secundario para estado por defecto
        self.update_preview()

    def select_audio_file(self):
        """Seleccionar archivo de audio"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar Audio Premium", 
            "", 
            "Audio (*.mp3 *.wav *.ogg *.m4a *.aac)"
        )
        
        if file_path:
            self.audio_file_path = file_path
            filename = os.path.basename(file_path)
            self.audio_status_label.setText(f"🎵 Audio: {filename}")
            # Aplicar tema success para audio seleccionado
            
            # Auto-rellenar el nombre si está vacío
            if not self.audio_name_edit.text():
                name_without_ext = os.path.splitext(filename)[0]
                self.audio_name_edit.setText(name_without_ext)
            
            self.update_preview()

    def clear_audio_file(self):
        """Limpiar archivo de audio seleccionado"""
        self.audio_file_path = None
        self.audio_status_label.setText("📁 Ningún audio seleccionado")
        # Aplicar tema secundario para estado por defecto
        self.audio_name_edit.clear()
        self.audio_description_edit.clear()
        self.update_preview()

    def insert_emoji_title(self):
        """Insertar emoji en el título"""
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor_pos = self.title_edit.cursorPosition()
                current_text = self.title_edit.text()
                new_text = current_text[:cursor_pos] + emoji + current_text[cursor_pos:]
                self.title_edit.setText(new_text)
                self.title_edit.setCursorPosition(cursor_pos + len(emoji))

    def insert_emoji_content(self):
        """Insertar emoji en el contenido"""
        picker = EmojiPicker(self)
        if picker.exec():
            emoji = picker.selected_emoji
            if emoji:
                cursor = self.premium_content_edit.textCursor()
                cursor.insertText(emoji)

    def open_button_config(self):
        """Abrir diálogo de configuración de botones"""
        dialog = ButtonConfigDialog(self, self.telegram_buttons)
        if dialog.exec():
            self.telegram_buttons = dialog.get_values()
            self.update_buttons_preview()

    def update_buttons_preview(self):
        """Actualizar preview de los botones"""
        if not self.telegram_buttons or not self.telegram_buttons[0]:
            self.buttons_preview_label.setText("Botones: No configurados")
            # Aplicar tema secundario para estado por defecto
        else:
            button_count = sum(len(row) for row in self.telegram_buttons)
            self.buttons_preview_label.setText(f"Botones: {button_count} configurados")
            # Aplicar tema success para botones configurados

    def update_preview(self):
        """Actualizar vista previa del contenido premium"""
        # Limpiar preview anterior
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Título premium
        if self.title_edit.text():
            title_label = QLabel(f"👑 {self.title_edit.text()}")
            # Aplicar tema responsivo para título premium
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: #6bbef4;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                    background: rgba(107, 190, 244, 0.1);
                    border-radius: 8px;
                    border-left: 3px solid #6bbef4;
                }}
            """)
            title_label.setWordWrap(True)
            self.preview_layout.addWidget(title_label)

        # Preview de medios
        if self.media_file_path:
            media_preview = QLabel(f"🎬 {self.media_type.title()}: {os.path.basename(self.media_file_path)}")
            media_preview.setStyleSheet(f"""
                QLabel {{
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 8px;
                    background: rgba(76, 175, 80, 0.1);
                    border-radius: 8px;
                    border-left: 3px solid #4CAF50;
                }}
            """)
            self.preview_layout.addWidget(media_preview)

        # Preview de audio
        if self.audio_file_path:
            audio_name = self.audio_name_edit.text() or "Audio sin nombre"
            audio_desc = self.audio_description_edit.toPlainText()
            
            audio_preview = QLabel()
            audio_text = f"🎵 {audio_name}"
            if audio_desc:
                audio_text += f"\\n📝 {audio_desc[:100]}{'...' if len(audio_desc) > 100 else ''}"
            
            audio_preview.setText(audio_text)
            audio_preview.setStyleSheet(f"""
                QLabel {{
                    color: #FF9800;
                    font-weight: bold;
                    padding: 8px;
                    background: rgba(255, 152, 0, 0.1);
                    border-radius: 8px;
                    border-left: 3px solid #FF9800;
                }}
            """)
            audio_preview.setWordWrap(True)
            self.preview_layout.addWidget(audio_preview)

        # Contenido premium
        content_text = self.premium_content_edit.toPlainText()
        if content_text:
            content_preview = QLabel(content_text)
            content_preview.setStyleSheet(f"""
                QLabel {{
                    color: #E1E1E1;
                    font-size: 12px;
                    padding: 12px;
                    background: #2a3442;
                    border-radius: 8px;
                    border: 1px solid #444;
                }}
            """)
            content_preview.setWordWrap(True)
            self.preview_layout.addWidget(content_preview)

        # Indicadores premium
        premium_indicators = QLabel()
        indicators = []
        if self.exclusive_content_cb.isChecked():
            indicators.append("💎 Exclusivo")
        if self.limited_access_cb.isChecked():
            indicators.append("🔒 Acceso Limitado")
        if self.premium_quality_cb.isChecked():
            indicators.append("⭐ Calidad Premium")
        
        if indicators:
            premium_indicators.setText(" • ".join(indicators))
            premium_indicators.setStyleSheet(f"""
                QLabel {{
                    color: #6bbef4;
                    font-size: 11px;
                    font-style: italic;
                    padding: 8px;
                    background: rgba(107, 190, 244, 0.05);
                    border-radius: 7px;
                }}
            """)
            self.preview_layout.addWidget(premium_indicators)

        # Spacer al final
        self.preview_layout.addStretch()

    def publish_premium_content(self):
        """Publicar contenido premium"""
        # Validaciones
        if not self.title_edit.text():
            QMessageBox.warning(self, "Error", "El título es obligatorio para contenido premium")
            return
        
        if not self.premium_content_edit.toPlainText():
            QMessageBox.warning(self, "Error", "El contenido premium no puede estar vacío")
            return

        # Simular publicación
        try:
            title = self.title_edit.text()
            content = self.premium_content_edit.toPlainText()
            
            # Log de la publicación
            self.log_activity(
                f"Publicación premium: {title}",
                f"Contenido publicado en canal premium con éxito"
            )
            
            # Mostrar mensaje de éxito
            QMessageBox.information(
                self, 
                "Publicación Exitosa", 
                f"✅ Contenido premium '{title}' publicado exitosamente\\n\\n"
                f"📊 Estadísticas:\\n"
                f"• Medios: {'Sí' if self.media_file_path else 'No'}\\n"
                f"• Audio: {'Sí' if self.audio_file_path else 'No'}\\n"
                f"• Botones: {sum(len(row) for row in self.telegram_buttons) if self.telegram_buttons[0] else 0}\\n"
                f"• Longitud: {len(content)} caracteres"
            )
            
        except Exception as e:
            self.log_activity("Error en publicación", str(e))
            QMessageBox.critical(self, "Error", f"Error al publicar contenido premium:\\n{str(e)}")

    def log_activity(self, action, details):
        """Agregar entrada al log de actividad"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {action}\\n{details}\\n\\n"
        
        current_text = self.activity_log.toPlainText()
        new_text = log_entry + current_text
        
        # Limitar el log a las últimas 10 entradas aproximadamente
        lines = new_text.split('\\n')
        if len(lines) > 50:  # ~10 entradas * 5 líneas promedio
            new_text = '\\n'.join(lines[:50])
        
        self.activity_log.setPlainText(new_text)
