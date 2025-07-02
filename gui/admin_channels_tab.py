
"""
Professional Admin Channels Tab - Shows all channels and groups administered by the configured bot
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QGroupBox, QHeaderView,
    QLineEdit, QComboBox, QTextEdit, QSplitter, QFrame,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QSpinBox, QTabWidget, QScrollArea, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from services.enhanced_telegram_client import EnhancedTelegramClient
from services.telegram_bot_client import TelegramBotClient, BotChannelInfo
from core.config import Config


@dataclass
class AdminChannelInfo:
    """Data class for admin channel information"""
    id: int
    title: str
    username: Optional[str]
    type: str  # 'channel', 'group', 'supergroup'
    members_count: int
    is_private: bool
    is_verified: bool
    is_scam: bool
    created_date: Optional[datetime]
    description: Optional[str]
    invite_link: Optional[str]
    admin_rights: Dict[str, bool]
    last_message_date: Optional[datetime]


class BotSearchWorker(QThread):
    """Worker thread for searching channels by ID using bot token"""
    
    channels_found = Signal(list)
    progress_updated = Signal(int, str)
    error_occurred = Signal(str)
    
    def __init__(self, config: Config, channel_ids: List[str]):
        super().__init__()
        self.config = config
        self.channel_ids = channel_ids
        self.bot_client = None
        self._stop_requested = False
    
    def run(self):
        """Main thread execution"""
        try:
            self._search_channels_by_ids()
        except Exception as e:
            self.error_occurred.emit(f"Error searching channels: {str(e)}")
    
    def _search_channels_by_ids(self):
        """Search channels using bot token"""
        try:
            self.progress_updated.emit(10, "Initializing bot client...")
            
            # Initialize bot client
            if not self.config.bot_token:
                self.error_occurred.emit("Bot token not configured")
                return
            
            self.bot_client = TelegramBotClient(self.config.bot_token)
            
            # Test connection
            if not self.bot_client.test_connection():
                self.error_occurred.emit("Failed to connect with bot token")
                return
            
            self.progress_updated.emit(20, "Bot connection established")
            
            found_channels = []
            total_ids = len(self.channel_ids)
            
            for i, channel_id in enumerate(self.channel_ids):
                if self._stop_requested:
                    break
                
                self.progress_updated.emit(
                    20 + (i / total_ids) * 70, 
                    f"Searching channel: {channel_id}"
                )
                
                try:
                    channel_info = self.bot_client.get_chat_info(channel_id.strip())
                    if channel_info:
                        # Check bot permissions
                        permissions = self.bot_client.validate_bot_permissions(str(channel_info.id))
                        
                        # Convert to AdminChannelInfo format
                        admin_channel = AdminChannelInfo(
                            id=channel_info.id,
                            title=channel_info.title,
                            username=channel_info.username,
                            type=channel_info.type,
                            members_count=channel_info.member_count or 0,
                            is_private=channel_info.username is None,
                            is_verified=channel_info.is_verified,
                            is_scam=channel_info.is_scam,
                            created_date=None,
                            description=channel_info.description,
                            invite_link=channel_info.invite_link,
                            admin_rights=permissions,
                            last_message_date=None
                        )
                        found_channels.append(admin_channel)
                        
                except Exception as e:
                    logging.warning(f"Could not get info for {channel_id}: {e}")
            
            self.progress_updated.emit(95, "Finalizing results...")
            self.channels_found.emit(found_channels)
            self.progress_updated.emit(100, "Search complete!")
            
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def stop(self):
        """Stop the worker thread"""
        self._stop_requested = True


class AdminChannelWorker(QThread):
    """Worker thread for fetching admin channels"""
    
    channels_loaded = Signal(list)
    progress_updated = Signal(int, str)
    error_occurred = Signal(str)
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.client = None
        self._stop_requested = False
    
    def run(self):
        """Main thread execution"""
        try:
            asyncio.run(self._fetch_admin_channels())
        except Exception as e:
            self.error_occurred.emit(f"Error fetching channels: {str(e)}")
    
    async def _fetch_admin_channels(self):
        """Fetch all channels and groups where bot is admin"""
        try:
            self.progress_updated.emit(10, "Connecting to Telegram...")
            
            # Initialize Telegram client
            self.client = EnhancedTelegramClient(
                session_name=self.config.session_name,
                api_id=self.config.api_id,
                api_hash=self.config.api_hash,
                phone_number=self.config.phone_number
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.error_occurred.emit("Bot not authorized. Please configure authentication.")
                return
            
            self.progress_updated.emit(30, "Fetching dialogs...")
            
            # Get all dialogs (conversations)
            dialogs = await self.client.get_dialogs()
            admin_channels = []
            
            total_dialogs = len(dialogs)
            processed = 0
            
            for dialog in dialogs:
                if self._stop_requested:
                    break
                
                entity = dialog.entity
                
                # Check if it's a channel or group and we have admin rights
                if hasattr(entity, 'admin_rights') and entity.admin_rights:
                    try:
                        channel_info = await self._get_channel_info(entity)
                        if channel_info:
                            admin_channels.append(channel_info)
                    except Exception as e:
                        logging.warning(f"Error getting info for {entity.title}: {e}")
                
                processed += 1
                progress = 30 + (processed / total_dialogs) * 60
                self.progress_updated.emit(int(progress), f"Processing {entity.title if hasattr(entity, 'title') else 'Unknown'}...")
            
            self.progress_updated.emit(95, "Finalizing...")
            self.channels_loaded.emit(admin_channels)
            self.progress_updated.emit(100, "Complete!")
            
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
        finally:
            if self.client:
                await self.client.disconnect()
    
    async def _get_channel_info(self, entity) -> Optional[AdminChannelInfo]:
        """Extract detailed information from a channel/group entity"""
        try:
            # Get full entity info
            full_entity = await self.client.get_entity(entity)
            
            # Determine type
            if hasattr(entity, 'megagroup') and entity.megagroup:
                channel_type = 'supergroup'
            elif hasattr(entity, 'broadcast') and entity.broadcast:
                channel_type = 'channel'
            else:
                channel_type = 'group'
            
            # Get admin rights
            admin_rights = {}
            if hasattr(entity, 'admin_rights') and entity.admin_rights:
                admin_rights = {
                    'change_info': entity.admin_rights.change_info,
                    'post_messages': entity.admin_rights.post_messages,
                    'edit_messages': entity.admin_rights.edit_messages,
                    'delete_messages': entity.admin_rights.delete_messages,
                    'ban_users': entity.admin_rights.ban_users,
                    'invite_users': entity.admin_rights.invite_users,
                    'pin_messages': entity.admin_rights.pin_messages,
                    'add_admins': entity.admin_rights.add_admins,
                }
            
            # Get member count
            try:
                participants = await self.client.get_participants(entity, limit=0)
                members_count = participants.total
            except:
                members_count = 0
            
            # Get last message date
            try:
                messages = await self.client.get_messages(entity, limit=1)
                last_message_date = messages[0].date if messages else None
            except:
                last_message_date = None
            
            return AdminChannelInfo(
                id=entity.id,
                title=entity.title,
                username=getattr(entity, 'username', None),
                type=channel_type,
                members_count=members_count,
                is_private=not hasattr(entity, 'username') or entity.username is None,
                is_verified=getattr(entity, 'verified', False),
                is_scam=getattr(entity, 'scam', False),
                created_date=getattr(entity, 'date', None),
                description=getattr(full_entity, 'about', None),
                invite_link=None,  # Would need separate API call
                admin_rights=admin_rights,
                last_message_date=last_message_date
            )
            
        except Exception as e:
            logging.error(f"Error getting channel info for {entity.title}: {e}")
            return None
    
    def stop(self):
        """Stop the worker thread"""
        self._stop_requested = True


class ChannelDetailsDialog(QDialog):
    """Dialog for showing detailed channel information"""
    
    def __init__(self, channel_info: AdminChannelInfo, parent=None):
        super().__init__(parent)
        self.channel_info = channel_info
        self.setWindowTitle(f"Channel Details - {channel_info.title}")
        self.setModal(True)
        self.resize(600, 500)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Basic info tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        basic_layout.addRow("Title:", QLabel(self.channel_info.title))
        basic_layout.addRow("ID:", QLabel(str(self.channel_info.id)))
        basic_layout.addRow("Username:", QLabel(self.channel_info.username or "Private"))
        basic_layout.addRow("Type:", QLabel(self.channel_info.type.title()))
        basic_layout.addRow("Members:", QLabel(f"{self.channel_info.members_count:,}"))
        basic_layout.addRow("Private:", QLabel("Yes" if self.channel_info.is_private else "No"))
        basic_layout.addRow("Verified:", QLabel("Yes" if self.channel_info.is_verified else "No"))
        basic_layout.addRow("Created:", QLabel(self.channel_info.created_date.strftime("%Y-%m-%d %H:%M") if self.channel_info.created_date else "Unknown"))
        basic_layout.addRow("Last Message:", QLabel(self.channel_info.last_message_date.strftime("%Y-%m-%d %H:%M") if self.channel_info.last_message_date else "Unknown"))
        
        tabs.addTab(basic_tab, "Basic Info")
        
        # Admin rights tab
        rights_tab = QWidget()
        rights_layout = QFormLayout(rights_tab)
        
        for right, has_right in self.channel_info.admin_rights.items():
            checkbox = QCheckBox()
            checkbox.setChecked(has_right)
            checkbox.setEnabled(False)
            rights_layout.addRow(right.replace('_', ' ').title() + ":", checkbox)
        
        tabs.addTab(rights_tab, "Admin Rights")
        
        # Description tab
        if self.channel_info.description:
            desc_tab = QWidget()
            desc_layout = QVBoxLayout(desc_tab)
            desc_text = QTextEdit()
            desc_text.setPlainText(self.channel_info.description)
            desc_text.setReadOnly(True)
            desc_layout.addWidget(desc_text)
            tabs.addTab(desc_tab, "Description")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class AdminChannelsTab(QWidget):
    """Professional tab for managing admin channels and groups"""
    
    def __init__(self, config: Config):

        
        # Apply unified theme
        if TelegramTheme:
            TelegramTheme.apply_widget_theme(self)
        super().__init__()
        self.config = config
        self.channels: List[AdminChannelInfo] = []
        self.filtered_channels: List[AdminChannelInfo] = []
        self.worker = None
        self._init_ui()
        self._setup_styles()
    
    def _init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🤖 Admin Channels & Groups Manager")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Manage all channels and groups where your bot has admin privileges")
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        # Control panel
        control_panel = QGroupBox("Controls")
        control_layout = QHBoxLayout(control_panel)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh Channels")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_channels)
        control_layout.addWidget(self.refresh_btn)
        
        # Filter controls
        control_layout.addWidget(QLabel("Filter:"))
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by name, username, or ID...")
        self.filter_input.textChanged.connect(self.filter_channels)
        control_layout.addWidget(self.filter_input)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Channel", "Group", "Supergroup"])
        self.type_filter.currentTextChanged.connect(self.filter_channels)
        control_layout.addWidget(self.type_filter)
        
        control_layout.addStretch()
        
        # Export button
        self.export_btn = QPushButton("📊 Export Data")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.export_btn.clicked.connect(self.export_data)
        control_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(control_panel)
        
        # Bot Search Panel
        bot_search_panel = QGroupBox("🔍 Search Channels by ID (Using Bot Token)")
        bot_search_layout = QVBoxLayout(bot_search_panel)
        
        # Instructions
        instructions = QLabel("Enter channel/group IDs (one per line) to search using bot token:")
        instructions.setStyleSheet("color: #7f8c8d; font-style: italic;")
        bot_search_layout.addWidget(instructions)
        
        # Input area for IDs
        input_layout = QHBoxLayout()
        
        self.id_input = QPlainTextEdit()
        self.id_input.setPlaceholderText("Examples:\n@channelname\n-1001234567890\n1234567890\n@username")
        self.id_input.setMaximumHeight(100)
        self.id_input.setStyleSheet("""
            QPlainTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
            }
            QPlainTextEdit:focus {
                border-color: #3498db;
            }
        """)
        input_layout.addWidget(self.id_input)
        
        # Search button
        self.search_btn = QPushButton("🔍 Search by ID")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.search_btn.clicked.connect(self.search_channels_by_id)
        input_layout.addWidget(self.search_btn)
        
        bot_search_layout.addLayout(input_layout)
        
        # Bot status
        self.bot_status_label = QLabel("Bot Status: Not tested")
        self.bot_status_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        bot_search_layout.addWidget(self.bot_status_label)
        
        # Test bot button
        self.test_bot_btn = QPushButton("🤖 Test Bot Connection")
        self.test_bot_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.test_bot_btn.clicked.connect(self.test_bot_connection)
        bot_search_layout.addWidget(self.test_bot_btn)
        
        main_layout.addWidget(bot_search_panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(TelegramTheme.get_progress_bar_stylesheet() if TelegramTheme else "QProgressBar { border: 1px solid #2AABEE; border-radius: 6px; text-align: center; }")
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to load channels...")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Channels table
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(8)
        self.channels_table.setHorizontalHeaderLabels([
            "Title", "Type", "Members", "Username", "ID", "Status", "Last Activity", "Actions"
        ])
        
        # Configure table
        header = self.channels_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Members
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Username
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Last Activity
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Actions
        
        self.channels_table.setAlternatingRowColors(True)
        self.channels_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.channels_table.setStyleSheet(TelegramTheme.get_table_stylesheet() if TelegramTheme else "")
        
        content_splitter.addWidget(self.channels_table)
        
        # Details panel
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.StyledPanel)
        details_frame.setMaximumWidth(300)
        details_layout = QVBoxLayout(details_frame)
        
        details_title = QLabel("Channel Statistics")
        details_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        details_layout.addWidget(details_title)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        details_layout.addWidget(self.stats_text)
        
        details_layout.addStretch()
        
        content_splitter.addWidget(details_frame)
        content_splitter.setSizes([800, 300])
        
        main_layout.addWidget(content_splitter)
    
    def _setup_styles(self):
        """Setup additional styles"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    @Slot()
    def refresh_channels(self):
        """Refresh the list of admin channels"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading channels...")
        
        # Clear current data
        self.channels_table.setRowCount(0)
        self.channels.clear()
        
        # Start worker thread
        self.worker = AdminChannelWorker(self.config)
        self.worker.channels_loaded.connect(self.on_channels_loaded)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()
    
    @Slot(list)
    def on_channels_loaded(self, channels: List[AdminChannelInfo]):
        """Handle loaded channels"""
        self.channels = channels
        self.filtered_channels = channels.copy()
        self.populate_table()
        self.update_statistics()
        
        self.refresh_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Loaded {len(channels)} admin channels/groups")
    
    @Slot(int, str)
    def on_progress_updated(self, value: int, message: str):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    @Slot(str)
    def on_error_occurred(self, error_message: str):
        """Handle errors"""
        self.refresh_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error_message}")
        
        QMessageBox.critical(self, "Error", error_message)
    
    def populate_table(self):
        """Populate the channels table"""
        self.channels_table.setRowCount(len(self.filtered_channels))
        
        for row, channel in enumerate(self.filtered_channels):
            # Title
            title_item = QTableWidgetItem(channel.title)
            if channel.is_verified:
                title_item.setText(f"{channel.title} ✓")
            if channel.is_scam:
                title_item.setStyleSheet("color: red;")
            self.channels_table.setItem(row, 0, title_item)
            
            # Type
            type_item = QTableWidgetItem(channel.type.title())
            self.channels_table.setItem(row, 1, type_item)
            
            # Members
            members_item = QTableWidgetItem(f"{channel.members_count:,}")
            self.channels_table.setItem(row, 2, members_item)
            
            # Username
            username_item = QTableWidgetItem(channel.username or "Private")
            self.channels_table.setItem(row, 3, username_item)
            
            # ID
            id_item = QTableWidgetItem(str(channel.id))
            self.channels_table.setItem(row, 4, id_item)
            
            # Status
            status = "🟢 Active"
            if channel.is_scam:
                status = "🔴 Scam"
            elif channel.is_private:
                status = "🟡 Private"
            status_item = QTableWidgetItem(status)
            self.channels_table.setItem(row, 5, status_item)
            
            # Last Activity
            last_activity = "Unknown"
            if channel.last_message_date:
                last_activity = channel.last_message_date.strftime("%Y-%m-%d")
            activity_item = QTableWidgetItem(last_activity)
            self.channels_table.setItem(row, 6, activity_item)
            
            # Actions
            actions_btn = QPushButton("Details")
            TelegramTheme.apply_button_theme(actions_btn, "primary") if TelegramTheme else actions_btn.setStyleSheet("background-color: #2AABEE; color: white; padding: 6px; border-radius: 4px;")
            actions_btn.clicked.connect(lambda checked, ch=channel: self.show_channel_details(ch))
            self.channels_table.setCellWidget(row, 7, actions_btn)
    
    @Slot()
    def filter_channels(self):
        """Filter channels based on search criteria"""
        filter_text = self.filter_input.text().lower()
        type_filter = self.type_filter.currentText()
        
        self.filtered_channels = []
        
        for channel in self.channels:
            # Text filter
            if filter_text:
                search_fields = [
                    channel.title.lower(),
                    channel.username.lower() if channel.username else "",
                    str(channel.id),
                ]
                if not any(filter_text in field for field in search_fields):
                    continue
            
            # Type filter
            if type_filter != "All Types":
                if channel.type.lower() != type_filter.lower():
                    continue
            
            self.filtered_channels.append(channel)
        
        self.populate_table()
        self.update_statistics()
    
    def show_channel_details(self, channel: AdminChannelInfo):
        """Show detailed channel information"""
        dialog = ChannelDetailsDialog(channel, self)
        dialog.exec()
    
    def update_statistics(self):
        """Update statistics panel"""
        if not self.filtered_channels:
            self.stats_text.setPlainText("No channels to display statistics.")
            return
        
        total_channels = len(self.filtered_channels)
        total_members = sum(ch.members_count for ch in self.filtered_channels)
        
        types_count = {}
        for channel in self.filtered_channels:
            types_count[channel.type] = types_count.get(channel.type, 0) + 1
        
        verified_count = sum(1 for ch in self.filtered_channels if ch.is_verified)
        private_count = sum(1 for ch in self.filtered_channels if ch.is_private)
        
        stats_text = f"""
📊 STATISTICS

Total Channels/Groups: {total_channels}
Total Members: {total_members:,}

By Type:
"""
        for channel_type, count in types_count.items():
            stats_text += f"  • {channel_type.title()}: {count}\n"
        
        stats_text += f"""
Verified: {verified_count}
Private: {private_count}
Public: {total_channels - private_count}
        """
        
        self.stats_text.setPlainText(stats_text.strip())
    
    @Slot()
    def export_data(self):
        """Export channel data to file"""
        if not self.channels:
            QMessageBox.information(self, "No Data", "No channels to export. Please refresh first.")
            return
        
        try:
            import csv
            from datetime import datetime
            
            filename = f"admin_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Title', 'Username', 'ID', 'Type', 'Members', 'Private',
                    'Verified', 'Created Date', 'Last Message Date', 'Description'
                ])
                
                for channel in self.channels:
                    writer.writerow([
                        channel.title,
                        channel.username or '',
                        channel.id,
                        channel.type,
                        channel.members_count,
                        'Yes' if channel.is_private else 'No',
                        'Yes' if channel.is_verified else 'No',
                        channel.created_date.strftime('%Y-%m-%d %H:%M') if channel.created_date else '',
                        channel.last_message_date.strftime('%Y-%m-%d %H:%M') if channel.last_message_date else '',
                        (channel.description or '').replace('\n', ' ')
                    ])
            
            QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    @Slot()
    def test_bot_connection(self):
        """Test the bot connection"""
        if not self.config.bot_token:
            QMessageBox.warning(self, "No Bot Token", "Bot token is not configured in config.py")
            self.bot_status_label.setText("Bot Status: ❌ No token configured")
            self.bot_status_label.setStyleSheet(TelegramTheme.get_error_label_style() if TelegramTheme else "color: #F44336; font-weight: bold;")
            return
        
        try:
            bot_client = TelegramBotClient(self.config.bot_token)
            if bot_client.test_connection():
                bot_info = bot_client.get_bot_info()
                bot_name = bot_info.get('first_name', 'Unknown Bot')
                bot_username = bot_info.get('username', 'Unknown')
                
                self.bot_status_label.setText(f"Bot Status: ✅ Connected (@{bot_username} - {bot_name})")
                self.bot_status_label.setStyleSheet(TelegramTheme.get_success_label_style() if TelegramTheme else "color: #4CAF50; font-weight: bold;")
                
                QMessageBox.information(
                    self, 
                    "Bot Connection Success", 
                    f"Successfully connected to bot:\n\nName: {bot_name}\nUsername: @{bot_username}\nID: {bot_info.get('id', 'Unknown')}"
                )
            else:
                self.bot_status_label.setText("Bot Status: ❌ Connection failed")
                self.bot_status_label.setStyleSheet(TelegramTheme.get_error_label_style() if TelegramTheme else "color: #F44336; font-weight: bold;")
                QMessageBox.warning(self, "Connection Failed", "Failed to connect to bot. Check your token.")
                
        except Exception as e:
            self.bot_status_label.setText("Bot Status: ❌ Error")
            self.bot_status_label.setStyleSheet(TelegramTheme.get_error_label_style() if TelegramTheme else "color: #F44336; font-weight: bold;")
            QMessageBox.critical(self, "Bot Error", f"Error testing bot connection: {str(e)}")
    
    @Slot()
    def search_channels_by_id(self):
        """Search channels by ID using bot token"""
        # Get IDs from input
        ids_text = self.id_input.toPlainText().strip()
        if not ids_text:
            QMessageBox.warning(self, "No IDs", "Please enter at least one channel ID to search.")
            return
        
        # Parse IDs (split by lines, remove empty lines)
        channel_ids = [line.strip() for line in ids_text.split('\n') if line.strip()]
        
        if not channel_ids:
            QMessageBox.warning(self, "No Valid IDs", "No valid channel IDs found in input.")
            return
        
        # Check if bot token is configured
        if not self.config.bot_token:
            QMessageBox.warning(self, "No Bot Token", "Bot token is not configured in config.py")
            return
        
        # Stop any running worker
        if hasattr(self, 'search_worker') and self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
        
        # Disable search button and show progress
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Searching channels by ID...")
        
        # Start search worker
        self.search_worker = BotSearchWorker(self.config, channel_ids)
        self.search_worker.channels_found.connect(self.on_channels_found_by_id)
        self.search_worker.progress_updated.connect(self.on_progress_updated)
        self.search_worker.error_occurred.connect(self.on_search_error_occurred)
        self.search_worker.start()
    
    @Slot(list)
    def on_channels_found_by_id(self, found_channels: List[AdminChannelInfo]):
        """Handle channels found by ID search"""
        # Add found channels to existing list (avoid duplicates)
        existing_ids = {channel.id for channel in self.channels}
        new_channels = [ch for ch in found_channels if ch.id not in existing_ids]
        
        # Add new channels
        self.channels.extend(new_channels)
        self.filtered_channels = self.channels.copy()
        
        # Update table
        self.populate_table()
        self.update_statistics()
        
        # Re-enable controls
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Show results
        total_found = len(found_channels)
        new_added = len(new_channels)
        
        if total_found > 0:
            message = f"Found {total_found} channels"
            if new_added < total_found:
                message += f" ({new_added} new, {total_found - new_added} already in list)"
            
            self.status_label.setText(message)
            
            # Show detailed results
            results_text = "Search Results:\n\n"
            for channel in found_channels:
                status = "NEW" if channel.id not in existing_ids else "EXISTING"
                results_text += f"• {channel.title} (@{channel.username or 'private'}) - {channel.type} [{status}]\n"
            
            QMessageBox.information(self, "Search Complete", results_text)
        else:
            self.status_label.setText("No channels found for the provided IDs")
            QMessageBox.information(self, "No Results", "No channels were found for the provided IDs.\n\nPossible reasons:\n• Invalid IDs\n• Bot doesn't have access to these channels\n• Channels don't exist")
    
    @Slot(str) 
    def on_search_error_occurred(self, error_message: str):
        """Handle search errors"""
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Search error: {error_message}")
        
        QMessageBox.critical(self, "Search Error", f"Error searching channels:\n\n{error_message}")
    
    def clear_search_input(self):
        """Clear the ID search input"""
        self.id_input.clear()
