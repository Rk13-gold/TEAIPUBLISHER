from PySide6.QtWidgets import QApplication
import sys
from gui.main_window import MainWindow
from core.config import Config
from core.logger import setup_logging
from core.database import Database
from theme import apply_telegram_compact_theme as apply_telegram_theme
def main():
    setup_logging()
    config = Config()
    db = Database()
    db.create_tables()
    app = QApplication(sys.argv)
    apply_telegram_theme(app)  # <--- Aplica el tema global
    main_window = MainWindow(config)
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()