"""
Simple Bot Channel ID Extractor GUI - Modular tool to extract channel IDs
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QTextEdit, QLabel, QGroupBox,
    QProgressBar, QMessageBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor

from utils.bot_channel_extractor import BotChannelIDExtractor, extract_admin_channel_ids


class ChannelExtractionWorker(QThread):
    """Worker thread for channel extraction"""
    
    extraction_complete = Signal(bool, list, str)
    progress_update = Signal(str)
    
    def __init__(self, bot_token: str):
        super().__init__()
        self.bot_token = bot_token
    
    def run(self):
        """Extract channels in background thread"""
        try:
            success, channels, message = extract_admin_channel_ids(
                self.bot_token, verbose=False
            )
            self.extraction_complete.emit(success, channels, message)
        except Exception as e:
            self.extraction_complete.emit(False, [], f"Extraction error: {str(e)}")


class BotChannelExtractorGUI(QWidget):
    """Simple GUI for extracting channel IDs using bot token"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.setup_styles()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("🤖 Bot Channel ID Extractor")
        self.setFixedSize(800, 600)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header_label = QLabel("🔍 Telegram Bot Channel ID Extractor")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel("Extract IDs of all channels and groups where your bot is administrator")
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        main_layout.addWidget(desc_label)
        
        # Token input section
        token_group = QGroupBox("🔑 Bot Token Configuration")
        token_layout = QVBoxLayout(token_group)
        
        token_label = QLabel("Enter your Telegram Bot Token:")
        token_label.setStyleSheet("color: #34495e; font-weight: bold;")
        token_layout.addWidget(token_label)
        
        # Token input
        token_input_layout = QHBoxLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        token_input_layout.addWidget(self.token_input)
        
        # Toggle visibility button
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setToolTip("Toggle token visibility")
        self.toggle_btn.clicked.connect(self.toggle_token_visibility)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        token_input_layout.addWidget(self.toggle_btn)
        
        token_layout.addLayout(token_input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 Test Token")
        self.test_btn.clicked.connect(self.test_token)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        button_layout.addWidget(self.test_btn)
        
        self.extract_btn = QPushButton("🚀 Extract Channel IDs")
        self.extract_btn.clicked.connect(self.extract_channels)
        self.extract_btn.setStyleSheet("""
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
        button_layout.addWidget(self.extract_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_layout.addWidget(self.clear_btn)
        
        token_layout.addLayout(button_layout)
        main_layout.addWidget(token_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Results section
        results_group = QGroupBox("📊 Extraction Results")
        results_layout = QVBoxLayout(results_group)
        
        # Status label
        self.status_label = QLabel("Ready to extract channel IDs")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        results_layout.addWidget(self.status_label)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-family: monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.results_text.setPlaceholderText("Channel extraction results will appear here...")
        results_layout.addWidget(self.results_text)
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy IDs to Clipboard")
        self.copy_btn.clicked.connect(self.copy_ids_to_clipboard)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        results_layout.addWidget(self.copy_btn)
        
        main_layout.addWidget(results_group)
        
        # Footer
        footer_label = QLabel("💡 Tip: Bot must be admin in channels to be detected")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #95a5a6; font-size: 10px; font-style: italic;")
        main_layout.addWidget(footer_label)
    
    def setup_styles(self):
        """Setup widget styles"""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin: 10px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }
        """)
    
    @Slot()
    def toggle_token_visibility(self):
        """Toggle token input visibility"""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.toggle_btn.setText("👁️")
    
    @Slot()
    def test_token(self):
        """Test the bot token"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "No Token", "Please enter a bot token first.")
            return
        
        try:
            self.status_label.setText("Testing token...")
            self.test_btn.setEnabled(False)
            
            extractor = BotChannelIDExtractor(token)
            result = extractor.test_bot_token()
            
            if result['success']:
                self.status_label.setText(f"✅ Token valid: {result['message']}")
                self.status_label.setStyleSheet("color: #27ae60;")
                QMessageBox.information(
                    self, 
                    "Token Valid", 
                    f"Bot token is valid!\n\n{result['message']}\nBot ID: {result['bot_id']}"
                )
            else:
                self.status_label.setText(f"❌ Token invalid: {result['error']}")
                self.status_label.setStyleSheet("color: #e74c3c;")
                QMessageBox.warning(self, "Token Invalid", result['error'])
        
        except Exception as e:
            self.status_label.setText(f"❌ Error testing token: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            QMessageBox.critical(self, "Test Error", f"Error testing token: {str(e)}")
        
        finally:
            self.test_btn.setEnabled(True)
    
    @Slot()
    def extract_channels(self):
        """Extract admin channels"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "No Token", "Please enter a bot token first.")
            return
        
        # Disable controls
        self.extract_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Extracting channels...")
        self.status_label.setStyleSheet("color: #3498db;")
        
        # Start extraction
        self.worker = ChannelExtractionWorker(token)
        self.worker.extraction_complete.connect(self.on_extraction_complete)
        self.worker.start()
    
    @Slot(bool, list, str)
    def on_extraction_complete(self, success: bool, channels: list, message: str):
        """Handle extraction completion"""
        # Re-enable controls
        self.extract_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #27ae60;")
            
            if channels:
                # Display results
                results_text = f"🎯 Found {len(channels)} admin channels/groups:\n"
                results_text += "=" * 60 + "\n\n"
                
                for i, channel in enumerate(channels, 1):
                    username_str = f"@{channel['username']}" if channel['username'] else "Private"
                    results_text += f"{i:2d}. {channel['title']}\n"
                    results_text += f"    ID: {channel['id']}\n"
                    results_text += f"    Username: {username_str}\n"
                    results_text += f"    Type: {channel['type'].title()}\n"
                    results_text += f"    Status: {channel['admin_status'].title()}\n\n"
                
                results_text += "\n" + "=" * 60 + "\n"
                results_text += "📋 Channel IDs (for copying):\n"
                results_text += "-" * 30 + "\n"
                
                self.channel_ids = []  # Store for copying
                for channel in channels:
                    self.channel_ids.append(str(channel['id']))
                    results_text += f"{channel['id']}\n"
                
                self.results_text.setText(results_text)
                self.copy_btn.setEnabled(True)
                
            else:
                self.results_text.setText("No admin channels found.\n\nPossible reasons:\n• Bot is not admin in any channels\n• No recent activity in admin channels\n• Bot needs to receive messages first")
                self.copy_btn.setEnabled(False)
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            self.results_text.setText(f"Extraction failed:\n{message}")
            self.copy_btn.setEnabled(False)
            
            QMessageBox.critical(self, "Extraction Failed", message)
    
    @Slot()
    def copy_ids_to_clipboard(self):
        """Copy channel IDs to clipboard"""
        if hasattr(self, 'channel_ids') and self.channel_ids:
            clipboard = QApplication.clipboard()
            ids_text = '\n'.join(self.channel_ids)
            clipboard.setText(ids_text)
            
            QMessageBox.information(
                self, 
                "Copied to Clipboard", 
                f"Copied {len(self.channel_ids)} channel IDs to clipboard!\n\nYou can now paste them into the main application."
            )
        else:
            QMessageBox.warning(self, "No IDs", "No channel IDs to copy.")
    
    @Slot()
    def clear_results(self):
        """Clear all results"""
        self.results_text.clear()
        self.status_label.setText("Ready to extract channel IDs")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.copy_btn.setEnabled(False)
        if hasattr(self, 'channel_ids'):
            delattr(self, 'channel_ids')


def run_channel_extractor():
    """Run the channel extractor GUI"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Bot Channel ID Extractor")
    app.setApplicationVersion("1.0")
    
    # Create and show window
    window = BotChannelExtractorGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_channel_extractor())
