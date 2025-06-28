"""
Simple Admin Channels Tab - Uses default program theme
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QGroupBox, QHeaderView,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtGui import QFont

from services.telegram_bot_client import TelegramBotClient, BotChannelInfo
from core.config import Config
import logging

logger = logging.getLogger(__name__)


class BotSearchWorker(QThread):
    """Worker thread for searching channels by ID using bot token"""
    
    channels_found = Signal(list)
    progress_updated = Signal(int, str)
    error_occurred = Signal(str)
    
    def __init__(self, config: Config, channel_ids: list):
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
                    channel_info = self.bot_client.get_channel_info_by_id(channel_id.strip())
                    if channel_info:
                        # Check bot permissions
                        permissions = self.bot_client.validate_bot_permissions(str(channel_info['id']))
                        
                        # Create simplified channel data
                        simple_channel = {
                            'id': channel_info['id'],
                            'title': channel_info['title'],
                            'username': channel_info['username'],
                            'type': channel_info['type'],
                            'member_count': channel_info.get('member_count', 0),
                            'is_private': channel_info['is_private'],
                            'permissions': permissions,
                            'description': channel_info.get('description', '')
                        }
                        found_channels.append(simple_channel)
                        
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


class SimpleAdminChannelsTab(QWidget):
    """Simple Admin Channels Tab with default theme"""
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.channels = []
        self.search_worker = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QLabel("🤖 Admin Channels Manager")
        header_label.setFont(QFont("", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel("Search and manage channels where your bot is administrator")
        desc_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc_label)
        
        # Search section
        search_group = QGroupBox("Search Channels by ID")
        search_layout = QVBoxLayout(search_group)
        
        # Instructions
        instructions = QLabel("Enter channel/group IDs (one per line):")
        search_layout.addWidget(instructions)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.id_input = QPlainTextEdit()
        self.id_input.setPlaceholderText("Examples:\n@channelname\n-1001234567890\n1234567890")
        self.id_input.setMaximumHeight(100)
        input_layout.addWidget(self.id_input)
        
        # Search button
        self.search_btn = QPushButton("🔍 Search by ID")
        self.search_btn.clicked.connect(self.search_channels_by_id)
        input_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(input_layout)
        
        # Bot test button
        self.test_bot_btn = QPushButton("🤖 Test Bot Connection")
        self.test_bot_btn.clicked.connect(self.test_bot_connection)
        search_layout.addWidget(self.test_bot_btn)
        
        main_layout.addWidget(search_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to search channels")
        main_layout.addWidget(self.status_label)
        
        # Results table
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)
        
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(6)
        self.channels_table.setHorizontalHeaderLabels([
            "Title", "Username", "ID", "Type", "Members", "Status"
        ])
        
        # Configure table
        header = self.channels_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        results_layout.addWidget(self.channels_table)
        
        # Export button
        self.export_btn = QPushButton("📊 Export Results")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        results_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(results_group)
    
    @Slot()
    def test_bot_connection(self):
        """Test the bot connection"""
        if not self.config.bot_token:
            QMessageBox.warning(self, "No Bot Token", "Bot token is not configured in config.py")
            return
        
        try:
            bot_client = TelegramBotClient(self.config.bot_token)
            if bot_client.test_connection():
                bot_info = bot_client.get_bot_info()
                bot_name = bot_info.get('first_name', 'Unknown Bot')
                bot_username = bot_info.get('username', 'unknown')
                
                QMessageBox.information(
                    self, 
                    "Bot Connection Success", 
                    f"Successfully connected to bot:\n\nName: {bot_name}\nUsername: @{bot_username}\nID: {bot_info.get('id', 'Unknown')}"
                )
                self.status_label.setText(f"✅ Bot connected: @{bot_username}")
            else:
                QMessageBox.warning(self, "Connection Failed", "Failed to connect to bot. Check your token.")
                self.status_label.setText("❌ Bot connection failed")
                
        except Exception as e:
            QMessageBox.critical(self, "Bot Error", f"Error testing bot connection: {str(e)}")
            self.status_label.setText("❌ Bot connection error")
    
    @Slot()
    def search_channels_by_id(self):
        """Search channels by ID using bot token"""
        # Get IDs from input
        ids_text = self.id_input.toPlainText().strip()
        if not ids_text:
            QMessageBox.warning(self, "No IDs", "Please enter at least one channel ID to search.")
            return
        
        # Parse IDs
        channel_ids = [line.strip() for line in ids_text.split('\n') if line.strip()]
        
        if not channel_ids:
            QMessageBox.warning(self, "No Valid IDs", "No valid channel IDs found in input.")
            return
        
        # Check bot token
        if not self.config.bot_token:
            QMessageBox.warning(self, "No Bot Token", "Bot token is not configured in config.py")
            return
        
        # Stop any running worker
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
        
        # Start search
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Searching channels...")
        
        # Create and start worker
        self.search_worker = BotSearchWorker(self.config, channel_ids)
        self.search_worker.channels_found.connect(self.on_channels_found)
        self.search_worker.progress_updated.connect(self.on_progress_updated)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()
    
    @Slot(list)
    def on_channels_found(self, found_channels):
        """Handle search results"""
        self.channels = found_channels
        self.populate_table()
        
        # Re-enable controls
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(len(found_channels) > 0)
        
        # Update status
        if found_channels:
            self.status_label.setText(f"✅ Found {len(found_channels)} channels")
        else:
            self.status_label.setText("❌ No channels found")
    
    @Slot(int, str)
    def on_progress_updated(self, value, message):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    @Slot(str)
    def on_search_error(self, error_message):
        """Handle search errors"""
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ Error: {error_message}")
        
        QMessageBox.critical(self, "Search Error", f"Error searching channels:\n\n{error_message}")
    
    def populate_table(self):
        """Populate the results table"""
        self.channels_table.setRowCount(len(self.channels))
        
        for row, channel in enumerate(self.channels):
            # Title
            self.channels_table.setItem(row, 0, QTableWidgetItem(channel['title']))
            
            # Username
            username = f"@{channel['username']}" if channel['username'] else "Private"
            self.channels_table.setItem(row, 1, QTableWidgetItem(username))
            
            # ID
            self.channels_table.setItem(row, 2, QTableWidgetItem(str(channel['id'])))
            
            # Type
            self.channels_table.setItem(row, 3, QTableWidgetItem(channel['type'].title()))
            
            # Members
            members = f"{channel['member_count']:,}" if channel['member_count'] else "Unknown"
            self.channels_table.setItem(row, 4, QTableWidgetItem(members))
            
            # Status
            permissions = channel.get('permissions', {})
            status = permissions.get('status', 'Unknown')
            self.channels_table.setItem(row, 5, QTableWidgetItem(status.title()))
    
    @Slot()
    def export_data(self):
        """Export channel data to file"""
        if not self.channels:
            QMessageBox.information(self, "No Data", "No channels to export.")
            return
        
        try:
            import csv
            from datetime import datetime
            
            filename = f"admin_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Title', 'Username', 'ID', 'Type', 'Members', 'Status', 'Description'])
                
                for channel in self.channels:
                    writer.writerow([
                        channel['title'],
                        channel['username'] or '',
                        channel['id'],
                        channel['type'],
                        channel.get('member_count', 0),
                        channel.get('permissions', {}).get('status', 'Unknown'),
                        (channel.get('description', '') or '').replace('\n', ' ')
                    ])
            
            QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")


# Alias for compatibility
AdminChannelsTab = SimpleAdminChannelsTab
