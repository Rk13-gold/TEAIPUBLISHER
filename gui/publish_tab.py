from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QSizePolicy, QProgressBar,
    QComboBox, QFrame, QFormLayout, QApplication, QCheckBox, QSpinBox, QDateTimeEdit,
    QGridLayout, QStyle, QScrollArea
)

from PySide6.QtCore import Qt, QThread, Signal, QDateTime
from PySide6.QtGui import QFont, QIcon
import requests
import json
import os
import time
import re
import random
import shutil
from datetime import datetime
from pathlib import Path
from services.telegram_bot_client import TelegramBotClient

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
    from gui.emoji_renderer import render_emoji
except ImportError:
    def render_emoji(char, size=28):
        return None

try:
    from gui.emoji_text_helper import insert_emoji_textedit, emoji_document_to_plaintext
except ImportError:
    # Fallback: plain text insertion
    def insert_emoji_textedit(textedit, emoji, size=28):
        cursor = textedit.textCursor()
        cursor.insertText(emoji)
    def emoji_document_to_plaintext(doc):
        return doc.toPlainText()

try:
    from utils.telegram_format import prepare_content_for_telegram, build_post_content
except ImportError:
    def prepare_content_for_telegram(c):
        return c
    def build_post_content(title, body, cta='', hashtags=''):
        parts = [p for p in [title and f'<b>{title}</b>', body] if p]
        if cta or hashtags:
            parts.append('\n'.join(p for p in [cta, hashtags] if p))
        return '\n\n'.join(parts)

try:
    from gui.emoji_line_edit import EmojiLineEdit
except ImportError:
    EmojiLineEdit = None

try:
    from gui.button_config_dialog import ButtonConfigDialog
except ImportError:
    ButtonConfigDialog = None

try:
    from services.voice_notes import convert_mp3_to_ogg as convert_audio_to_ogg, get_audio_quality_settings
except ImportError:
    # Fallback audio conversion functions
    def convert_audio_to_ogg(input_path, output_path, quality="high", title="", artist="", album=""):
        """Fallback audio conversion - copies file if conversion not available"""
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

# Professional publishing worker for ordered Telegram posts
class PublishWorker(QThread):
    """Professional worker for step-by-step Telegram publishing"""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # Success, final message
    
    def __init__(self, post_data, config):
        super().__init__()
        self.post_data = post_data
        self.config = config
        
    def run(self):
        """Execute professional publishing sequence"""
        try:
            from core.database import get_telegram_credentials
            db_token, db_chat_id = get_telegram_credentials()
            token = db_token or getattr(self.config, "bot_token", None) or getattr(self.config, "telegram_token", None)
            chat_id = db_chat_id or self.config.telegram_chat_id

            # Validate token and chat before starting publish sequence
            if not token:
                self.progress.emit("❌ Token de bot no configurado en la configuración")
                self.finished.emit(False, "Token de bot no configurado")
                return
            try:
                bot_client = TelegramBotClient(token)
                chat_info = bot_client.get_chat_info(chat_id)
                if not chat_info:
                    self.progress.emit(f"❌ Chat no encontrado: {chat_id}")
                    self.finished.emit(False, "Chat no encontrado. Verifica ID o @username y que el bot esté añadido al canal como administrador")
                    return
                perms = bot_client.validate_bot_permissions(chat_id) or {}
                status = perms.get('status', None)
                if status not in ['administrator', 'creator']:
                    self.progress.emit("⚠️ El bot no es administrador en el chat. Es posible que no pueda publicar mensajes")
            except Exception as e:
                self.progress.emit(f"❌ Error validando token/chat: {e}")
                self.finished.emit(False, f"Error validando token/chat: {e}")
                return
            
            self.progress.emit("🚀 Iniciando secuencia de publicación...")
            
            # Debug information
            media_path = self.post_data.get('presentation_path')
            main_content = self.post_data.get('main_content')
            self.progress.emit(f"🔍 Media path: {media_path}")
            self.progress.emit(f"🔍 Main content: {main_content}")
            
            main_content_sent = False
            
            # STEP 1: Send main content (image/video/gif with text) - ALWAYS FIRST
            if self.post_data.get('presentation_path') and self.post_data.get('main_content'):
                self.progress.emit("📸 Enviando contenido principal con media...")
                success = self.send_presentation_with_content(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar contenido principal con media")
                    return
                main_content_sent = True
                time.sleep(1.5)
            elif self.post_data.get('presentation_path'):
                self.progress.emit("📸 Enviando media sin texto...")
                success = self.send_presentation(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar media sin texto")
                    return
                main_content_sent = True
                time.sleep(1.5)
            elif self.post_data.get('main_content'):
                self.progress.emit("📝 Enviando mensaje de texto...")
                success = self.send_main_message(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar mensaje de texto")
                    return
                main_content_sent = True
                time.sleep(1.5)
            
            # STEP 2: Send premium voice note (SECOND) - Maximum quality
            voice_file = self.post_data.get('voice_file')
            if voice_file and os.path.exists(voice_file):
                self.progress.emit("🎵 Enviando audio premium en máxima calidad...")
                success = self.send_voice_note_max_quality(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar nota de voz")
                    return
                time.sleep(1.5)
            
            # STEP 3: Send CTA and hashtags (THIRD) - Without buttons
            if self.post_data.get('cta_hashtags'):
                self.progress.emit("🎯 Enviando llamada a la acción...")
                success = self.send_cta_hashtags_only(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar CTA")
                    return
                time.sleep(1.5)
            
            # STEP 4: Send buttons (ALWAYS LAST) - Only if there are buttons
            if self.post_data.get('reply_markup'):
                self.progress.emit("🔗 Enviando botones interactivos...")
                success = self.send_buttons_only(token, chat_id)
                if not success:
                    self.finished.emit(False, "Error al enviar botones")
                    return
            
            if not main_content_sent:
                self.finished.emit(False, "No hay contenido para publicar")
                return
                
            self.progress.emit("✅ Secuencia de publicación completada exitosamente")
            self.finished.emit(True, "Post publicado correctamente en el orden especificado")
            
        except requests.exceptions.Timeout:
            self.finished.emit(False, "Timeout: La conexión con Telegram tardó demasiado")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, "Error de conexión: No se pudo conectar con Telegram")
        except Exception as e:
            self.finished.emit(False, f"Error inesperado: {str(e)}")

    def send_presentation_with_content(self, token, chat_id):
        """Send presentation media with main content as caption"""
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
            self.progress.emit(f"❌ Error en presentación con contenido: {e}")
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
            self.progress.emit(f"📝 Preparando mensaje: {len(text)} caracteres")
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            
            self.progress.emit("📡 Enviando petición a Telegram...")
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            self.progress.emit(f"📡 Respuesta de Telegram: {result}")
            
            if result.get("ok"):
                self.progress.emit("✅ Mensaje principal enviado")
                return True
            else:
                error_desc = result.get('description', 'Error desconocido')
                self.progress.emit(f"❌ Error API Telegram: {error_desc}")
                return False
        except requests.exceptions.Timeout:
            self.progress.emit("❌ Timeout: La petición tardó demasiado")
            return False
        except requests.exceptions.ConnectionError:
            self.progress.emit("❌ Error de conexión con Telegram")
            return False
        except Exception as e:
            self.progress.emit(f"❌ Error inesperado en mensaje: {e}")
            return False

    def send_voice_note_max_quality(self, token, chat_id):
        """Send premium voice note with maximum quality conversion"""
        try:
            voice_file = self.post_data['voice_file']
            voice_title = self.post_data.get('voice_title', '')
            voice_description = self.post_data.get('voice_description', '')
            
            # Validate voice file exists
            if not os.path.exists(voice_file):
                self.progress.emit("❌ Error: Archivo de audio no encontrado")
                return False
            
            self.progress.emit("🔄 Preparando audio premium en máxima calidad...")
            
            # Convert to OGG with maximum quality (320k) for best Telegram compatibility
            ext = os.path.splitext(voice_file)[1].lower()
            ogg_path = voice_file
            
            if ext != '.ogg':
                try:
                    ogg_path = voice_file.rsplit('.', 1)[0] + '_telegram_premium.ogg'
                    self.progress.emit("🔄 Convirtiendo audio a OGG premium (320k)...")
                    success = convert_audio_to_ogg(
                        voice_file, 
                        ogg_path,
                        quality="ultra",  # Always maximum quality
                        title=voice_title or "Audio Premium",
                        artist="Canal Premium",
                        album="Contenido Exclusivo"
                    )
                    if success and os.path.exists(ogg_path):
                        self.progress.emit("✅ Audio convertido a máxima calidad")
                    else:
                        self.progress.emit("⚠️ Conversión falló, usando archivo original")
                        ogg_path = voice_file
                except Exception as e:
                    self.progress.emit(f"⚠️ Error en conversión: {str(e)}")
                    self.progress.emit("⚠️ Usando archivo original")
                    ogg_path = voice_file
            else:
                self.progress.emit("✅ Archivo ya está en formato OGG")
            
            # Validate final file
            if not os.path.exists(ogg_path):
                self.progress.emit("❌ Error: No se pudo preparar el archivo de audio")
                return False
            
            # Create caption with consistent width formatting
            caption = ""
            if voice_title:
                caption += f"👑 {voice_title}\n\n"
            if voice_description:
                caption += f"{voice_description}\n\n"
            caption += "💎 Contenido Premium Exclusivo - Máxima Calidad 🔒"
            
            # Limit caption to 1024 characters for voice messages
            if len(caption) > 1024:
                caption = caption[:1020] + "..."
            
            self.progress.emit("📤 Enviando nota de voz premium a Telegram...")
            
            # Send voice note
            with open(ogg_path, "rb") as voice:
                url = f"https://api.telegram.org/bot{token}/sendVoice"
                files = {"voice": voice}
                data = {"chat_id": chat_id, "caption": caption}
                
                # Send request with timeout
                response = requests.post(url, data=data, files=files, timeout=60)
                result = response.json()
            
            # Clean up temporary file
            if ogg_path != voice_file and os.path.exists(ogg_path):
                os.remove(ogg_path)
            
            if result.get("ok"):
                self.progress.emit("✅ Nota de voz premium enviada correctamente")
                return True
            else:
                self.progress.emit(f"❌ Error: {result.get('description', 'Error desconocido')}")
                return False
        except Exception as e:
            self.progress.emit(f"❌ Error en nota de voz: {e}")
            return False

    def send_cta_hashtags_only(self, token, chat_id):
        """Send CTA and hashtags as separate message (without buttons)"""
        try:
            text = self.post_data['cta_hashtags']
            
            self.progress.emit(f"📝 Preparando CTA: {len(text)} caracteres")
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            
            self.progress.emit("📡 Enviando CTA a Telegram...")
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            self.progress.emit(f"📡 Respuesta de Telegram: {result}")
            
            if result.get("ok"):
                self.progress.emit("✅ CTA y hashtags enviados")
                return True
            else:
                error_desc = result.get('description', 'Error desconocido')
                self.progress.emit(f"❌ Error API Telegram: {error_desc}")
                return False
        except requests.exceptions.Timeout:
            self.progress.emit("❌ Timeout: La petición de CTA tardó demasiado")
            return False
        except requests.exceptions.ConnectionError:
            self.progress.emit("❌ Error de conexión con Telegram en CTA")
            return False
        except Exception as e:
            self.progress.emit(f"❌ Error inesperado en CTA: {e}")
            return False

    def send_buttons_only(self, token, chat_id):
        """Send buttons as separate interactive message with psychological phrases"""
        try:
            reply_markup = self.post_data.get('reply_markup')
            
            if not reply_markup:
                self.progress.emit("⚠️ No hay botones para enviar")
                return True  # Not an error, just no buttons
            
            # Mensaje fijo que dirige al menú de botones
            text = "📋 Menú de opciones: usa los botones para elegir la acción que prefieras."
            self.progress.emit("🎯 CTA fijo para menú de opciones aplicado")
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id, 
                "text": text, 
                "reply_markup": reply_markup,
                "parse_mode": "HTML"
            }
            
            self.progress.emit("📡 Enviando botones a Telegram...")
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            self.progress.emit(f"📡 Respuesta de Telegram: {result}")
            
            if result.get("ok"):
                self.progress.emit("✅ Botones interactivos enviados")
                return True
            else:
                error_desc = result.get('description', 'Error desconocido')
                self.progress.emit(f"❌ Error API Telegram: {error_desc}")
                return False
        except requests.exceptions.Timeout:
            self.progress.emit("❌ Timeout: La petición de botones tardó demasiado")
            return False
        except requests.exceptions.ConnectionError:
            self.progress.emit("❌ Error de conexión con Telegram en botones")
            return False
        except Exception as e:
            self.progress.emit(f"❌ Error inesperado en botones: {e}")
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

class PublishTab(QWidget):
    """Professional Telegram Publisher with 3 equal sections layout"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("publish_tab")
        self.setWindowTitle("🚀 Publicar en Telegram")

        # State variables
        self.presentation_media_path = None
        self.presentation_media_type = None
        self.telegram_buttons = [[]]
        self.worker = None
        self.voice_selected_file = None
        self.telegram_image_path = None
        
        # Audio quality settings
        self.audio_quality_settings = get_audio_quality_settings()
        
        # Layout principal con scroll
        container_widget = QWidget()
        main_layout = QHBoxLayout(container_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)
        
        # Sección izquierda - Configuración de contenido
        left_group = QGroupBox("Configuración de Contenido")
        left_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)
        self.setup_content_configuration_section(left_layout)
        
        # Sección central - Editor de publicaciones
        center_group = QGroupBox("Editor de Publicación")
        center_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout = QVBoxLayout(center_group)
        center_layout.setContentsMargins(4, 4, 4, 4)
        center_layout.setSpacing(4)
        self.setup_post_editor_section(center_layout)
        
        # Sección derecha - Vista previa
        right_group = QGroupBox("Vista Previa")
        right_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_group)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)
        self.setup_preview_publishing_section(right_layout)
        
        # Configurar tamaños mínimos y máximos
        left_group.setMinimumWidth(240)
        left_group.setMaximumWidth(300)
        right_group.setMinimumWidth(240)
        right_group.setMaximumWidth(300)
        
        # Añadir widgets al layout principal con factores de estiramiento
        main_layout.addWidget(left_group, 1)    # Sección izquierda - 1/4 del ancho
        main_layout.addWidget(center_group, 2)  # Sección central - 2/4 del ancho
        main_layout.addWidget(right_group, 1)   # Sección derecha - 1/4 del ancho

        # Scroll area para toda la pestaña
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_widget)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll_area)

        # Connect events
        self.connect_all_events()

    def setup_content_configuration_section(self, parent_layout):
        """Setup left section: Content Configuration"""
        # Configurar el layout principal
        parent_layout.setSpacing(6)
        parent_layout.setContentsMargins(4, 4, 4, 4)
        
        # Media selection
        media_group = QGroupBox("Medios")
        media_layout = QVBoxLayout(media_group)
        media_layout.setSpacing(4)
        media_layout.setContentsMargins(4, 8, 4, 4)
        
        # Add media selection button
        self.btn_select_media = QPushButton("Seleccionar Imagen/Video")
        try:
            from PySide6.QtWidgets import QStyle
            app_style = QApplication.style()
            file_icon = app_style.standardIcon(QStyle.SP_FileIcon)
            self.btn_select_media.setIcon(file_icon)
        except Exception as e:
            print(f"Warning al cargar el ícono: {e}")
        media_layout.addWidget(self.btn_select_media)
        
        # Media info label
        self.lbl_media_info = QLabel("Ningún archivo seleccionado")
        self.lbl_media_info.setWordWrap(True)
        self.lbl_media_info.setStyleSheet("color: #888; font-style: italic; font-size: 9px;")
        media_layout.addWidget(self.lbl_media_info)
        # Backwards compatibility alias used elsewhere
        self.media_status_label = self.lbl_media_info
        
        # Add media group to parent layout
        parent_layout.addWidget(media_group)
        
        # Add voice note section
        voice_group = QGroupBox("Nota de Voz")
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setSpacing(4)
        voice_layout.setContentsMargins(4, 8, 4, 4)
        
        # Add voice note button
        self.btn_select_voice = QPushButton("Seleccionar Audio")
        try:
            from PySide6.QtWidgets import QStyle
            app_style = QApplication.style()
            audio_icon = app_style.standardIcon(QStyle.SP_MediaVolume)
            self.btn_select_voice.setIcon(audio_icon)
        except Exception as e:
            print(f"Warning al cargar el ícono de audio: {e}")
        voice_layout.addWidget(self.btn_select_voice)
        
        # Voice info label
        self.lbl_voice_info = QLabel("Ningún archivo de audio seleccionado")
        self.lbl_voice_info.setWordWrap(True)
        self.lbl_voice_info.setStyleSheet("color: #888; font-style: italic; font-size: 9px;")
        voice_layout.addWidget(self.lbl_voice_info)
        
        # Add voice group to parent layout
        parent_layout.addWidget(voice_group)
        
        # CTA & Hashtags Group
        cta_group = QGroupBox("Llamado a la acción")
        cta_layout = QVBoxLayout(cta_group)
        cta_layout.setSpacing(4)
        cta_layout.setContentsMargins(4, 8, 4, 4)
        
        # CTA Input
        self.cta_input = QLineEdit()
        self.cta_input.setPlaceholderText("Ej: ¡Visita nuestro sitio web!")
        cta_layout.addWidget(QLabel("Texto del CTA:"))
        cta_layout.addWidget(self.cta_input)
        # Legacy alias used elsewhere
        self.cta_edit = self.cta_input
        
        # Hashtags Input
        self.hashtags_input = QLineEdit()
        self.hashtags_input.setPlaceholderText("#ejemplo #otro")
        cta_layout.addWidget(QLabel("Hashtags:"))
        cta_layout.addWidget(self.hashtags_input)
        # Legacy alias used elsewhere
        self.hashtags_edit = self.hashtags_input
        
        # Add CTA group to parent layout
        parent_layout.addWidget(cta_group)
        
        # Add stretch to push everything up
        parent_layout.addStretch(1)
        
        # Connect signals
        self.btn_select_media.clicked.connect(self.select_image_for_preview)
        self.btn_select_voice.clicked.connect(self.select_voice_file)
        self.cta_input.textChanged.connect(self.update_preview)
        self.hashtags_input.textChanged.connect(self.update_preview)
        
        # Publishing Status & Parameters
        self.setup_publishing_status_section(parent_layout)
        
        # Add stretch to push content to the top
        parent_layout.addStretch()

    def setup_post_editor_section(self, parent_layout):
        """Setup center section: Post Editor (using AI Generator structure)"""
        editor_group = QGroupBox("✍️ Editor de Post")
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(6)
        editor_layout.setContentsMargins(8, 8, 8, 8)
        editor_group.setLayout(editor_layout)
        editor_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        # Title and image selection row (from AI Generator)
        title_img_layout = QHBoxLayout()
        title_img_layout.setSpacing(4)
        
        # Title label and field
        title_label = QLabel("Título:")
        title_label.setFixedWidth(40)
        title_img_layout.addWidget(title_label)
        
        self.title_edit = EmojiLineEdit() if EmojiLineEdit else QLineEdit()
        self.title_edit.setPlaceholderText("Título del post")
        self.title_edit.textChanged.connect(self.update_preview)
        title_img_layout.addWidget(self.title_edit, 1)  # Takes remaining space

        # Emoji button for title
        self.title_emoji_btn = QPushButton()
        self.title_emoji_btn.setFixedSize(36, 36)
        _pix = render_emoji("😊", 22)
        if _pix and not _pix.isNull():
            self.title_emoji_btn.setIcon(QIcon(_pix))
            self.title_emoji_btn.setIconSize(_pix.size())
        else:
            self.title_emoji_btn.setText(":)")
        self.title_emoji_btn.setToolTip("Insertar emoji en el título")
        self.title_emoji_btn.clicked.connect(self.insert_emoji_title)
        self.title_emoji_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #333; border-radius: 6px; padding: 2px; }
            QPushButton:hover { background: #2d2f52; border: 1px solid #7c5cfc; }
            QPushButton:pressed { background: #3a3d6b; }
        """)
        title_img_layout.addWidget(self.title_emoji_btn)

        # Image selection button
        self.image_btn = QPushButton("Img")
        self.image_btn.setFixedSize(28, 28)
        self.image_btn.setToolTip("Seleccionar imagen/vídeo/GIF")
        self.image_btn.clicked.connect(self.select_image_for_preview)
        title_img_layout.addWidget(self.image_btn)

        editor_layout.addLayout(title_img_layout)

        # Content editor
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Escribe el contenido del post aquí...")
        self.content_edit.textChanged.connect(self.update_preview)
        editor_layout.addWidget(self.content_edit, 1)  # Takes all available space
        # Legacy attribute name compatibility
        self.edit_area = self.content_edit

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        # Button configuration
        self.button_config_btn = QPushButton("🛠 Botones")
        self.button_config_btn.setToolTip("Configurar botones del mensaje")
        self.button_config_btn.clicked.connect(self.open_button_config)
        buttons_layout.addWidget(self.button_config_btn)
        
        # Emoji button
        self.emoji_btn = QPushButton()
        self.emoji_btn.setFixedSize(36, 36)
        _pix = render_emoji("😊", 22)
        if _pix and not _pix.isNull():
            self.emoji_btn.setIcon(QIcon(_pix))
            self.emoji_btn.setIconSize(_pix.size())
        else:
            self.emoji_btn.setText(":)")
        self.emoji_btn.setToolTip("Insertar emoji")
        self.emoji_btn.clicked.connect(self.insert_emoji_content)
        self.emoji_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #333; border-radius: 6px; padding: 2px; }
            QPushButton:hover { background: #2d2f52; border: 1px solid #7c5cfc; }
            QPushButton:pressed { background: #3a3d6b; }
        """)
        buttons_layout.addWidget(self.emoji_btn)
        
        buttons_layout.addStretch()
        editor_layout.addLayout(buttons_layout)
        publish_layout = QHBoxLayout()
        self.publish_button = QPushButton("🚀 PUBLICAR EN TELEGRAM")
        self.publish_button.setMinimumHeight(50)
        self.publish_button.clicked.connect(self.publish_post)
        publish_layout.addWidget(self.publish_button)
        editor_layout.addLayout(publish_layout)
        
        # Asegurarse de que el grupo del editor tenga el layout configurado
        editor_group.setLayout(editor_layout)
        editor_group.setMinimumWidth(350)
        editor_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Agregar el grupo al layout padre que se pasó como parámetro
        parent_layout.addWidget(editor_group, 1)  # Equal width

    def setup_preview_publishing_section(self, parent_layout):
        """Setup right section: Preview and Publishing Status"""
        preview_group = QGroupBox("📱 Vista Previa")
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(8)
        
        # Preview widget (from AI Generator)
        if PostPreviewWidget:
            self.post_preview = PostPreviewWidget()
            self.post_preview.setMinimumWidth(280)  # Más estrecho pero completo
            self.post_preview.setMaximumWidth(320)  # Límite máximo
            self.post_preview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            
            # Enable image selection from preview (from AI Generator)
            if hasattr(self.post_preview, 'image_label'):
                self.post_preview.image_label.mousePressEvent = self.post_preview_select_image
            
            preview_layout.addWidget(self.post_preview)
        else:
            # Fallback preview
            self.preview_area = QTextEdit()
            self.preview_area.setReadOnly(True)
            self.preview_area.setPlaceholderText("Vista previa del post...")
            self.preview_area.setMinimumWidth(280)
            self.preview_area.setMaximumWidth(320)
            preview_layout.addWidget(self.preview_area)
        
        preview_group.setLayout(preview_layout)
        preview_group.setMinimumWidth(300)
        preview_group.setMaximumWidth(340)
        preview_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        parent_layout.addWidget(preview_group, 0)  # Sin expansión

    def setup_voice_note_section(self, layout):
        """Setup professional voice note section"""
        voice_group = QGroupBox("🎵 Nota de Voz Premium (Opcional)")
        voice_group.setMinimumHeight(180)
        voice_group.setMaximumHeight(200)
        voice_layout = QVBoxLayout()
        
        # Voice file selection
        voice_file_layout = QHBoxLayout()
        self.voice_select_btn = QPushButton("🎤 Seleccionar Audio")
        self.voice_select_btn.clicked.connect(self.select_voice_file)
        voice_file_layout.addWidget(self.voice_select_btn)
        
        self.voice_file_label = QLabel("Ningún archivo seleccionado")
        self.voice_file_label.setStyleSheet("color: gray; font-style: italic;")
        voice_file_layout.addWidget(self.voice_file_label)
        voice_layout.addLayout(voice_file_layout)
        
        # Voice metadata with emoji button
        metadata_layout = QVBoxLayout()
        
        # Title row with emoji button
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Título:"))
        self.voice_title_edit = EmojiLineEdit() if EmojiLineEdit else QLineEdit()
        self.voice_title_edit.setPlaceholderText("Título del audio (opcional)")
        title_row.addWidget(self.voice_title_edit)
        
        # Emoji button for voice title
        self.voice_emoji_btn = QPushButton()
        self.voice_emoji_btn.setFixedSize(32, 32)
        _pix = render_emoji("😊", 20)
        if _pix and not _pix.isNull():
            self.voice_emoji_btn.setIcon(QIcon(_pix))
            self.voice_emoji_btn.setIconSize(_pix.size())
        else:
            self.voice_emoji_btn.setText(":)")
        self.voice_emoji_btn.setToolTip("Agregar emoji al título del audio")
        self.voice_emoji_btn.clicked.connect(self.insert_emoji_voice_title)
        self.voice_emoji_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #333; border-radius: 6px; padding: 2px; }
            QPushButton:hover { background: #2d2f52; border: 1px solid #7c5cfc; }
            QPushButton:pressed { background: #3a3d6b; }
        """)
        title_row.addWidget(self.voice_emoji_btn)
        metadata_layout.addLayout(title_row)
        
        # Description
        metadata_layout.addWidget(QLabel("Descripción:"))
        self.voice_description_edit = QTextEdit()
        self.voice_description_edit.setPlaceholderText("Descripción del audio (opcional)")
        self.voice_description_edit.setMaximumHeight(50)
        metadata_layout.addWidget(self.voice_description_edit)
        
        voice_layout.addLayout(metadata_layout)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

    def setup_cta_hashtags_section(self, layout):
        """Setup CTA and hashtags section"""
        engagement_group = QGroupBox("🎯 Engagement y Hashtags")
        engagement_group.setMinimumHeight(120)
        engagement_group.setMaximumHeight(140)
        engagement_layout = QVBoxLayout()
        
        # CTA section
        cta_layout = QHBoxLayout()
        cta_layout.addWidget(QLabel("💬 CTA:"))
        self.cta_edit = EmojiLineEdit() if EmojiLineEdit else QLineEdit()
        self.cta_edit.setPlaceholderText("¡Comparte si te gustó! 👍")
        self.cta_edit.textChanged.connect(self.update_preview)
        self.cta_edit.textChanged.connect(self.update_post_statistics)
        cta_layout.addWidget(self.cta_edit)
        
        self.cta_emoji_btn = QPushButton()
        self.cta_emoji_btn.setFixedSize(32, 32)
        _pix = render_emoji("😊", 20)
        if _pix and not _pix.isNull():
            self.cta_emoji_btn.setIcon(QIcon(_pix))
            self.cta_emoji_btn.setIconSize(_pix.size())
        else:
            self.cta_emoji_btn.setText(":)")
        self.cta_emoji_btn.clicked.connect(self.insert_emoji_cta)
        self.cta_emoji_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #333; border-radius: 6px; padding: 2px; }
            QPushButton:hover { background: #2d2f52; border: 1px solid #7c5cfc; }
            QPushButton:pressed { background: #3a3d6b; }
        """)
        cta_layout.addWidget(self.cta_emoji_btn)
        engagement_layout.addLayout(cta_layout)
        
        # Hashtags section
        hashtags_layout = QHBoxLayout()
        hashtags_layout.addWidget(QLabel("🏷️ Tags:"))
        self.hashtags_edit = QLineEdit()
        self.hashtags_edit.setPlaceholderText("#viral #trending #content")
        self.hashtags_edit.textChanged.connect(self.update_preview)
        self.hashtags_edit.textChanged.connect(self.update_post_statistics)
        hashtags_layout.addWidget(self.hashtags_edit)
        engagement_layout.addLayout(hashtags_layout)
        
        engagement_group.setLayout(engagement_layout)
        layout.addWidget(engagement_group)

    def setup_publishing_status_section(self, layout):
        """Setup comprehensive publishing status and parameters section"""
        status_group = QGroupBox("📊 Estado y Parámetros de Publicación")
        status_group.setMinimumHeight(350)
        status_group.setMaximumHeight(400)
        status_layout = QVBoxLayout()
        
        # Current status
        self.status_label = QLabel("✅ Listo para publicar")
        self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        
        # Publishing parameters
        params_layout = QFormLayout()
        
        # Telegram limits info
        self.max_text_label = QLabel("4096 caracteres")
        self.max_caption_label = QLabel("1024 caracteres") 
        self.max_voice_label = QLabel("50 MB")
        self.max_photo_label = QLabel("10 MB")
        self.max_video_label = QLabel("50 MB")
        
        params_layout.addRow("📝 Límite texto:", self.max_text_label)
        params_layout.addRow("📷 Límite caption:", self.max_caption_label)
        params_layout.addRow("🎵 Límite audio:", self.max_voice_label)
        params_layout.addRow("🖼️ Límite foto:", self.max_photo_label)
        params_layout.addRow("🎥 Límite video:", self.max_video_label)
        
        status_layout.addLayout(params_layout)
        
        # Current post statistics
        stats_layout = QFormLayout()
        self.current_chars_label = QLabel("0")
        self.current_words_label = QLabel("0")
        self.current_media_label = QLabel("Ninguno")
        self.current_buttons_label = QLabel("0")
        
        stats_layout.addRow("✏️ Caracteres actuales:", self.current_chars_label)
        stats_layout.addRow("📝 Palabras actuales:", self.current_words_label)
        stats_layout.addRow("📎 Media actual:", self.current_media_label)
        stats_layout.addRow("🔗 Botones actuales:", self.current_buttons_label)
        
        status_layout.addLayout(stats_layout)
        
        # Publishing options (moved here)
        options_layout = QVBoxLayout()
        
        self.premium_formatting_checkbox = QCheckBox("✨ Formato Premium HTML")
        self.premium_formatting_checkbox.setToolTip("Aplicar formato HTML mejorado al texto")
        self.premium_formatting_checkbox.setChecked(True)
        options_layout.addWidget(self.premium_formatting_checkbox)
        
        self.spoiler_checkbox = QCheckBox("🕵️ Efecto Spoiler en medios")
        self.spoiler_checkbox.setToolTip("Ocultar imágenes/videos hasta que el usuario haga clic")
        options_layout.addWidget(self.spoiler_checkbox)
        
        status_layout.addLayout(options_layout)
        
        # Progress bar (moved here)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Progress log (moved here)
        self.progress_log = QTextEdit()
        self.progress_log.setMaximumHeight(80)
        self.progress_log.setReadOnly(True)
        self.progress_log.setVisible(False)
        self.progress_log.setStyleSheet("font-family: 'Consolas', monospace; font-size: 9px;")
        self.progress_log.setPlaceholderText("El log de publicación aparecerá aquí...")
        status_layout.addWidget(self.progress_log)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
    


    # ==================== AI GENERATOR EDITOR METHODS ====================
    
    def insert_emoji_title(self):
        """Insert emoji into title field (from AI Generator)"""
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

    def insert_emoji_voice_title(self):
        """Insert emoji into voice title field"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.voice_title_edit.cursorPosition()
                    text = self.voice_title_edit.text()
                    self.voice_title_edit.setText(text[:cursor] + emoji + text[cursor:])
                    self.voice_title_edit.setCursorPosition(cursor + len(emoji))
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def insert_emoji_content(self):
        """Insert emoji into content area (from AI Generator)"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    insert_emoji_textedit(self.edit_area, emoji)
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def select_image_for_preview(self):
        """Select image/video/GIF for preview (from AI Generator)"""
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Media",
            "", "Archivos de Media (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.gif);;Imágenes (*.png *.jpg *.jpeg *.webp *.bmp);;Videos (*.mp4 *.mov *.avi *.mkv);;GIFs (*.gif)"
        )
        
        if file:
            self.presentation_media_path = file
            ext = file.lower().split('.')[-1]
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                self.presentation_media_type = "photo"
                icon = "🖼️"
            elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                self.presentation_media_type = "video"
                icon = "🎥"
            elif ext == 'gif':
                self.presentation_media_type = "animation"
                icon = "🎭"
            else:
                self.presentation_media_type = "document"
                icon = "📎"
            
            filename = os.path.basename(file)
            self.media_status_label.setText(f"{icon} {filename}")
            self.media_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.update_preview()
            self.update_post_statistics()

    def post_preview_select_image(self, event):
        """Handle image selection from preview click (from AI Generator)"""
        self.select_image_for_preview()

    def open_button_config(self):
        """Open button configuration dialog"""
        if ButtonConfigDialog:
            dlg = ButtonConfigDialog(self, self.telegram_buttons)
            if dlg.exec():
                self.telegram_buttons = dlg.get_values()
                # Actualizar inmediatamente el previsualizador y estadísticas
                self.update_preview()
                self.update_post_statistics()
        else:
            QMessageBox.information(self, "Info", "Configuración de botones no disponible")

    def update_preview(self):
        """Update post preview using PostPreviewWidget (same logic as AI Generator)"""
        if hasattr(self, 'post_preview') and self.post_preview:
            # Get content parts
            title = self.title_edit.text().strip()
            content = emoji_document_to_plaintext(self.edit_area.document()).strip()
            cta = self.cta_edit.text().strip()
            hashtags = self.hashtags_edit.text().strip()
            
            # Combine content using AI Generator logic
            full_text = ""
            if title:
                full_text += f"{title}\n\n"
            if content:
                full_text += content
            if cta or hashtags:
                full_text += "\n\n"
            if cta:
                full_text += f"{cta}"
            if hashtags:
                if cta:
                    full_text += f"\n{hashtags}"
                else:
                    full_text += hashtags
            
            # Format text using same logic as AI Generator
            formatted_text = self.format_telegram_post(full_text)
            
            # Update preview using correct methods (same as AI Generator)
            self.post_preview.set_html(formatted_text)
            self.post_preview.set_image(self.presentation_media_path)
            
            # Update buttons using same format as AI Generator - SIEMPRE mostrar botones configurados
            keyboard = []
            if self.telegram_buttons and any(self.telegram_buttons):
                for row in self.telegram_buttons:
                    if row:  # Si la fila no está vacía
                        row_buttons = []
                        for btn in row:
                            if isinstance(btn, dict) and "text" in btn and btn["text"].strip():
                                if "url" in btn and btn["url"].strip():
                                    row_buttons.append({"text": btn["text"], "url": btn["url"]})
                                else:
                                    row_buttons.append({"text": btn["text"]})
                        if row_buttons:
                            keyboard.append(row_buttons)
            
            # Siempre actualizar los botones (aunque esté vacío)
            self.post_preview.set_buttons(keyboard, "row")
                
        elif hasattr(self, 'preview_area'):
            # Fallback text preview
            title = self.title_edit.text().strip()
            content = emoji_document_to_plaintext(self.edit_area.document()).strip()
            cta = self.cta_edit.text().strip()
            hashtags = self.hashtags_edit.text().strip()
            
            preview_text = ""
            if title:
                preview_text += f"📝 Título: {title}\n\n"
            if content:
                preview_text += f"💬 Contenido:\n{content}\n\n"
            if self.presentation_media_path:
                filename = os.path.basename(self.presentation_media_path)
                preview_text += f"📎 Media: {filename}\n\n"
            if cta:
                preview_text += f"🎯 CTA: {cta}\n"
            if hashtags:
                preview_text += f"🏷️ Tags: {hashtags}\n"
            
            # Mostrar botones en preview de texto también
            if self.telegram_buttons and any(self.telegram_buttons):
                preview_text += "\n🔗 Botones configurados:\n"
                for i, row in enumerate(self.telegram_buttons):
                    if row:
                        for j, btn in enumerate(row):
                            if isinstance(btn, dict) and "text" in btn and btn["text"].strip():
                                preview_text += f"   [{btn['text']}]"
                                if "url" in btn and btn["url"].strip():
                                    preview_text += f" -> {btn['url']}"
                                preview_text += "\n"
            
            self.preview_area.setPlainText(preview_text)
        
        # Actualizar estadísticas del post
        self.update_post_statistics()

    def update_character_counter(self):
        """Update character counter for content"""
        content = emoji_document_to_plaintext(self.edit_area.document())
        char_count = len(content)
        word_count = len([word for word in content.split() if word])
        self.char_counter.setText(f"{char_count} caracteres ({word_count} palabras)")

    def select_voice_file(self):
        """Select voice/audio file for premium note"""
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de Audio",
            "", "Archivos de Audio (*.mp3 *.wav *.ogg *.m4a *.aac *.flac)"
        )
        
        if file:
            self.voice_selected_file = file
            filename = os.path.basename(file)
            self.voice_file_label.setText(f"🎵 {filename}")
            self.voice_file_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.voice_selected_file = None
            self.voice_file_label.setText("Ningún archivo seleccionado")
            self.voice_file_label.setStyleSheet("color: gray; font-style: italic;")

    def connect_all_events(self):
        """Connect all UI events"""
        pass  # Events already connected in setup methods

    def prepare_post_data(self):
        """Prepare post data for publishing"""
        # Get content with formatting (bold, italic, etc preserved)
        raw_content = emoji_document_to_plaintext(self.edit_area.document()).strip()
        title = self.title_edit.text().strip()

        # Apply Telegram formatting to content
        main_content = prepare_content_for_telegram(raw_content)
        full_content = build_post_content(title, main_content)

        # Get CTA and hashtags
        cta = self.cta_edit.text().strip()
        hashtags = self.hashtags_edit.text().strip()
        cta_hashtags = ""
        if cta or hashtags:
            if cta:
                cta_hashtags += cta
            if hashtags:
                if cta:
                    cta_hashtags += f"\n{hashtags}"
                else:
                    cta_hashtags = hashtags
        
        # Get voice data
        voice_data = {}
        if self.voice_selected_file:
            voice_data = {
                'voice_file': self.voice_selected_file,
                'voice_title': self.voice_title_edit.text().strip(),
                'voice_description': self.voice_description_edit.toPlainText().strip(),
                'voice_quality': 'ultra'  # Always maximum quality
            }
        
        # Reset media status if no media selected
        if not self.presentation_media_path:
            self.media_status_label.setText("Sin media seleccionado")
            self.media_status_label.setStyleSheet("color: gray; font-style: italic;")
        
        return {
            'main_content': full_content if full_content else None,
            'presentation_path': self.presentation_media_path,
            'presentation_type': self.presentation_media_type,
            'cta_hashtags': cta_hashtags if cta_hashtags else None,
            'reply_markup': json.dumps({"inline_keyboard": self.telegram_buttons}) if self.telegram_buttons and self.telegram_buttons[0] else None,
            **voice_data
        }

    def load_post_data(self, post_data: dict) -> None:
        """Load a given post_data dict into the publish tab fields.
        The expected keys match `prepare_post_data` output.
        """
        # Title and main content
        main_content = post_data.get('main_content') or ""
        # If the content includes a bold title inserted from AI tab, try to extract it
        # If it's HTML <b>title</b> we can extract a simple plain title
        title = ""
        if main_content.startswith('<b>') and '</b>' in main_content:
            try:
                t_end = main_content.index('</b>')
                title = re.sub('<.*?>', '', main_content[3:t_end])
                main_content = main_content[t_end+4:].strip()
            except Exception:
                # fallback to no splitting
                pass

        self.title_edit.setText(title)
        self.edit_area.setHtml(main_content if main_content else '')
        self.edit_area.moveCursor(self.edit_area.textCursor().End)

        # Presentation media
        path = post_data.get('presentation_path')
        ptype = post_data.get('presentation_type')
        self.presentation_media_path = path
        self.presentation_media_type = ptype
        if path:
            # Update preview helper
            self.post_preview.set_image(path)
            if hasattr(self, 'current_media_label'):
                self.current_media_label.setText(Path(path).name)
            if hasattr(self, 'lbl_media_info'):
                self.lbl_media_info.setText(Path(path).name)
        else:
            self.post_preview.set_image(None)
            self.current_media_label.setText('Ninguno')

        # Buttons/reply_markup
        reply_markup = post_data.get('reply_markup')
        if reply_markup:
            try:
                payload = json.loads(reply_markup) if isinstance(reply_markup, str) else reply_markup
                self.telegram_buttons = payload.get('inline_keyboard', [[]])
            except Exception:
                self.telegram_buttons = [[]]
        else:
            self.telegram_buttons = [[]]
        self.update_preview()

        # CTA and hashtags
        cta_hashtags = post_data.get('cta_hashtags')
        if cta_hashtags and isinstance(cta_hashtags, str):
            parts = cta_hashtags.split('\n')
            self.cta_edit.setText(parts[0] if parts else "")
            self.hashtags_edit.setText('\n'.join(parts[1:]) if len(parts) > 1 else "")

        # Voice
        if post_data.get('voice_file'):
            self.voice_selected_file = post_data.get('voice_file')
            if hasattr(self, 'lbl_voice_info'):
                self.lbl_voice_info.setText(Path(self.voice_selected_file).name)
            # keep compatibility with other name
            if hasattr(self, 'voice_file_label'):
                self.voice_file_label.setText(Path(self.voice_selected_file).name)
            self.voice_title_edit.setText(post_data.get('voice_title', ''))
            self.voice_description_edit.setPlainText(post_data.get('voice_description', ''))

        # Update UI labels & statistics
        self.update_preview()
        self.update_post_statistics()

    def publish_post(self):
        """Publish post to Telegram"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Advertencia", "Ya hay una publicación en proceso")
            return
        
        # Validate that we have at least some content
        post_data = self.prepare_post_data()
        
        if not any([post_data.get('main_content'), post_data.get('presentation_path'), 
                   post_data.get('voice_file'), post_data.get('cta_hashtags')]):
            QMessageBox.warning(self, "Error", "Debes agregar al menos un título o contenido")
            return
        
        # Start publishing
        self.worker = PublishWorker(post_data, self.config)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        
        # Update UI
        self.publish_button.setEnabled(False)
        self.status_label.setText("📤 Publicación en proceso")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_log.setVisible(True)
        self.progress_log.clear()
        
        self.worker.start()

    def on_progress(self, message):
        """Handle progress updates"""
        self.progress_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.progress_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_finished(self, success, message):
        """Handle publishing completion"""
        self.publish_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ Publicado exitosamente")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Éxito", message)
            
            # Clear form after successful publish
            self.edit_area.clear()
            self.title_edit.clear()
            self.cta_edit.clear()
            self.hashtags_edit.clear()
            self.presentation_media_path = None
            self.presentation_media_type = None
            self.media_status_label.setText("Sin media seleccionado")
            self.media_status_label.setStyleSheet("color: gray; font-style: italic;")
            self.update_preview()
        else:
            self.status_label.setText("❌ Error en publicación")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Error", message)



    def insert_emoji_voice_title(self):
        """Insert emoji into voice title field"""
        if EmojiPicker:
            picker = EmojiPicker(self)
            if picker.exec():
                emoji = picker.selected_emoji
                if emoji:
                    cursor = self.voice_title_edit.cursorPosition()
                    text = self.voice_title_edit.text()
                    self.voice_title_edit.setText(text[:cursor] + emoji + text[cursor:])
                    self.voice_title_edit.setCursorPosition(cursor + len(emoji))
        else:
            QMessageBox.information(self, "Info", "Función de emoji no disponible")

    def format_telegram_post(self, text):
        """Format text for Telegram preview (same logic as AI Generator)"""
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
        return "<br>".join(formatted)

    def update_post_statistics(self):
        """Update real-time post statistics"""
        # Calcular caracteres totales
        title = self.title_edit.text().strip()
        content = emoji_document_to_plaintext(self.edit_area.document()).strip()
        cta = self.cta_edit.text().strip()
        hashtags = self.hashtags_edit.text().strip()
        
        full_text = ""
        if title:
            full_text += title + "\n\n"
        if content:
            full_text += content
        if cta or hashtags:
            full_text += "\n\n"
        if cta:
            full_text += cta
        if hashtags:
            if cta:
                full_text += "\n" + hashtags
            else:
                full_text += hashtags
        
        char_count = len(full_text)
        word_count = len([word for word in full_text.split() if word])
        
        # Actualizar labels de estadísticas
        self.current_chars_label.setText(f"{char_count}/4096")
        if char_count > 4096:
            self.current_chars_label.setStyleSheet("color: red; font-weight: bold;")
        elif char_count > 3500:
            self.current_chars_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.current_chars_label.setStyleSheet("color: green;")
        
        self.current_words_label.setText(str(word_count))
        
        # Actualizar info de media
        if self.presentation_media_path:
            filename = os.path.basename(self.presentation_media_path)
            try:
                file_size = os.path.getsize(self.presentation_media_path) / (1024 * 1024)  # MB
                self.current_media_label.setText(f"{filename} ({file_size:.1f} MB)")
            except Exception:
                # If the file does not exist or can't be read, show only the filename
                self.current_media_label.setText(f"{filename} (desconocido)")
            
            # Verificar límites de tamaño
            if self.presentation_media_type == "photo" and file_size > 10:
                self.current_media_label.setStyleSheet("color: red; font-weight: bold;")
            elif self.presentation_media_type in ["video", "animation"] and file_size > 50:
                self.current_media_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.current_media_label.setStyleSheet("color: green;")
        else:
            self.current_media_label.setText("Ninguno")
            self.current_media_label.setStyleSheet("color: gray;")
        
        # Contar botones configurados
        button_count = 0
        if self.telegram_buttons and any(self.telegram_buttons):
            for row in self.telegram_buttons:
                if row:
                    for btn in row:
                        if isinstance(btn, dict) and "text" in btn and btn["text"].strip():
                            button_count += 1
        
        self.current_buttons_label.setText(str(button_count))
        if button_count > 0:
            self.current_buttons_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.current_buttons_label.setStyleSheet("color: gray;")


