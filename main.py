from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import sys
import os
import warnings

# Configurar advertencias para que no muestren los mensajes de PySide6
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'
warnings.filterwarnings("ignore", category=RuntimeWarning)

from core.config import Config
from core.logger import setup_logging
from core.database import Database
from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    setup_logging()
    config = Config()
    db = Database()
    db.create_tables()
    
    app = QApplication(sys.argv)
    app.setDesktopFileName("telegram-ai-publisher")
    
    # Configurar el estilo de la aplicación
    app_style = QStyleFactory.create('Fusion')
    app.setStyle(app_style)
    
    # Configurar la aplicación
    app.setApplicationName("Telegram AI Publisher")
    app.setApplicationVersion("1.0.0")

    # Establecer icono global desde el arranque (logo.svg -> fallback alternos)
    icons_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets",
        "icons",
    )
    icon_path = None
    for filename in ("logo.svg", "logo.png", "app_icon.svg"):
        candidate = os.path.join(icons_dir, filename)
        if os.path.exists(candidate):
            icon_path = candidate
            break
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    # Configuración de alta resolución (el atributo AA_UseHighDpiPixmaps está obsoleto en PySide6 6.0+)
    # PySide6 ya maneja automáticamente el escalado de alta resolución
    
    main_window = MainWindow(config, icon_path=icon_path)
    main_window.show()

    # Run the Qt application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()