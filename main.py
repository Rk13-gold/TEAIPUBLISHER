from PySide6.QtWidgets import QApplication
import sys
from gui.main_window import MainWindow
from core.config import Config
from core.logger import setup_logging
from core.database import Database


def main():
    """Main application entry point"""
    setup_logging()
    config = Config()
    db = Database()
    db.create_tables()
    
    app = QApplication(sys.argv)
    main_window = MainWindow(config)
    main_window.show()

    # Run the Qt application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()