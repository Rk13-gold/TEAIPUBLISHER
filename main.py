from PySide6.QtWidgets import QApplication
import sys
from gui.main_window import MainWindow
from core.config import Config
from core.logger import setup_logging
from core.database import Database

from gui.telegram_theme import TelegramTheme


def main():
    """Main application entry point"""
    setup_logging()
    config = Config()
    db = Database()
    db.create_tables()
    
    app = QApplication(sys.argv)
    TelegramTheme.apply_application_theme(app)  # Apply global theme
    main_window = MainWindow(config)
    main_window.show()

    # Run the Qt application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()