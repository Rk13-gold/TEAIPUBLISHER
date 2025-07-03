
# Import unified theme system
try:
    from gui.telegram_theme_simple import TelegramThemeSimple as TelegramTheme
except ImportError:
    TelegramTheme = None

"""
Simplified Channel Manager Tab for testing
"""
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QProgressBar,
    QTextEdit, QSplitter, QComboBox, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
from datetime import datetime
import requests
import json


class ChannelExtractorWorker(QThread):
    """Professional worker to extract bot-administered channels and groups"""
    progress = Signal(str)  # Progress message
    channel_found = Signal(dict)  # Channel data: {id, title, type, username}
    finished = Signal(bool, str, list)  # Success, message, channels_list
    
    def __init__(self, bot_token):
        super().__init__()
        self.bot_token = bot_token
        self.channels = []
        
    def run(self):
        """Extract all channels and groups administered by the bot"""
        try:
            self.progress.emit("🔍 Iniciando extracción de canales administrados...")
            
            # Step 1: Get bot information
            self.progress.emit("🤖 Verificando información del bot...")
            bot_info = self.get_bot_info()
            if not bot_info:
                self.finished.emit(False, "Error: Token de bot inválido", [])
                return
                
            bot_username = bot_info.get('username', 'Unknown')
            self.progress.emit(f"✅ Bot conectado: @{bot_username}")
            
            # Step 2: Get updates to find administered channels/groups
            self.progress.emit("📡 Obteniendo actualizaciones del bot...")
            updates = self.get_bot_updates()
            
            # Step 3: Extract unique channels from updates
            self.progress.emit("🔍 Analizando canales y grupos...")
            extracted_channels = self.extract_channels_from_updates(updates)
            
            # Step 4: Get detailed info for each channel
            self.progress.emit("📊 Obteniendo información detallada...")
            detailed_channels = []
            
            for channel in extracted_channels:
                try:
                    chat_info = self.get_chat_info(channel['id'])
                    if chat_info:
                        # Check if bot is admin
                        is_admin = self.check_bot_admin_status(channel['id'])
                        
                        detailed_info = {
                            'id': channel['id'],
                            'title': chat_info.get('title', 'Sin título'),
                            'type': chat_info.get('type', 'unknown'),
                            'username': chat_info.get('username', ''),
                            'description': chat_info.get('description', ''),
                            'member_count': chat_info.get('member_count', 0),
                            'is_admin': is_admin,
                            'permissions': self.get_bot_permissions(channel['id']) if is_admin else []
                        }
                        
                        detailed_channels.append(detailed_info)
                        self.channel_found.emit(detailed_info)
                        self.progress.emit(f"✅ Procesado: {detailed_info['title']}")
                        
                except Exception as e:
                    self.progress.emit(f"⚠️ Error procesando canal {channel['id']}: {str(e)}")
                    continue
            
            self.channels = detailed_channels
            
            if detailed_channels:
                admin_count = len([ch for ch in detailed_channels if ch['is_admin']])
                self.progress.emit(f"🎉 Extracción completada: {len(detailed_channels)} canales encontrados")
                self.progress.emit(f"👑 El bot es administrador en {admin_count} canales/grupos")
                self.finished.emit(True, f"Se encontraron {len(detailed_channels)} canales/grupos", detailed_channels)
            else:
                self.finished.emit(False, "No se encontraron canales administrados", [])
                
        except Exception as e:
            self.finished.emit(False, f"Error inesperado: {str(e)}", [])
    
    def get_bot_info(self):
        """Get bot information"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return result.get('result')
            else:
                return None
        except:
            return None
    
    def get_bot_updates(self, limit=100):
        """Get bot updates to find conversations"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {'limit': limit, 'offset': -limit}  # Get recent updates
            response = requests.get(url, params=params, timeout=15)
            result = response.json()
            
            if result.get('ok'):
                return result.get('result', [])
            else:
                return []
        except:
            return []
    
    def extract_channels_from_updates(self, updates):
        """Extract unique channels from bot updates"""
        channels = {}
        
        for update in updates:
            # Check different types of updates
            chat = None
            
            if 'message' in update:
                chat = update['message'].get('chat')
            elif 'edited_message' in update:
                chat = update['edited_message'].get('chat')
            elif 'channel_post' in update:
                chat = update['channel_post'].get('chat')
            elif 'edited_channel_post' in update:
                chat = update['edited_channel_post'].get('chat')
            elif 'my_chat_member' in update:
                chat = update['my_chat_member'].get('chat')
            elif 'chat_member' in update:
                chat = update['chat_member'].get('chat')
            
            if chat:
                chat_id = chat.get('id')
                chat_type = chat.get('type')
                
                # Only process channels, supergroups, and groups
                if chat_type in ['channel', 'supergroup', 'group'] and chat_id:
                    channels[chat_id] = {
                        'id': chat_id,
                        'title': chat.get('title', 'Sin título'),
                        'type': chat_type,
                        'username': chat.get('username', '')
                    }
        
        return list(channels.values())
    
    def get_chat_info(self, chat_id):
        """Get detailed chat information"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getChat"
            params = {'chat_id': chat_id}
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return result.get('result')
            else:
                return None
        except:
            return None
    
    def check_bot_admin_status(self, chat_id):
        """Check if bot is administrator in the chat"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getChatMember"
            bot_info = self.get_bot_info()
            if not bot_info:
                return False
                
            bot_id = bot_info.get('id')
            params = {'chat_id': chat_id, 'user_id': bot_id}
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                member_info = result.get('result', {})
                status = member_info.get('status', '')
                return status in ['administrator', 'creator']
            else:
                return False
        except:
            return False
    
    def get_bot_permissions(self, chat_id):
        """Get bot permissions in the chat"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getChatMember"
            bot_info = self.get_bot_info()
            if not bot_info:
                return []
                
            bot_id = bot_info.get('id')
            params = {'chat_id': chat_id, 'user_id': bot_id}
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                member_info = result.get('result', {})
                permissions = []
                
                # Extract permissions
                if member_info.get('can_post_messages'):
                    permissions.append('Publicar mensajes')
                if member_info.get('can_edit_messages'):
                    permissions.append('Editar mensajes')
                if member_info.get('can_delete_messages'):
                    permissions.append('Eliminar mensajes')
                if member_info.get('can_invite_users'):
                    permissions.append('Invitar usuarios')
                if member_info.get('can_restrict_members'):
                    permissions.append('Restringir miembros')
                if member_info.get('can_pin_messages'):
                    permissions.append('Fijar mensajes')
                if member_info.get('can_promote_members'):
                    permissions.append('Promover miembros')
                
                return permissions
            else:
                return []
        except:
            return []


class SimpleChannelTab(QWidget):
    """Simplified channel management tab for testing"""
    
    def __init__(self):
        # Apply unified theme
        if TelegramTheme:
            TelegramTheme.apply_simple_theme(self)
        super().__init__()
        self.monitored_channels = set()
        self.extracted_channels = []  # Store extracted channels
        self.extractor_worker = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Enhanced Channel Manager (Simplified)")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # ==================== AUTO EXTRACTION SECTION ====================
        # Professional Bot Channel Extractor
        extractor_group = QGroupBox("🤖 Extractor Automático de Canales")
        extractor_layout = QVBoxLayout(extractor_group)
        
        # Token input section
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("🔑 Token del Bot:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Introduce el token de tu bot de Telegram...")
        self.token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.token_input)
        
        # Show/hide token button
        self.toggle_token_btn = QPushButton("👁️")
        self.toggle_token_btn.setMaximumWidth(30)
        self.toggle_token_btn.clicked.connect(self.toggle_token_visibility)
        token_layout.addWidget(self.toggle_token_btn)
        
        extractor_layout.addLayout(token_layout)
        
        # Extract button and progress
        extract_layout = QHBoxLayout()
        self.extract_btn = QPushButton("🔍 EXTRAER CANALES ADMINISTRADOS")
        self.extract_btn.setMinimumHeight(40)
        self.extract_btn.clicked.connect(self.extract_bot_channels)
        extract_layout.addWidget(self.extract_btn)
        
        # Progress bar
        self.extraction_progress = QProgressBar()
        self.extraction_progress.setVisible(False)
        extract_layout.addWidget(self.extraction_progress)
        
        extractor_layout.addLayout(extract_layout)
        
        # Extraction results table
        self.extracted_table = QTableWidget()
        self.extracted_table.setColumnCount(6)
        self.extracted_table.setHorizontalHeaderLabels([
            "Canal/Grupo", "ID", "Tipo", "Miembros", "Admin", "Acciones"
        ])
        self.extracted_table.setMaximumHeight(200)
        self.extracted_table.setSelectionBehavior(QTableWidget.SelectRows)
        extractor_layout.addWidget(self.extracted_table)
        
        # Extraction actions
        extract_actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("✅ Seleccionar Todos")
        self.select_all_btn.clicked.connect(self.select_all_extracted)
        
        self.add_selected_btn = QPushButton("➕ Agregar Seleccionados")
        self.add_selected_btn.clicked.connect(self.add_selected_extracted)
        
        self.export_btn = QPushButton("📤 Exportar Lista")
        self.export_btn.clicked.connect(self.export_channels_list)
        
        extract_actions_layout.addWidget(self.select_all_btn)
        extract_actions_layout.addWidget(self.add_selected_btn)
        extract_actions_layout.addWidget(self.export_btn)
        extract_actions_layout.addStretch()
        
        extractor_layout.addLayout(extract_actions_layout)
        
        main_layout.addWidget(extractor_group)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Search section
        search_group = QGroupBox("Channel Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search input
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter channel username (e.g., python, telegram)...")
        
        self.search_btn = QPushButton("Add Channel")
        self.search_btn.clicked.connect(self.add_channel)
        
        search_input_layout.addWidget(QLabel("Channel:"))
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_input_layout)
        
        main_layout.addWidget(search_group)
        
        # Channels table
        channels_group = QGroupBox("Managed Channels")
        channels_layout = QVBoxLayout(channels_group)
        
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(4)
        self.channels_table.setHorizontalHeaderLabels([
            "Channel", "Date Added", "Status", "Actions"
        ])
        self.channels_table.setSelectionBehavior(QTableWidget.SelectRows)
        channels_layout.addWidget(self.channels_table)
        
        # Channel buttons
        channel_btn_layout = QHBoxLayout()
        self.remove_channel_btn = QPushButton("Remove Selected")
        self.remove_channel_btn.clicked.connect(self.remove_selected_channels)
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_channels)
        
        channel_btn_layout.addWidget(self.remove_channel_btn)
        channel_btn_layout.addWidget(self.clear_all_btn)
        channels_layout.addLayout(channel_btn_layout)
        
        main_layout.addWidget(channels_group)
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(150)
        self.activity_log.setReadOnly(True)
        log_layout.addWidget(self.activity_log)
        
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_activity_log)
        log_layout.addWidget(self.clear_log_btn)
        
        main_layout.addWidget(log_group)
        
        # Info section
        info_group = QGroupBox("Enhanced Features Info")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
🚀 <b>Enhanced Features Available:</b><br>
• Intelligent caching system for faster channel queries<br>
• Batch operations for multiple channels<br>
• Real-time monitoring capabilities<br>
• Persistent configuration management<br>
• Advanced search functionality<br><br>
<b>Note:</b> This is a simplified version for testing. 
Run the full application to access all features.
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        main_layout.addWidget(info_group)
        
        # Initial log message
        self.log_activity("Enhanced Channel Manager initialized successfully")
        self.log_activity("Ready to manage multiple Telegram channels")
    
    def add_channel(self):
        """Add a channel to the list"""
        channel = self.search_input.text().strip()
        if not channel:
            QMessageBox.warning(self, "Warning", "Please enter a channel username")
            return
        
        # Remove @ if present
        if channel.startswith('@'):
            channel = channel[1:]
        
        if channel in self.monitored_channels:
            QMessageBox.information(self, "Info", f"Channel @{channel} is already added")
            return
        
        # Add to set
        self.monitored_channels.add(channel)
        
        # Update table
        self.update_channels_table()
        
        # Clear input
        self.search_input.clear()
        
        # Log activity
        self.log_activity(f"Added channel: @{channel}")
        
        QMessageBox.information(self, "Success", f"Channel @{channel} added successfully!")
    
    def remove_selected_channels(self):
        """Remove selected channels"""
        selected_rows = set()
        for item in self.channels_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select channels to remove")
            return
        
        channels_to_remove = []
        for row in selected_rows:
            channel_item = self.channels_table.item(row, 0)
            if channel_item:
                channel = channel_item.text().replace('@', '')
                channels_to_remove.append(channel)
        
        # Remove from set
        for channel in channels_to_remove:
            self.monitored_channels.discard(channel)
        
        # Update table
        self.update_channels_table()
        
        # Log activity
        self.log_activity(f"Removed {len(channels_to_remove)} channels")
        
        QMessageBox.information(self, "Success", f"Removed {len(channels_to_remove)} channels")
    
    def clear_all_channels(self):
        """Clear all channels"""
        if not self.monitored_channels:
            QMessageBox.information(self, "Info", "No channels to clear")
            return
        
        reply = QMessageBox.question(
            self, "Confirm", 
            f"Are you sure you want to remove all {len(self.monitored_channels)} channels?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = len(self.monitored_channels)
            self.monitored_channels.clear()
            self.update_channels_table()
            self.log_activity(f"Cleared all {count} channels")
            QMessageBox.information(self, "Success", f"Cleared all {count} channels")
    
    def update_channels_table(self):
        """Update the channels table"""
        channels_list = sorted(list(self.monitored_channels))
        self.channels_table.setRowCount(len(channels_list))
        
        for row, channel in enumerate(channels_list):
            self.channels_table.setItem(row, 0, QTableWidgetItem(f"@{channel}"))
            self.channels_table.setItem(row, 1, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M")))
            self.channels_table.setItem(row, 2, QTableWidgetItem("Added"))
            self.channels_table.setItem(row, 3, QTableWidgetItem("Ready"))
    
    def clear_activity_log(self):
        """Clear activity log"""
        self.activity_log.clear()
        self.log_activity("Activity log cleared")
    
    def log_activity(self, message: str):
        """Log activity message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    # ==================== CHANNEL EXTRACTOR METHODS ====================
    
    def toggle_token_visibility(self):
        """Toggle token visibility"""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.toggle_token_btn.setText("🔒")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.toggle_token_btn.setText("👁️")
    
    def extract_bot_channels(self):
        """Extract channels and groups administered by the bot"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "Por favor ingresa un token de bot válido")
            return
        
        # Check if worker is already running
        if self.extractor_worker and self.extractor_worker.isRunning():
            QMessageBox.warning(self, "En proceso", "La extracción ya está en progreso")
            return
        
        # Clear previous results
        self.extracted_channels = []
        self.extracted_table.setRowCount(0)
        
        # Show progress
        self.extraction_progress.setValue(0)
        self.extraction_progress.setRange(0, 0)  # Indeterminate
        self.extraction_progress.setVisible(True)
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("⏳ EXTRAYENDO CANALES...")
        
        # Log activity
        self.log_activity("🔍 Iniciando extracción de canales administrados...")
        
        # Create and start worker
        self.extractor_worker = ChannelExtractorWorker(token)
        self.extractor_worker.progress.connect(self.on_extractor_progress)
        self.extractor_worker.channel_found.connect(self.on_channel_found)
        self.extractor_worker.finished.connect(self.on_extractor_finished)
        self.extractor_worker.start()
    
    def on_extractor_progress(self, message):
        """Handle progress updates from extractor"""
        self.log_activity(message)
    
    def on_channel_found(self, channel_data):
        """Add a new channel to the extracted table"""
        row = self.extracted_table.rowCount()
        self.extracted_table.insertRow(row)
        
        # Fill row data
        self.extracted_table.setItem(row, 0, QTableWidgetItem(channel_data['title']))
        self.extracted_table.setItem(row, 1, QTableWidgetItem(str(channel_data['id'])))
        
        # Type with icon
        type_text = ""
        if channel_data['type'] == 'channel':
            type_text = "📢 Canal"
        elif channel_data['type'] == 'supergroup':
            type_text = "👥 Supergrupo"
        elif channel_data['type'] == 'group':
            type_text = "👥 Grupo"
        else:
            type_text = f"❓ {channel_data['type']}"
        self.extracted_table.setItem(row, 2, QTableWidgetItem(type_text))
        
        # Member count
        member_count = channel_data.get('member_count', 0)
        self.extracted_table.setItem(row, 3, QTableWidgetItem(f"{member_count:,}"))
        
        # Admin status
        is_admin = channel_data.get('is_admin', False)
        admin_text = "✅ Sí" if is_admin else "❌ No"
        admin_item = QTableWidgetItem(admin_text)
        admin_item.setTextAlignment(Qt.AlignCenter)
        self.extracted_table.setItem(row, 4, admin_item)
        
        # Add checkbox for action
        add_checkbox = QCheckBox()
        add_checkbox.setChecked(is_admin)  # Pre-check if bot is admin
        self.extracted_table.setCellWidget(row, 5, add_checkbox)
        
        # Update table
        self.extracted_table.resizeColumnsToContents()
    
    def on_extractor_finished(self, success, message, channels):
        """Handle extraction completion"""
        # Hide progress
        self.extraction_progress.setVisible(False)
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("🔍 EXTRAER CANALES ADMINISTRADOS")
        
        # Store extracted channels
        self.extracted_channels = channels
        
        # Log activity
        if success:
            self.log_activity(f"✅ {message}")
            QMessageBox.information(self, "Éxito", message)
            
            # Update columns size
            self.extracted_table.resizeColumnsToContents()
            
            # Show result message
            admin_count = len([ch for ch in channels if ch['is_admin']])
            QMessageBox.information(
                self, 
                "Extracción Completada", 
                f"Se encontraron {len(channels)} canales/grupos.\n"
                f"El bot es administrador en {admin_count} de ellos.\n\n"
                f"✅ Selecciona los que quieres agregar y haz clic en 'Agregar Seleccionados'"
            )
        else:
            self.log_activity(f"❌ {message}")
            QMessageBox.critical(self, "Error", message)
    
    def select_all_extracted(self):
        """Select all extracted channels"""
        for row in range(self.extracted_table.rowCount()):
            checkbox = self.extracted_table.cellWidget(row, 5)
            if checkbox:
                checkbox.setChecked(True)
        
        self.log_activity("✅ Todos los canales seleccionados")
    
    def add_selected_extracted(self):
        """Add selected channels to monitored list"""
        selected_channels = []
        
        for row in range(self.extracted_table.rowCount()):
            checkbox = self.extracted_table.cellWidget(row, 5)
            if checkbox and checkbox.isChecked():
                channel_item = self.extracted_table.item(row, 0)  # Title
                channel_id = self.extracted_table.item(row, 1).text()  # ID
                
                if channel_item:
                    channel_name = channel_item.text()
                    selected_channels.append((channel_name, channel_id))
        
        if not selected_channels:
            QMessageBox.warning(self, "Aviso", "No has seleccionado ningún canal")
            return
        
        # Add to monitored channels
        added_count = 0
        for channel_name, channel_id in selected_channels:
            key = f"{channel_name} ({channel_id})"
            if key not in self.monitored_channels:
                self.monitored_channels.add(key)
                added_count += 1
        
        # Update table
        self.update_channels_table()
        
        # Log activity
        self.log_activity(f"➕ Agregados {added_count} canales al monitoreo")
        
        QMessageBox.information(
            self,
            "Canales agregados",
            f"Se han agregado {added_count} canales/grupos al monitoreo."
        )
    
    def export_channels_list(self):
        """Export channels list to JSON file"""
        if not self.extracted_channels:
            QMessageBox.warning(self, "Aviso", "No hay canales para exportar")
            return
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Exportar Lista de Canales", 
            "", 
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # Ensure extension
        if not file_path.endswith('.json'):
            file_path += '.json'
        
        # Export data
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_channels, f, indent=4, ensure_ascii=False)
            
            self.log_activity(f"📤 Lista de canales exportada a: {file_path}")
            QMessageBox.information(
                self, 
                "Exportación Completada", 
                f"La lista de {len(self.extracted_channels)} canales ha sido exportada correctamente a:\n{file_path}"
            )
        except Exception as e:
            self.log_activity(f"❌ Error al exportar: {str(e)}")
            QMessageBox.critical(self, "Error", f"No se pudo exportar el archivo: {str(e)}")
