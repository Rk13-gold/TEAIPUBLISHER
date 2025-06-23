from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QFileDialog, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt

class FileUploadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Archivos del post (imágenes, videos, gifs, docs)")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Agregar archivo")
        self.add_btn.clicked.connect(self.add_files)
        btn_row.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Eliminar seleccionado")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_row.addWidget(self.remove_btn)

        layout.addLayout(btn_row)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos",
            "",
            "Todos los archivos (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.mp4 *.mov *.avi *.mkv *.pdf *.doc *.docx *.txt *.zip *.rar);;Imágenes (*.png *.jpg *.jpeg *.bmp *.webp);;Videos (*.mp4 *.mov *.avi *.mkv);;GIFs (*.gif);;Documentos (*.pdf *.doc *.docx *.txt *.zip *.rar)"
        )
        for f in files:
            if f not in self.get_files():
                self.file_list.addItem(f)

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def get_files(self):
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]