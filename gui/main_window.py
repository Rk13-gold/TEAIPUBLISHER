from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction, QIcon
from gui.dashboard import Dashboard
from gui.content_tab import ContentTab
from gui.ai_tab import AITab
from gui.publish_tab import PublishTab
from gui.metrics_tab import MetricsTab
from gui.simple_channel_tab import SimpleChannelTab
from gui.simple_admin_channels_tab import SimpleAdminChannelsTab

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self
        # Apply unified theme to main window
        # (Asegúrate de que TelegramTheme y app estén definidos si usas esto)
        # if hasattr(app, "instance") and app.instance():
        #     TelegramTheme.apply_application_theme(app.instance())

        self.setWindowTitle("Telegram AI Publisher")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("assets/icons/app_icon.svg"))
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instancia de cada pestaña con manejo de errores
        try:
            self.dashboard = Dashboard(self.config)
            self.tabs.addTab(self.dashboard, "Dashboard")
        except Exception as e:
            self._add_error_tab("Dashboard", e)

        try:
            self.content_tab = ContentTab()
            self.tabs.addTab(self.content_tab, "Content")
        except Exception as e:
            self._add_error_tab("Content", e)

        try:
            self.ai_tab = AITab(self.config)
            self.tabs.addTab(self.ai_tab, "AI Generation")
        except Exception as e:
            self._add_error_tab("AI Generation", e)

        try:
            self.publish_tab = PublishTab(self.config)
            self.tabs.addTab(self.publish_tab, "Publish")
        except Exception as e:
            self._add_error_tab("Publish", e)

        try:
            self.metrics_tab = MetricsTab()
            self.tabs.addTab(self.metrics_tab, "Metrics")
        except Exception as e:
            self._add_error_tab("Metrics", e)

        # Simple Admin Channels Tab (with default theme)
        try:
            self.admin_channels_tab = SimpleAdminChannelsTab(self.config)
            self.tabs.addTab(self.admin_channels_tab, "🤖 Admin Channels")
        except Exception as e:
            self._add_error_tab("Admin Channels", e)

        # Enhanced Channel Manager Tab (Simplified version)
        try:
            self.enhanced_channel_tab = SimpleChannelTab()
            self.tabs.addTab(self.enhanced_channel_tab, "Channel Manager")
        except Exception as e:
            self._add_error_tab("Channel Manager", e)

        # Nueva pestaña: Bot de Notas de Voz
        try:
            from gui.voice_note_tab import VoiceNoteTab
            self.voice_note_tab = VoiceNoteTab()
            self.tabs.addTab(self.voice_note_tab, "Bot Voz Telegram")
        except Exception as e:
            self._add_error_tab("Bot Voz Telegram", e)

        # Si tienes señales personalizadas, conéctalas aquí si es necesario

    def _add_error_tab(self, name, exception):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        error_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Error loading {name} tab:\n{exception}"))
        error_tab.setLayout(layout)
        self.tabs.addTab(error_tab, name)

    def _create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("Help")