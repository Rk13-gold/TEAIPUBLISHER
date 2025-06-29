
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget,
    QMessageBox, QFileDialog, QGroupBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from data.repository import Repository

# Import unified theme system
try:
    from gui.telegram_theme import TelegramTheme
except ImportError:
    TelegramTheme = None

class ContentTab(QWidget):
    def __init__(self):
        super().__init__()
        # Apply unified theme
        if TelegramTheme:
            TelegramTheme.apply_theme_to_widget(self)
        self.setWindowTitle("Títulos e Imágenes")
        self.repo = Repository()
        self.init_ui()
        self.load_titles()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Panel izquierdo: Títulos ---
        left_group = QGroupBox("Títulos")
        left_layout = QVBoxLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Nuevo título")
        left_layout.addWidget(self.title_input)

        btn_layout = QHBoxLayout()
        self.add_title_btn = QPushButton("Agregar")
        self.add_title_btn.clicked.connect(self.add_title)
        btn_layout.addWidget(self.add_title_btn)
        self.edit_title_btn = QPushButton("Editar")
        self.edit_title_btn.clicked.connect(self.edit_title)
        btn_layout.addWidget(self.edit_title_btn)
        self.delete_title_btn = QPushButton("Eliminar")
        self.delete_title_btn.clicked.connect(self.delete_title)
        btn_layout.addWidget(self.delete_title_btn)
        left_layout.addLayout(btn_layout)

        self.titles_list = QListWidget()
        self.titles_list.currentItemChanged.connect(self.load_images)
        left_layout.addWidget(self.titles_list)
        left_group.setLayout(left_layout)
        main_layout.addWidget(left_group, 1)

        # --- Panel derecho: Imágenes asociadas ---
        right_group = QGroupBox("Imágenes asociadas")
        right_layout = QVBoxLayout()

        self.images_list = QListWidget()
        self.images_list.currentItemChanged.connect(self.show_image_preview)
        right_layout.addWidget(self.images_list)

        # Previsualización de imagen
        self.image_preview = QLabel("Previsualización")
        self.image_preview.setFixedSize(180, 180)
        self.image_preview.setStyleSheet("background: #232E3C; border-radius: 8px;")
        self.image_preview.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.image_preview)

        self.upload_btn = QPushButton("Subir Imagen")
        self.upload_btn.clicked.connect(self.upload_image)
        right_layout.addWidget(self.upload_btn)

        right_group.setLayout(right_layout)
        main_layout.addWidget(right_group, 2)

        self.setLayout(main_layout)

    def load_titles(self):
        self.titles_list.clear()
        self.titles = self.repo.get_titles()
        for title in self.titles:
            self.titles_list.addItem(f"{title.id}: {title.name}")

    def get_selected_title_id(self):
        item = self.titles_list.currentItem()
        if item:
            return int(item.text().split(":")[0])
        return None

    def add_title(self):
        name = self.title_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Advertencia", "El título no puede estar vacío.")
            return
        self.repo.add_title(name)
        self.load_titles()
        self.title_input.clear()

    def edit_title(self):
        item = self.titles_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Advertencia", "Seleccione un título para editar.")
            return
        new_name = self.title_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Advertencia", "El nuevo título no puede estar vacío.")
            return
        title_id = int(item.text().split(":")[0])
        self.repo.update_title(title_id, new_name)
        self.load_titles()
        self.title_input.clear()

    def delete_title(self):
        item = self.titles_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Advertencia", "Seleccione un título para eliminar.")
            return
        title_id = int(item.text().split(":")[0])
        self.repo.delete_title(title_id)
        self.load_titles()
        self.images_list.clear()
        self.title_input.clear()
        self.image_preview.clear()
        self.image_preview.setText("Previsualización")

    def load_images(self):
        self.images_list.clear()
        self.image_preview.clear()
        self.image_preview.setText("Previsualización")
        title_id = self.get_selected_title_id()
        if not title_id:
            return
        images = self.repo.get_images_by_title(title_id)
        if not images:
            self.images_list.addItem("No hay imágenes asociadas a este título.")
        else:
            for image in images:
                self.images_list.addItem(f"{image.id}: {image.path}")

    def show_image_preview(self):
        item = self.images_list.currentItem()
        if not item or ":" not in item.text():
            self.image_preview.clear()
            self.image_preview.setText("Previsualización")
            return
        image_path = item.text().split(":", 1)[1].strip()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.width(),
                self.image_preview.height(),
                aspectRatioMode=Qt.KeepAspectRatio,
                transformMode=Qt.SmoothTransformation
            ))
        else:
            self.image_preview.setText("No se pudo cargar")

    def upload_image(self):
        title_id = self.get_selected_title_id()
        if not title_id:
            QMessageBox.warning(self, "Error", "Seleccione un título antes de subir una imagen.")
            return
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Images (*.png *.jpg *.jpeg *.gif);;All Files (*)")
        if not file_name:
            return
        try:
            self.repo.add_image(title_id=title_id, path=file_name)
            QMessageBox.information(self, "Éxito", "Imagen subida y asociada correctamente.")
            self.load_images()
            
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap.scaled(
                    self.image_preview.width(),
                    self.image_preview.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
            else:
                self.image_preview.setText("No se pudo cargar")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo subir la imagen: {e}")