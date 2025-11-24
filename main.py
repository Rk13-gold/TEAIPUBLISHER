from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt
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
    
    # Configurar el estilo de la aplicación
    app_style = QStyleFactory.create('Fusion')
    app.setStyle(app_style)
    
    # Configurar la aplicación
    app.setApplicationName("Telegram AI Publisher")
    app.setApplicationVersion("1.0.0")
    
    # Configuración de alta resolución (el atributo AA_UseHighDpiPixmaps está obsoleto en PySide6 6.0+)
    # PySide6 ya maneja automáticamente el escalado de alta resolución
    
    main_window = MainWindow(config)
    main_window.show()

    # Run the Qt application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()