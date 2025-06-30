from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QFileDialog, QHBoxLayout, QMessageBox, QGroupBox
from PySide6.QtCore import Qt
import os

class FileUploadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths = []  # Mantener rutas completas separadamente
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Grupo para archivos adicionales
        group = QGroupBox("📎 Archivos Adicionales")
        group_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(120)
        group_layout.addWidget(self.file_list)

        # Botones
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ Agregar")
        self.add_btn.clicked.connect(self.add_files)
        btn_row.addWidget(self.add_btn)

        self.remove_btn = QPushButton("🗑️ Eliminar")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_row.addWidget(self.remove_btn)

        group_layout.addLayout(btn_row)
        group.setLayout(group_layout)
        layout.addWidget(group)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos adicionales",
            "",
            "Todos los medios (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.mp4 *.mov *.avi *.mkv *.pdf *.doc *.docx *.txt *.zip *.rar);;Imágenes (*.png *.jpg *.jpeg *.bmp *.webp);;Videos (*.mp4 *.mov *.avi *.mkv);;GIFs (*.gif);;Documentos (*.pdf *.doc *.docx *.txt *.zip *.rar)"
        )
        for f in files:
            if f not in self.file_paths:
                self.file_paths.append(f)
                filename = os.path.basename(f)
                ext = f.lower().split('.')[-1]
                
                # Iconos según tipo de archivo
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
                    icon = "📷"
                elif ext in ['mp4', 'mov', 'avi', 'mkv']:
                    icon = "🎬"
                elif ext == 'gif':
                    icon = "🎞️"
                elif ext in ['pdf', 'doc', 'docx']:
                    icon = "📄"
                elif ext in ['zip', 'rar']:
                    icon = "📦"
                else:
                    icon = "📎"
                
                self.file_list.addItem(f"{icon} {filename}")

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            if row < len(self.file_paths):
                self.file_paths.pop(row)

    def get_files(self):
        return self.file_paths.copy()

    def clear_files(self):
        """Limpiar todos los archivos"""
        self.file_list.clear()
        self.file_paths.clear()