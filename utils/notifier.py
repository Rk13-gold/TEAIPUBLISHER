from PySide6.QtWidgets import QMessageBox

class Notifier:
    @staticmethod
    def show_info(message: str, title: str = "Información"):
        QMessageBox.information(None, title, message)

    @staticmethod
    def show_warning(message: str, title: str = "Advertencia"):
        QMessageBox.warning(None, title, message)

    @staticmethod
    def show_error(message: str, title: str = "Error"):
        QMessageBox.critical(None, title, message)

    @staticmethod
    def show_question(message: str, title: str = "Pregunta") -> bool:
        reply = QMessageBox.question(None, title, message, QMessageBox.Yes | QMessageBox.No)
        return reply == QMessageBox.Yes