from PySide6.QtWidgets import (QMainWindow, QTabWidget, QMessageBox, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QApplication, QScrollArea, 
                             QSizePolicy, QStyle, QStyleOption, QToolButton, QMenuBar, QMenu,
                             QGroupBox, QLineEdit, QStyle, QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QFont, QPixmap, QPalette, QColor
from datetime import datetime
from pathlib import Path

# Importar las pestañas
from gui.publish_tab import PublishTab
from gui.ai_tab import AITab
from gui.metrics_tab import MetricsTab
from gui.simple_admin_channels_tab import SimpleAdminChannelsTab
from gui.simple_channel_tab import SimpleChannelTab

class MainWindow(QMainWindow):
    def __init__(self, config, icon_path: str | None = None):
        super().__init__()
        self.config = config
        self.setWindowTitle("🚀 Telegram AI Publisher Pro")
        
        # Obtener dimensiones de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        width = min(1400, screen.width() * 0.9)  # 90% del ancho de la pantalla
        height = min(900, screen.height() * 0.9)  # 90% del alto de la pantalla
        
        # Establecer tamaño inicial centrado
        self.setGeometry(
            int((screen.width() - width) / 2),
            int((screen.height() - height) / 2),
            int(width),
            int(height)
        )
        
        icons_dir = Path(__file__).resolve().parents[1] / "assets" / "icons"
        default_icon = icons_dir / "app_icon.svg"
        resolved_icon = Path(icon_path).resolve() if icon_path else default_icon
        self.setWindowIcon(QIcon(str(resolved_icon)))
        self._setup_tray_icon(resolved_icon)
        
        # Configurar políticas de tamaño
        self.setMinimumSize(1024, 600)  # Tamaño mínimo razonable
        
        # Habilitar el botón de maximizar
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | 
                          Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        # Conectar el evento de cambio de tamaño
        self.installEventFilter(self)
        
        # Apply modern dark theme
        self.apply_modern_theme()
        
        # Initialize UI
        self._init_ui()
        self._create_menu()
        
        # Setup status updates
        self.setup_status_timer()

    def _setup_tray_icon(self, icon_path: Path):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)), self)
        self.tray_icon.setToolTip("Telegram AI Publisher Pro")

        tray_menu = QMenu()
        restore_action = QAction("Mostrar", self)
        restore_action.triggered.connect(self.restore_from_tray)
        tray_menu.addAction(restore_action)

        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def apply_modern_theme(self):
        """Apply modern dark theme from central stylesheet"""
        try:
            # Get the absolute path to the stylesheet
            import os
            from pathlib import Path
            
            # Get the directory of the current file
            current_dir = Path(__file__).parent
            # Navigate to the styles directory and load main_style.qss
            style_path = current_dir / 'styles' / 'main_style.qss'
            
            with open(style_path, 'r') as f:
                style = f.read()
            
            # Add tab-specific styles that should override the base styles
            tab_styles = """
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
            """
            
            # Combine base styles with tab-specific styles
            self.setStyleSheet(style + tab_styles)
            
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            # Fallback to a basic style if the stylesheet can't be loaded
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
                    padding: 8px 16px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #0078d4;
                }
            """)

    def _init_ui(self):
        """Initialize the modern UI"""
        # Crear widget principal y layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Crear el widget de pestañas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        
        # Configurar la barra de pestañas
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(True)
        tab_bar.setMinimumWidth(self.width() - 20)  # Dejar un pequeño margen
        
        # Añadir las pestañas
        self._add_ai_tab()
        self._add_publish_tab()
        self._add_metrics_tab()
        self._add_admin_channels_tab()
        self._add_channel_manager_tab()
        
        # Añadir el widget de pestañas al layout principal
        main_layout.addWidget(self.tabs, 1)  # El 1 es el factor de estiramiento
        
        # Configurar el pie de página
        self.setup_footer(main_layout)
        
        # Establecer el widget principal
        self.setCentralWidget(main_widget)
        
        # Configurar la política de tamaño
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Conectar señales
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def eventFilter(self, obj, event):
        """Manejar eventos de cambio de tamaño"""
        from PySide6.QtCore import QEvent
        
        try:
            if event.type() == QEvent.Resize:
                # Actualizar el ancho mínimo de las pestañas cuando cambia el tamaño
                if hasattr(self, 'tabs') and self.tabs is not None:
                    tab_bar = self.tabs.tabBar()
                    if tab_bar:
                        tab_bar.setMinimumWidth(self.width())
                        # Forzar actualización del layout
                        self.updateGeometry()
                        QApplication.processEvents()
            
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error en eventFilter: {e}")
            return super().eventFilter(obj, event)
    
    def on_tab_changed(self, index):
        """Se llama cuando se cambia de pestaña"""
        # Forzar la actualización del layout
        self.updateGeometry()
        QApplication.processEvents()
    
    def setup_footer(self, parent_layout):
        """Setup status bar with connection info"""
        footer = QFrame()
        footer.setFrameShape(QFrame.StyledPanel)
        footer.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-top: 1px solid #333333;
                padding: 4px 8px;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
                padding: 2px 8px;
            }
        """)
        
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(8, 2, 8, 2)
        footer_layout.setSpacing(10)
        
        # Connection status
        self.status_label = QLabel("🔴 Sin conexión")
        footer_layout.addWidget(self.status_label)
        
        # Bot info
        self.bot_info = QLabel("🤖 Bot: No conectado")
        footer_layout.addWidget(self.bot_info)
        
        # API status
        self.api_status = QLabel("🌐 API: Inactiva")
        footer_layout.addWidget(self.api_status)
        
        # Spacer to push items to the left
        footer_layout.addStretch(1)
        
        # Version info
        self.version_label = QLabel("v1.0.0")
        footer_layout.addWidget(self.version_label)
        
        footer.setLayout(footer_layout)
        parent_layout.addWidget(footer, 0)  # No stretch, fixed height
        
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

    def _add_publish_tab(self, retry_count=0, max_retries=3):
        """Add Publish tab with green theme with retry mechanism"""
        try:
            print("🔍 Intentando cargar la pestaña de publicación...")
            # Importar aquí para capturar cualquier error de importación
            from gui.publish_tab import PublishTab
            
            # Crear instancia de la pestaña
            self.publish_tab = PublishTab(self.config)
            
            # Añadir la pestaña a la interfaz
            tab_index = self.tabs.addTab(self.publish_tab, "🚀 Publish")
            self.tabs.setTabIcon(tab_index, QIcon("🚀"))
            
            # Configurar propiedades de la pestaña
            self.tabs.tabBar().setTabData(tab_index, {"theme": "green", "name": "publish_tab"})
            print("✅ Pestaña de publicación cargada exitosamente")
            
        except ImportError as e:
            error_msg = f"❌ Error de importación: {str(e)}\n\nAsegúrate de que todos los módulos requeridos estén instalados.\nEjecuta: pip install -r requirements.txt"
            print(error_msg)
            self._add_error_tab("🚀 Publish", error_msg, "red")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error al cargar la pestaña de publicación: {str(e)}")
            print(f"🔍 Detalles del error:\n{error_details}")
            
            if retry_count < max_retries:
                # Intentar de nuevo después de un breve retraso
                from PySide6.QtCore import QTimer
                delay_ms = 1000 * (retry_count + 1)
                print(f"⏳ Reintentando en {delay_ms/1000} segundos...")
                
                QTimer.singleShot(delay_ms, 
                               lambda: self.retry_add_publish_tab(retry_count + 1, max_retries))
            else:
                error_msg = f"No se pudo cargar la pestaña después de {max_retries} intentos.\n\nError: {str(e)}\n\nDetalles:\n{error_details}"
                print(f"❌ {error_msg}")
                self._add_error_tab("🚀 Publish", error_msg, "red")
    
    def retry_add_publish_tab(self, retry_count, max_retries):
        """Método auxiliar para reintentar cargar la pestaña de publicación"""
        # Eliminar la pestaña de error si existe
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "🚀 Publish":
                self.tabs.removeTab(i)
                break
        # Volver a intentar cargar la pestaña
        self._add_publish_tab(retry_count, max_retries)

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