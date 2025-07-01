from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from core.database import Database
from services.metrics import MetricsService


# Import unified theme system
try:
    from gui.telegram_theme import TelegramTheme
except ImportError:
    TelegramTheme = None

class MetricsTab(QWidget):
    def __init__(self):
        super().__init__()
        # Apply unified theme
        if TelegramTheme:
            TelegramTheme.apply_theme_to_widget(self)
        self.setWindowTitle("Métricas y Estadísticas")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Visualización de Métricas")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Título", "Publicaciones", "Interacciones", "Clics"])
        self.layout.addWidget(self.table)

        self.refresh_button = QPushButton("Actualizar Métricas")
        self.refresh_button.clicked.connect(self.load_metrics)
        self.layout.addWidget(self.refresh_button)

        self.setLayout(self.layout)
        self.db = Database()
        self.metrics_service = MetricsService(self.db)
        self.load_metrics()

    def load_metrics(self):
        try:
            metrics_data = self.metrics_service.get_metrics()
            if not isinstance(metrics_data, list):
                raise ValueError("El servicio de métricas no devolvió una lista.")
            self.table.setRowCount(len(metrics_data))
            self.table.clearContents()

            for row_index, data in enumerate(metrics_data):
                self.table.setItem(row_index, 0, QTableWidgetItem(str(data.get('title', ''))))
                self.table.setItem(row_index, 1, QTableWidgetItem(str(data.get('posts', 0))))
                self.table.setItem(row_index, 2, QTableWidgetItem(str(data.get('interactions', 0))))
                self.table.setItem(row_index, 3, QTableWidgetItem(str(data.get('clicks', 0))))
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar métricas", f"Ocurrió un error al cargar las métricas:\n{e}")
            self.table.setRowCount(0)