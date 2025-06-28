"""
Unified Admin Channels Tab - Extract and manage channel IDs where bot is admin
Combines functionality for extracting IDs from both public and private channels/groups
"""
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QComboBox, QGroupBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox,
                             QSplitter, QFrame, QScrollArea, QCheckBox, QSpinBox, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCursor
import logging
from typing import List, Dict, Optional

# Import our modular extractor
try:
    from utils.bot_channel_extractor import BotChannelIDExtractor, extract_admin_channel_ids_only
except ImportError:
    from telegram_ai_publisher.utils.bot_channel_extractor import BotChannelIDExtractor, extract_admin_channel_ids_only

logger = logging.getLogger(__name__)


class ChannelExtractionWorker(QThread):
    """Worker thread for extracting channel IDs"""
    progress = Signal(str)  # Progress messages
    finished = Signal(bool, list, str)  # success, channels, message
    channel_found = Signal(dict)  # Individual channel found
    
    def __init__(self, bot_token: str, extraction_type: str = "detailed", comprehensive: bool = False, include_members: bool = False):
        super().__init__()
        self.bot_token = bot_token
        self.extraction_type = extraction_type
        self.comprehensive = comprehensive
        self.include_members = include_members
        self.extractor = None
        
    def run(self):
        """Run the extraction process"""
        try:
            self.progress.emit("🤖 Initializing Bot Channel Extractor...")
            self.extractor = BotChannelIDExtractor(bot_token=self.bot_token)
            
            # Override log_progress to emit signals
            self.extractor.log_progress = self.progress.emit
            
            # Test bot token
            self.progress.emit("🔍 Testing bot token...")
            bot_test = self.extractor.test_bot_token()
            
            if not bot_test['success']:
                self.finished.emit(False, [], f"Bot token test failed: {bot_test['error']}")
                return
            
            self.progress.emit(f"✅ {bot_test['message']}")
            
            # Choose extraction method
            if self.comprehensive:
                self.progress.emit("� Starting comprehensive channel scan...")
                admin_channels = self.extractor.get_comprehensive_admin_channels(
                    include_member_channels=self.include_members
                )
            else:
                self.progress.emit("📡 Searching for channels from updates...")
                # Get channels from updates
                channels = self.extractor.get_channel_ids_from_updates()
                self.progress.emit(f"🔍 Found {len(channels)} channels from updates")
                
                admin_channels = []
                
                for i, channel in enumerate(channels):
                    self.progress.emit(f"Checking {i+1}/{len(channels)}: {channel['title']}")
                    
                    # Check admin permissions
                    admin_info = self.extractor.check_admin_permissions(channel['id'])
                    
                    is_admin = admin_info.get('is_admin', False)
                    
                    if is_admin or (self.include_members and not is_admin):
                        # Create detailed channel info
                        channel_info = {
                            'id': channel['id'],
                            'title': channel['title'],
                            'username': channel.get('username'),
                            'type': channel['type'],
                            'is_private': channel['is_private'],
                            'admin_status': admin_info.get('status'),
                            'permissions': admin_info.get('permissions', {}),
                            'is_admin': is_admin
                        }
                        admin_channels.append(channel_info)
                        self.channel_found.emit(channel_info)
                        
                        status_emoji = "✅" if is_admin else "👥"
                        status_text = "Admin" if is_admin else "Member"
                        self.progress.emit(f"  {status_emoji} {status_text} in: {channel['title']}")
                    else:
                        self.progress.emit(f"  ❌ No access to: {channel['title']}")
            
            # Emit channels found during comprehensive scan
            if self.comprehensive:
                for channel in admin_channels:
                    self.channel_found.emit(channel)
            
            self.finished.emit(True, admin_channels, f"Found {len(admin_channels)} channels")
            
        except Exception as e:
            self.finished.emit(False, [], f"Error during extraction: {str(e)}")


class ChannelSearchWorker(QThread):
    """Worker thread for searching specific channel by ID"""
    finished = Signal(bool, dict, str)  # success, channel_info, message
    
    def __init__(self, bot_token: str, channel_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.channel_id = channel_id
        
    def run(self):
        """Search for specific channel"""
        try:
            extractor = BotChannelIDExtractor(self.bot_token)
            
            # Get channel info
            channel_info = extractor.get_channel_info_by_id(self.channel_id)
            
            if channel_info:
                # Check if bot is admin
                admin_info = extractor.check_admin_permissions(channel_info['id'])
                channel_info['admin_status'] = admin_info.get('status', 'unknown')
                channel_info['is_admin'] = admin_info.get('is_admin', False)
                channel_info['permissions'] = admin_info.get('permissions', {})
                
                self.finished.emit(True, channel_info, "Channel found successfully")
            else:
                self.finished.emit(False, {}, "Channel not found or bot has no access")
                
        except Exception as e:
            self.finished.emit(False, {}, f"Error searching channel: {str(e)}")


class UnifiedAdminChannelsTab(QWidget):
    """Unified tab for extracting and managing admin channel IDs"""
    
    def __init__(self):
        super().__init__()
        self.extracted_channels = []
        self.extractor_worker = None
        self.search_worker = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🔧 Admin Channels Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Extract and manage channel IDs where your bot is administrator (public and private channels/groups)")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Left panel
        splitter.setStretchFactor(1, 2)  # Right panel takes more space
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
    def create_control_panel(self) -> QWidget:
        """Create the control panel with settings and actions"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Bot Token Section
        token_group = QGroupBox("🤖 Bot Configuration")
        token_layout = QVBoxLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter your Telegram Bot Token here...")
        self.token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(QLabel("Bot Token:"))
        token_layout.addWidget(self.token_input)
        
        # Show/Hide token button
        self.toggle_token_btn = QPushButton("👁 Show Token")
        self.toggle_token_btn.clicked.connect(self.toggle_token_visibility)
        token_layout.addWidget(self.toggle_token_btn)
        
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)
        
        # Extraction Section
        extraction_group = QGroupBox("📡 Channel Extraction")
        extraction_layout = QVBoxLayout()
        
                # Extraction options
        options_layout = QHBoxLayout()
        
        self.comprehensive_scan = QCheckBox("Comprehensive Scan")
        self.comprehensive_scan.setToolTip("More thorough scan (slower but finds more channels)")
        options_layout.addWidget(self.comprehensive_scan)
        
        self.include_member_channels = QCheckBox("Include Member Channels")
        self.include_member_channels.setToolTip("Include channels where bot is member (not admin)")
        options_layout.addWidget(self.include_member_channels)
        
        extraction_layout.addLayout(options_layout)
        
        # Extract button
        self.extract_btn = QPushButton("🔍 Extract Admin Channels")
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.extract_btn.clicked.connect(self.extract_channels)
        extraction_layout.addWidget(self.extract_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        extraction_layout.addWidget(self.progress_bar)
        
        extraction_group.setLayout(extraction_layout)
        layout.addWidget(extraction_group)
        
        # Search Section
        search_group = QGroupBox("🔎 Search Specific Channel")
        search_layout = QVBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Channel ID or @username...")
        search_layout.addWidget(QLabel("Channel ID/Username:"))
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 Search Channel")
        self.search_btn.clicked.connect(self.search_channel)
        search_layout.addWidget(self.search_btn)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Export Section
        export_group = QGroupBox("💾 Export Options")
        export_layout = QVBoxLayout()
        
        self.export_ids_btn = QPushButton("📋 Copy IDs to Clipboard")
        self.export_ids_btn.clicked.connect(self.copy_ids_to_clipboard)
        self.export_ids_btn.setEnabled(False)
        export_layout.addWidget(self.export_ids_btn)
        
        self.save_ids_btn = QPushButton("💾 Save IDs to File")
        self.save_ids_btn.clicked.connect(self.save_ids_to_file)
        self.save_ids_btn.setEnabled(False)
        export_layout.addWidget(self.save_ids_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
        
    def create_results_panel(self) -> QWidget:
        """Create the results panel with channels table and logs"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Results splitter (vertical)
        results_splitter = QSplitter(Qt.Vertical)
        
        # Channels table
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        
        # Table header
        table_header = QLabel("📊 Discovered Admin Channels")
        table_header.setFont(QFont("", 12, QFont.Bold))
        table_layout.addWidget(table_header)
        
        # Channels table
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(7)
        self.channels_table.setHorizontalHeaderLabels([
            "ID", "Title", "Username", "Type", "Status", "Members", "Private"
        ])
        
        # Set column widths
        header = self.channels_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Username
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Members
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Private
        
        self.channels_table.setAlternatingRowColors(True)
        self.channels_table.setSelectionBehavior(QTableWidget.SelectRows)
        table_layout.addWidget(self.channels_table)
        
        table_widget.setLayout(table_layout)
        results_splitter.addWidget(table_widget)
        
        # Progress/Log area
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        
        log_header = QLabel("📝 Extraction Progress & Logs")
        log_header.setFont(QFont("", 12, QFont.Bold))
        log_layout.addWidget(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_widget.setLayout(log_layout)
        results_splitter.addWidget(log_widget)
        
        # Set splitter proportions
        results_splitter.setStretchFactor(0, 3)  # Table takes more space
        results_splitter.setStretchFactor(1, 1)  # Log area smaller
        
        layout.addWidget(results_splitter)
        widget.setLayout(layout)
        return widget
    
    def toggle_token_visibility(self):
        """Toggle bot token visibility"""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.toggle_token_btn.setText("🙈 Hide Token")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.toggle_token_btn.setText("👁 Show Token")
    
    def extract_channels(self):
        """Start channel extraction process"""
        bot_token = self.token_input.text().strip()
        
        if not bot_token:
            QMessageBox.warning(self, "Warning", "Please enter a bot token first!")
            return
        
        # Clear previous results
        self.extracted_channels = []
        self.channels_table.setRowCount(0)
        self.log_text.clear()
        
        # Disable UI
        self.extract_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start worker thread
        comprehensive = self.comprehensive_scan.isChecked()
        include_members = self.include_member_channels.isChecked()
        
        self.extractor_worker = ChannelExtractionWorker(
            bot_token, "detailed", comprehensive, include_members
        )
        self.extractor_worker.progress.connect(self.update_progress)
        self.extractor_worker.channel_found.connect(self.add_channel_to_table)
        self.extractor_worker.finished.connect(self.extraction_finished)
        self.extractor_worker.start()
    
    def search_channel(self):
        """Search for a specific channel"""
        bot_token = self.token_input.text().strip()
        channel_id = self.search_input.text().strip()
        
        if not bot_token:
            QMessageBox.warning(self, "Warning", "Please enter a bot token first!")
            return
            
        if not channel_id:
            QMessageBox.warning(self, "Warning", "Please enter a channel ID or username!")
            return
        
        # Disable search button
        self.search_btn.setEnabled(False)
        self.update_progress(f"🔍 Searching for channel: {channel_id}")
        
        # Start search worker
        self.search_worker = ChannelSearchWorker(bot_token, channel_id)
        self.search_worker.finished.connect(self.search_finished)
        self.search_worker.start()
    
    def update_progress(self, message: str):
        """Update progress log"""
        self.log_text.append(message)
        # Auto-scroll to bottom using a simpler method
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_channel_to_table(self, channel_info: Dict):
        """Add a channel to the results table"""
        row = self.channels_table.rowCount()
        self.channels_table.insertRow(row)
        
        # Add data to columns
        self.channels_table.setItem(row, 0, QTableWidgetItem(str(channel_info['id'])))
        self.channels_table.setItem(row, 1, QTableWidgetItem(channel_info['title']))
        
        username = channel_info.get('username', '')
        username_text = f"@{username}" if username else "N/A"
        self.channels_table.setItem(row, 2, QTableWidgetItem(username_text))
        
        self.channels_table.setItem(row, 3, QTableWidgetItem(channel_info['type'].title()))
        # Admin status with emoji
        is_admin = channel_info.get('is_admin', False)
        admin_status = channel_info.get('admin_status', 'Unknown').title()
        status_with_emoji = f"{'🔧' if is_admin else '👥'} {admin_status}"
        self.channels_table.setItem(row, 4, QTableWidgetItem(status_with_emoji))
        
        # Member count (if available)
        member_count = channel_info.get('member_count', 'N/A')
        self.channels_table.setItem(row, 5, QTableWidgetItem(str(member_count)))
        
        # Private status
        is_private = "Yes" if channel_info.get('is_private', False) else "No"
        self.channels_table.setItem(row, 6, QTableWidgetItem(is_private))
        
        # Store full channel info
        self.extracted_channels.append(channel_info)
    
    def extraction_finished(self, success: bool, channels: List[Dict], message: str):
        """Handle extraction completion"""
        # Re-enable UI
        self.extract_btn.setEnabled(True)
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.update_progress(f"✅ {message}")
            if channels:
                self.export_ids_btn.setEnabled(True)
                self.save_ids_btn.setEnabled(True)
                QMessageBox.information(self, "Success", f"Found {len(channels)} admin channels!")
            else:
                QMessageBox.information(self, "No Results", "No admin channels found.")
        else:
            self.update_progress(f"❌ {message}")
            QMessageBox.critical(self, "Error", message)
    
    def search_finished(self, success: bool, channel_info: Dict, message: str):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        
        if success:
            self.update_progress(f"✅ {message}")
            # Add to table if not already present
            channel_id = channel_info['id']
            
            # Check if already in table
            already_exists = False
            for i in range(self.channels_table.rowCount()):
                if self.channels_table.item(i, 0).text() == str(channel_id):
                    already_exists = True
                    break
            
            if not already_exists:
                self.add_channel_to_table(channel_info)
                self.export_ids_btn.setEnabled(True)
                self.save_ids_btn.setEnabled(True)
            
            # Show detailed info
            admin_status = "✅ Admin" if channel_info.get('is_admin', False) else "❌ Not Admin"
            QMessageBox.information(self, "Channel Found", 
                f"Channel: {channel_info['title']}\n"
                f"ID: {channel_info['id']}\n"
                f"Type: {channel_info['type'].title()}\n"
                f"Admin Status: {admin_status}")
        else:
            self.update_progress(f"❌ {message}")
            QMessageBox.warning(self, "Search Failed", message)
    
    def copy_ids_to_clipboard(self):
        """Copy channel IDs to clipboard"""
        if not self.extracted_channels:
            QMessageBox.warning(self, "No Data", "No channels to copy!")
            return
        
        ids = [str(channel['id']) for channel in self.extracted_channels]
        ids_text = '\n'.join(ids)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(ids_text)
        
        QMessageBox.information(self, "Copied", f"Copied {len(ids)} channel IDs to clipboard!")
    
    def save_ids_to_file(self):
        """Save channel IDs to file"""
        if not self.extracted_channels:
            QMessageBox.warning(self, "No Data", "No channels to save!")
            return
        
        try:
            filename = "admin_channel_ids.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Admin Channel IDs extracted by Telegram AI Publisher\n")
                f.write(f"# Total channels: {len(self.extracted_channels)}\n\n")
                
                for channel in self.extracted_channels:
                    f.write(f"# {channel['title']} ({channel['type']})\n")
                    f.write(f"{channel['id']}\n\n")
            
            QMessageBox.information(self, "Saved", f"Saved {len(self.extracted_channels)} channel IDs to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")


# Import QApplication for clipboard functionality (already imported above)


if __name__ == "__main__":
    """Test the unified admin channels tab"""
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    window = UnifiedAdminChannelsTab()
    window.show()
    
    sys.exit(app.exec_())
