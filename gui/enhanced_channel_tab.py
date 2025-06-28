"""
Enhanced Channel Manager Tab with real-time monitoring and batch operations
"""
import asyncio
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QProgressBar, QTabWidget,
    QTextEdit, QComboBox, QSpinBox, QCheckBox, QSplitter, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtGui import QFont, QColor, QIcon
import json
from datetime import datetime, timedelta

from services.telegram_metrics import (
    get_enhanced_client, get_monitor_service, search_channels,
    batch_get_channels_info, start_monitoring, stop_monitoring,
    get_monitoring_stats, clear_cache, get_search_history
)


class ChannelSearchWorker(QThread):
    """Worker thread for channel search operations"""
    
    results_ready = Signal(list)
    error_occurred = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self, query: str, limit: int = 50):
        super().__init__()
        self.query = query
        self.limit = limit
    
    def run(self):
        try:
            self.progress_updated.emit(25)
            
            # Run async search
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.progress_updated.emit(50)
            results = loop.run_until_complete(search_channels(self.query, self.limit))
            
            self.progress_updated.emit(100)
            self.results_ready.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


class BatchInfoWorker(QThread):
    """Worker thread for batch channel info retrieval"""
    
    results_ready = Signal(dict)
    error_occurred = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self, channels: List[str]):
        super().__init__()
        self.channels = channels
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            total = len(self.channels)
            results = {}
            
            # Process in smaller batches to show progress
            batch_size = 5
            for i in range(0, total, batch_size):
                batch = self.channels[i:i + batch_size]
                batch_results = loop.run_until_complete(batch_get_channels_info(batch))
                results.update(batch_results)
                
                progress = int((i + len(batch)) / total * 100)
                self.progress_updated.emit(progress)
            
            self.results_ready.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


class ChannelMonitoringDialog(QDialog):
    """Dialog for configuring channel monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Channel Monitoring Settings")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QFormLayout(self)
        
        # Update interval
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)  # 10 seconds to 1 hour
        self.interval_spin.setValue(30)
        self.interval_spin.setSuffix(" seconds")
        layout.addRow("Update Interval:", self.interval_spin)
        
        # Enable notifications
        self.notifications_check = QCheckBox("Enable notifications for new messages")
        self.notifications_check.setChecked(True)
        layout.addRow(self.notifications_check)
        
        # Monitor subscriber changes
        self.subscriber_check = QCheckBox("Monitor subscriber count changes")
        self.subscriber_check.setChecked(True)
        layout.addRow(self.subscriber_check)
        
        # Monitor message activity
        self.activity_check = QCheckBox("Monitor message activity")
        self.activity_check.setChecked(True)
        layout.addRow(self.activity_check)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_settings(self) -> Dict:
        """Get monitoring settings"""
        return {
            "interval": self.interval_spin.value(),
            "notifications": self.notifications_check.isChecked(),
            "monitor_subscribers": self.subscriber_check.isChecked(),
            "monitor_activity": self.activity_check.isChecked()
        }


class EnhancedChannelManagerTab(QWidget):
    """Enhanced tab for managing multiple Telegram channels with real-time monitoring"""
    
    def __init__(self):
        super().__init__()
        self.monitored_channels = set()
        self.monitoring_active = False
        self.search_worker = None
        self.batch_worker = None
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Search and management
        left_widget = self.create_left_panel()
        splitter.addWidget(left_widget)
        
        # Right side - Monitoring and stats
        right_widget = self.create_right_panel()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with search and channel management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search section
        search_group = QGroupBox("Channel Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search input
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search channels by name or username...")
        self.search_input.returnPressed.connect(self.search_channels)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_channels)
        
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_input_layout)
        
        # Search progress
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        search_layout.addWidget(self.search_progress)
        
        # Search results
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(4)
        self.search_results.setHorizontalHeaderLabels(["Title", "Username", "Subscribers", "Type"])
        self.search_results.setSelectionBehavior(QTableWidget.SelectRows)
        self.search_results.horizontalHeader().setStretchLastSection(True)
        search_layout.addWidget(self.search_results)
        
        # Search buttons
        search_btn_layout = QHBoxLayout()
        self.add_selected_btn = QPushButton("Add Selected to Monitoring")
        self.add_selected_btn.clicked.connect(self.add_selected_channels)
        self.add_selected_btn.setEnabled(False)
        
        self.clear_search_btn = QPushButton("Clear Results")
        self.clear_search_btn.clicked.connect(self.clear_search_results)
        
        search_btn_layout.addWidget(self.add_selected_btn)
        search_btn_layout.addWidget(self.clear_search_btn)
        search_layout.addLayout(search_btn_layout)
        
        layout.addWidget(search_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Manual add
        manual_layout = QHBoxLayout()
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Enter channel username or ID...")
        
        self.add_manual_btn = QPushButton("Add Channel")
        self.add_manual_btn.clicked.connect(self.add_manual_channel)
        
        manual_layout.addWidget(QLabel("Manual Add:"))
        manual_layout.addWidget(self.manual_input)
        manual_layout.addWidget(self.add_manual_btn)
        actions_layout.addLayout(manual_layout)
        
        # Bulk operations
        bulk_layout = QHBoxLayout()
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        
        bulk_layout.addWidget(self.clear_cache_btn)
        bulk_layout.addWidget(self.export_btn)
        actions_layout.addLayout(bulk_layout)
        
        layout.addWidget(actions_group)
        
        # Search history
        history_group = QGroupBox("Search History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QTreeWidget()
        self.history_list.setHeaderLabels(["Query", "Date", "Results"])
        self.history_list.itemDoubleClicked.connect(self.repeat_search)
        history_layout.addWidget(self.history_list)
        
        self.load_history_btn = QPushButton("Load History")
        self.load_history_btn.clicked.connect(self.load_search_history)
        history_layout.addWidget(self.load_history_btn)
        
        layout.addWidget(history_group)
        
        return widget
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with monitoring and statistics"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Monitoring controls
        monitor_group = QGroupBox("Channel Monitoring")
        monitor_layout = QVBoxLayout(monitor_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("Start Monitoring")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        
        self.stop_monitor_btn = QPushButton("Stop Monitoring")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        
        self.config_monitor_btn = QPushButton("Configure")
        self.config_monitor_btn.clicked.connect(self.configure_monitoring)
        
        control_layout.addWidget(self.start_monitor_btn)
        control_layout.addWidget(self.stop_monitor_btn)
        control_layout.addWidget(self.config_monitor_btn)
        monitor_layout.addLayout(control_layout)
        
        # Status
        self.monitor_status = QLabel("Monitoring: Inactive")
        self.monitor_status.setFont(QFont("Arial", 10, QFont.Bold))
        monitor_layout.addWidget(self.monitor_status)
        
        layout.addWidget(monitor_group)
        
        # Monitored channels table
        channels_group = QGroupBox("Monitored Channels")
        channels_layout = QVBoxLayout(channels_group)
        
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(7)
        self.channels_table.setHorizontalHeaderLabels([
            "Title", "Username", "Subscribers", "Growth", "Activity", "Last Update", "Actions"
        ])
        self.channels_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.channels_table.horizontalHeader().setStretchLastSection(True)
        channels_layout.addWidget(self.channels_table)
        
        # Channel table buttons
        channel_btn_layout = QHBoxLayout()
        self.refresh_channels_btn = QPushButton("Refresh All")
        self.refresh_channels_btn.clicked.connect(self.refresh_all_channels)
        
        self.remove_channel_btn = QPushButton("Remove Selected")
        self.remove_channel_btn.clicked.connect(self.remove_selected_channels)
        
        channel_btn_layout.addWidget(self.refresh_channels_btn)
        channel_btn_layout.addWidget(self.remove_channel_btn)
        channels_layout.addLayout(channel_btn_layout)
        
        layout.addWidget(channels_group)
        
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
        
        layout.addWidget(log_group)
        
        return widget
    
    def setup_timer(self):
        """Setup timer for periodic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_monitoring_display)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def search_channels(self):
        """Search for channels"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search query")
            return
        
        # Disable search button and show progress
        self.search_btn.setEnabled(False)
        self.search_progress.setVisible(True)
        self.search_progress.setValue(0)
        
        # Start search worker
        self.search_worker = ChannelSearchWorker(query, 50)
        self.search_worker.results_ready.connect(self.on_search_results)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.progress_updated.connect(self.search_progress.setValue)
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.start()
    
    @Slot(list)
    def on_search_results(self, results: List[Dict]):
        """Handle search results"""
        self.search_results.setRowCount(len(results))
        
        for row, channel in enumerate(results):
            self.search_results.setItem(row, 0, QTableWidgetItem(channel.get("title", "Unknown")))
            self.search_results.setItem(row, 1, QTableWidgetItem(channel.get("username", "")))
            self.search_results.setItem(row, 2, QTableWidgetItem(str(channel.get("subscribers", "N/A"))))
            self.search_results.setItem(row, 3, QTableWidgetItem(channel.get("type", "Unknown")))
        
        self.add_selected_btn.setEnabled(len(results) > 0)
        self.log_activity(f"Search completed: {len(results)} channels found for '{self.search_input.text()}'")
    
    @Slot(str)
    def on_search_error(self, error: str):
        """Handle search error"""
        QMessageBox.critical(self, "Search Error", f"Error during search: {error}")
        self.log_activity(f"Search error: {error}")
    
    @Slot()
    def on_search_finished(self):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        self.search_progress.setVisible(False)
    
    def add_selected_channels(self):
        """Add selected channels to monitoring"""
        selected_rows = set()
        for item in self.search_results.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select channels to add")
            return
        
        channels_to_add = []
        for row in selected_rows:
            username_item = self.search_results.item(row, 1)
            if username_item and username_item.text():
                channels_to_add.append(username_item.text())
        
        if channels_to_add:
            self.add_channels_to_monitoring(channels_to_add)
    
    def add_manual_channel(self):
        """Add channel manually"""
        channel = self.manual_input.text().strip()
        if not channel:
            QMessageBox.warning(self, "Warning", "Please enter a channel username or ID")
            return
        
        self.add_channels_to_monitoring([channel])
        self.manual_input.clear()
    
    def add_channels_to_monitoring(self, channels: List[str]):
        """Add multiple channels to monitoring"""
        if not channels:
            return
        
        # Start batch worker to get channel info
        self.batch_worker = BatchInfoWorker(channels)
        self.batch_worker.results_ready.connect(self.on_batch_info_ready)
        self.batch_worker.error_occurred.connect(self.on_batch_info_error)
        self.batch_worker.start()
    
    @Slot(dict)
    def on_batch_info_ready(self, results: Dict[str, Optional[Dict]]):
        """Handle batch channel info results"""
        added_count = 0
        for channel, info in results.items():
            if info:
                self.monitored_channels.add(channel)
                added_count += 1
        
        if added_count > 0:
            self.update_channels_table()
            self.log_activity(f"Added {added_count} channels to monitoring")
        
        if added_count < len(results):
            failed_count = len(results) - added_count
            QMessageBox.warning(self, "Warning", f"{failed_count} channels could not be added")
    
    @Slot(str)
    def on_batch_info_error(self, error: str):
        """Handle batch info error"""
        QMessageBox.critical(self, "Error", f"Error getting channel information: {error}")
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.monitored_channels:
            QMessageBox.warning(self, "Warning", "No channels to monitor. Please add some channels first.")
            return
        
        try:
            # Start monitoring with callback
            start_monitoring(list(self.monitored_channels), self.on_channel_update, 30)
            
            self.monitoring_active = True
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)
            self.monitor_status.setText("Monitoring: Active")
            self.monitor_status.setStyleSheet("color: green; font-weight: bold;")
            
            self.log_activity(f"Started monitoring {len(self.monitored_channels)} channels")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            stop_monitoring()
            
            self.monitoring_active = False
            self.start_monitor_btn.setEnabled(True)
            self.stop_monitor_btn.setEnabled(False)
            self.monitor_status.setText("Monitoring: Inactive")
            self.monitor_status.setStyleSheet("color: red; font-weight: bold;")
            
            self.log_activity("Stopped monitoring")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop monitoring: {e}")
    
    def configure_monitoring(self):
        """Configure monitoring settings"""
        dialog = ChannelMonitoringDialog(self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()
            self.log_activity(f"Monitoring settings updated: {settings}")
    
    def on_channel_update(self, channel_id: str, update_data: Dict):
        """Handle channel update callback"""
        if update_data.get("type") == "new_messages":
            messages = update_data.get("messages", [])
            self.log_activity(f"New messages in {channel_id}: {len(messages)} messages")
    
    def update_monitoring_display(self):
        """Update monitoring display with current stats"""
        if not self.monitoring_active:
            return
        
        try:
            stats = get_monitoring_stats()
            
            # Update channels table
            self.channels_table.setRowCount(len(stats))
            
            for row, stat in enumerate(stats):
                info = stat.get("info", {})
                identifier = stat.get("identifier", "")
                
                self.channels_table.setItem(row, 0, QTableWidgetItem(info.get("title", "Unknown")))
                self.channels_table.setItem(row, 1, QTableWidgetItem(identifier))
                self.channels_table.setItem(row, 2, QTableWidgetItem(str(info.get("subscribers", "N/A"))))
                
                growth = stat.get("subscriber_growth", {})
                growth_text = f"+{growth.get('daily', 0)}/day"
                self.channels_table.setItem(row, 3, QTableWidgetItem(growth_text))
                
                activity = stat.get("activity_level", "Unknown")
                self.channels_table.setItem(row, 4, QTableWidgetItem(activity))
                
                last_update = stat.get("last_update", "")
                if last_update:
                    try:
                        dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"
                
                self.channels_table.setItem(row, 5, QTableWidgetItem(time_str))
                
                # Actions column - could add buttons here
                self.channels_table.setItem(row, 6, QTableWidgetItem("Active"))
        
        except Exception as e:
            self.log_activity(f"Error updating display: {e}")
    
    def update_channels_table(self):
        """Update the channels table with current monitored channels"""
        # This is a simplified version - in real implementation, 
        # you'd get actual channel info
        channels_list = list(self.monitored_channels)
        self.channels_table.setRowCount(len(channels_list))
        
        for row, channel in enumerate(channels_list):
            self.channels_table.setItem(row, 0, QTableWidgetItem("Loading..."))
            self.channels_table.setItem(row, 1, QTableWidgetItem(channel))
            self.channels_table.setItem(row, 2, QTableWidgetItem("Loading..."))
            self.channels_table.setItem(row, 3, QTableWidgetItem("N/A"))
            self.channels_table.setItem(row, 4, QTableWidgetItem("Unknown"))
            self.channels_table.setItem(row, 5, QTableWidgetItem("Never"))
            self.channels_table.setItem(row, 6, QTableWidgetItem("Inactive"))
    
    def refresh_all_channels(self):
        """Refresh information for all monitored channels"""
        if not self.monitored_channels:
            return
        
        # Force refresh all channels
        channels_list = list(self.monitored_channels)
        self.batch_worker = BatchInfoWorker(channels_list)
        self.batch_worker.results_ready.connect(self.on_refresh_complete)
        self.batch_worker.start()
    
    @Slot(dict)
    def on_refresh_complete(self, results: Dict):
        """Handle refresh completion"""
        self.log_activity(f"Refreshed information for {len(results)} channels")
    
    def remove_selected_channels(self):
        """Remove selected channels from monitoring"""
        selected_rows = set()
        for item in self.channels_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select channels to remove")
            return
        
        channels_to_remove = []
        for row in selected_rows:
            username_item = self.channels_table.item(row, 1)
            if username_item:
                channels_to_remove.append(username_item.text())
        
        for channel in channels_to_remove:
            self.monitored_channels.discard(channel)
        
        self.update_channels_table()
        self.log_activity(f"Removed {len(channels_to_remove)} channels from monitoring")
    
    def clear_search_results(self):
        """Clear search results"""
        self.search_results.setRowCount(0)
        self.add_selected_btn.setEnabled(False)
    
    def clear_cache(self):
        """Clear all caches"""
        try:
            clear_cache()
            self.log_activity("Cache cleared successfully")
            QMessageBox.information(self, "Success", "Cache cleared successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")
    
    def export_data(self):
        """Export monitoring data"""
        # Implementation for exporting data to JSON/CSV
        data = {
            "monitored_channels": list(self.monitored_channels),
            "export_time": datetime.now().isoformat(),
            "stats": get_monitoring_stats() if self.monitoring_active else []
        }
        
        try:
            with open("channel_data_export.json", "w") as f:
                json.dump(data, f, indent=2)
            
            self.log_activity("Data exported to channel_data_export.json")
            QMessageBox.information(self, "Success", "Data exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
    
    def load_search_history(self):
        """Load and display search history"""
        try:
            history = get_search_history(20)
            
            self.history_list.clear()
            for entry in history:
                item = QTreeWidgetItem([
                    entry["query"],
                    entry["date"],
                    str(len(entry["results"]))
                ])
                item.setData(0, Qt.UserRole, entry)
                self.history_list.addTopLevelItem(item)
        
        except Exception as e:
            self.log_activity(f"Error loading search history: {e}")
    
    def repeat_search(self, item: QTreeWidgetItem):
        """Repeat a search from history"""
        entry = item.data(0, Qt.UserRole)
        if entry:
            self.search_input.setText(entry["query"])
            self.search_channels()
    
    def clear_activity_log(self):
        """Clear activity log"""
        self.activity_log.clear()
    
    def log_activity(self, message: str):
        """Log activity message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
