import logging
import os

class Logger:
    def __init__(self, log_file='app.log'):
        self.logger = logging.getLogger('TelegramAIPublisher')
        self.logger.setLevel(logging.DEBUG)

        # Evita agregar múltiples handlers si ya existen
        if not self.logger.handlers:
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

def setup_logging(log_file='app.log'):
    """
    Configura el logging global para la aplicación.
    """
    Logger(log_file=log_file)

# Instancia global opcional
log_file_path = os.path.join(os.path.dirname(__file__), 'app.log')
logger = Logger(log_file=log_file_path)