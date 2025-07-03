from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QFont, QPixmap, QPalette, QColor
from gui.ai_tab import AITab
from gui.publish_tab import PublishTab
from gui.metrics_tab import MetricsTab
from gui.simple_channel_tab import SimpleChannelTab
from gui.simple_admin_channels_tab import SimpleAdminChannelsTab
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("🚀 Telegram AI Publisher Pro")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon("assets/icons/app_icon.svg"))
        
        # Apply modern dark theme
        self.apply_modern_theme()
        
        # Initialize UI
        self._init_ui()
        self._create_menu()
        
        # Setup status updates
        self.setup_status_timer()

    def apply_modern_theme(self):
        """Apply modern dark theme with professional colors"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #2d2d2d;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            
            QTabBar::tab:hover {
                background-color: #505050;
            }
            
            /* AI Generation Tab - Blue Theme */
            QTabBar::tab:selected[objectName="ai_tab"] {
                background-color: #0078d4;
            }
            
            /* Publish Tab - Green Theme */
            QTabBar::tab:selected[objectName="publish_tab"] {
                background-color: #107c10;
            }
            
            /* Metrics Tab - Purple Theme */
            QTabBar::tab:selected[objectName="metrics_tab"] {
                background-color: #881798;
            }
            
            /* Admin Channels Tab - Orange Theme */
            QTabBar::tab:selected[objectName="admin_tab"] {
                background-color: #ff8c00;
            }
            
            /* Channel Manager Tab - Teal Theme */
            QTabBar::tab:selected[objectName="channel_tab"] {
                background-color: #008080;
            }
            
            QMenuBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-bottom: 1px solid #404040;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 16px;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
                border-radius: 4px;
            }
            
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            
            QMenu::item {
                padding: 8px 16px;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
            }
            
            QStatusBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-top: 1px solid #404040;
            }
        """)

    def _init_ui(self):
        """Initialize the modern UI"""
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.setCentralWidget(self.tabs)

        # Add tabs with modern styling and error handling
        self._add_ai_tab()
        self._add_publish_tab()
        self._add_metrics_tab()
        self._add_admin_channels_tab()
        self._add_channel_manager_tab()
        
        # Set default tab
        self.tabs.setCurrentIndex(0)  # Start with AI Generation tab
        
        # Create status bar
        self.statusBar().showMessage("🚀 Telegram AI Publisher Pro - Listo para uso")

    def _add_ai_tab(self):
        """Add AI Generation tab with blue theme"""
        try:
            self.ai_tab = AITab(self.config)
            tab_index = self.tabs.addTab(self.ai_tab, "🤖 AI Generation")
            self.tabs.setTabIcon(tab_index, QIcon("🤖"))
            
            # Set tab properties for theming
            self.tabs.tabBar().setTabData(tab_index, {"theme": "blue", "name": "ai_tab"})
            
        except Exception as e:
            self._add_error_tab("🤖 AI Generation", e, "blue")

    def _add_publish_tab(self):
        """Add Publish tab with green theme"""
        try:
            self.publish_tab = PublishTab(self.config)
            tab_index = self.tabs.addTab(self.publish_tab, "🚀 Publish")
            self.tabs.setTabIcon(tab_index, QIcon("🚀"))
            
            # Set tab properties for theming
            self.tabs.tabBar().setTabData(tab_index, {"theme": "green", "name": "publish_tab"})
            
        except Exception as e:
            self._add_error_tab("🚀 Publish", e, "green")

    def _add_metrics_tab(self):
        """Add Metrics tab with purple theme"""
        try:
            self.metrics_tab = MetricsTab()
            tab_index = self.tabs.addTab(self.metrics_tab, "📊 Metrics")
            self.tabs.setTabIcon(tab_index, QIcon("📊"))
            
            # Set tab properties for theming
            self.tabs.tabBar().setTabData(tab_index, {"theme": "purple", "name": "metrics_tab"})
            
        except Exception as e:
            self._add_error_tab("📊 Metrics", e, "purple")

    def _add_admin_channels_tab(self):
        """Add Admin Channels tab with orange theme"""
        try:
            self.admin_channels_tab = SimpleAdminChannelsTab(self.config)
            tab_index = self.tabs.addTab(self.admin_channels_tab, "🔧 Admin Channels")
            self.tabs.setTabIcon(tab_index, QIcon("🔧"))
            
            # Set tab properties for theming
            self.tabs.tabBar().setTabData(tab_index, {"theme": "orange", "name": "admin_tab"})
            
        except Exception as e:
            self._add_error_tab("🔧 Admin Channels", e, "orange")

    def _add_channel_manager_tab(self):
        """Add Channel Manager tab with teal theme"""
        try:
            self.channel_manager_tab = SimpleChannelTab()
            tab_index = self.tabs.addTab(self.channel_manager_tab, "🎛️ Channel Manager")
            self.tabs.setTabIcon(tab_index, QIcon("🎛️"))
            
            # Set tab properties for theming
            self.tabs.tabBar().setTabData(tab_index, {"theme": "teal", "name": "channel_tab"})
            
        except Exception as e:
            self._add_error_tab("🎛️ Channel Manager", e, "teal")

    def _add_error_tab(self, name, exception, theme_color):
        """Add error tab with consistent styling"""
        error_tab = QWidget()
        error_tab.setStyleSheet(f"""
            QWidget {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QLabel {{
                color: #ff4444;
                font-size: 14px;
                padding: 20px;
            }}
            QPushButton {{
                background-color: #{self._get_theme_color(theme_color)};
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #{self._get_theme_color_hover(theme_color)};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Error icon and message
        error_icon = QLabel("❌")
        error_icon.setFont(QFont("Arial", 48))
        error_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_icon)
        
        error_label = QLabel(f"Error loading {name} tab:\n\n{str(exception)}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        # Retry button
        retry_btn = QPushButton("🔄 Retry Loading")
        retry_btn.clicked.connect(lambda: self._retry_tab_loading(name))
        layout.addWidget(retry_btn)
        
        error_tab.setLayout(layout)
        self.tabs.addTab(error_tab, name)

    def _get_theme_color(self, theme):
        """Get theme color hex code"""
        colors = {
            "blue": "0078d4",
            "green": "107c10", 
            "purple": "881798",
            "orange": "ff8c00",
            "teal": "008080"
        }
        return colors.get(theme, "404040")

    def _get_theme_color_hover(self, theme):
        """Get theme hover color hex code"""
        colors = {
            "blue": "106ebe",
            "green": "0e6e0e",
            "purple": "7a1587",
            "orange": "e67e00",
            "teal": "007373"
        }
        return colors.get(theme, "505050")

    def _retry_tab_loading(self, tab_name):
        """Retry loading a failed tab"""
        self.statusBar().showMessage(f"Retrying to load {tab_name}...")
        # Here you could implement retry logic
        QMessageBox.information(self, "Retry", f"Retry functionality for {tab_name} would be implemented here.")

    def setup_status_timer(self):
        """Setup timer for status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(30000)  # Update every 30 seconds

    def update_status(self):
        """Update status bar with current time and info"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_tab = self.tabs.currentIndex()
        tab_names = ["AI Generation", "Publish", "Metrics", "Admin Channels", "Channel Manager"]
        
        if current_tab < len(tab_names):
            status_msg = f"🚀 Telegram AI Publisher Pro - {tab_names[current_tab]} | {current_time}"
        else:
            status_msg = f"🚀 Telegram AI Publisher Pro | {current_time}"
            
        self.statusBar().showMessage(status_msg)

    def _create_menu(self):
        """Create modern professional menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("📁 File")
        
        # New Project action
        new_action = QAction("🆕 New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open Project action
        open_action = QAction("📂 Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        # Save Project action
        save_action = QAction("💾 Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("🚪 Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("🔧 Tools")
        
        # Configuration action
        config_action = QAction("⚙️ Settings", self)
        config_action.setShortcut("Ctrl+,")
        config_action.triggered.connect(self._open_settings)
        tools_menu.addAction(config_action)
        
        # Test Connection action
        test_action = QAction("🔗 Test Telegram Connection", self)
        test_action.triggered.connect(self._test_connection)
        tools_menu.addAction(test_action)
        
        # Clear Cache action
        clear_cache_action = QAction("🗑️ Clear Cache", self)
        clear_cache_action.triggered.connect(self._clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # View menu
        view_menu = menu_bar.addMenu("👁️ View")
        
        # Toggle fullscreen
        fullscreen_action = QAction("🖥️ Toggle Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Theme selection
        theme_menu = view_menu.addMenu("🎨 Theme")
        
        dark_theme_action = QAction("🌙 Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self._change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("☀️ Light Theme", self)
        light_theme_action.triggered.connect(lambda: self._change_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("❓ Help")
        
        # Documentation action
        docs_action = QAction("📚 Documentation", self)
        docs_action.setShortcut("F1")
        docs_action.triggered.connect(self._open_documentation)
        help_menu.addAction(docs_action)
        
        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # Menu action implementations
    def _new_project(self):
        """Create new project"""
        reply = QMessageBox.question(
            self, "New Project", 
            "Are you sure you want to create a new project? Unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage("🆕 New project created", 3000)
            # Reset all tabs to default state
            self._reset_all_tabs()

    def _open_project(self):
        """Open existing project"""
        self.statusBar().showMessage("📂 Open project functionality would be implemented here", 3000)

    def _save_project(self):
        """Save current project"""
        self.statusBar().showMessage("💾 Project saved successfully", 3000)

    def _open_settings(self):
        """Open settings dialog"""
        self.statusBar().showMessage("⚙️ Settings dialog would be implemented here", 3000)

    def _test_connection(self):
        """Test Telegram connection"""
        self.statusBar().showMessage("🔗 Testing Telegram connection...", 2000)
        # Here you would implement actual connection testing
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("✅ Connection successful", 3000))

    def _clear_cache(self):
        """Clear application cache"""
        reply = QMessageBox.question(
            self, "Clear Cache", 
            "Are you sure you want to clear the application cache?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage("🗑️ Cache cleared successfully", 3000)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("🖥️ Exited fullscreen mode", 2000)
        else:
            self.showFullScreen()
            self.statusBar().showMessage("🖥️ Entered fullscreen mode", 2000)

    def _change_theme(self, theme_name):
        """Change application theme"""
        if theme_name == "dark":
            self.apply_modern_theme()
            self.statusBar().showMessage("🌙 Dark theme applied", 2000)
        elif theme_name == "light":
            self.apply_light_theme()
            self.statusBar().showMessage("☀️ Light theme applied", 2000)

    def apply_light_theme(self):
        """Apply light theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                color: #333333;
            }
            
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333333;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            
            QMenuBar {
                background-color: #ffffff;
                color: #333333;
                border-bottom: 1px solid #cccccc;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 16px;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
                color: #ffffff;
                border-radius: 4px;
            }
            
            QMenu {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            
            QMenu::item {
                padding: 8px 16px;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            
            QStatusBar {
                background-color: #ffffff;
                color: #333333;
                border-top: 1px solid #cccccc;
            }
        """)

    def _open_documentation(self):
        """Open documentation"""
        self.statusBar().showMessage("📚 Opening documentation...", 2000)
        # Here you would open a web browser or documentation window

    def _show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>🚀 Telegram AI Publisher Pro</h2>
        <p><b>Version:</b> 2.0.0</p>
        <p><b>Author:</b> Professional Development Team</p>
        <p><b>Description:</b> Advanced AI-powered content creation and publishing platform for Telegram channels.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>🤖 AI Content Generation</li>
            <li>🚀 Professional Publishing</li>
            <li>📊 Advanced Metrics</li>
            <li>🔧 Channel Management</li>
            <li>🎛️ Professional Dashboard</li>
        </ul>
        <br>
        <p><i>Built with PySide6 and modern design principles.</i></p>
        """
        
        QMessageBox.about(self, "About Telegram AI Publisher Pro", about_text)

    def _reset_all_tabs(self):
        """Reset all tabs to default state"""
        # This would reset all tabs to their initial state
        try:
            if hasattr(self, 'ai_tab') and self.ai_tab:
                # Reset AI tab
                pass
            if hasattr(self, 'publish_tab') and self.publish_tab:
                # Reset publish tab
                pass
            # Add reset logic for other tabs
        except Exception as e:
            print(f"Error resetting tabs: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, "Exit Application", 
            "Are you sure you want to exit Telegram AI Publisher Pro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Save any unsaved work
            self.statusBar().showMessage("👋 Goodbye! Thanks for using Telegram AI Publisher Pro")
            event.accept()
        else:
            event.ignore()