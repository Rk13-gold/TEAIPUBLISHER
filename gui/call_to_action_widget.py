from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class CallToActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Llamado a la acción (CTA)")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.cta_edit = QTextEdit()
        self.cta_edit.setPlaceholderText("Ejemplo: ¡Haz clic en el enlace para más información!\nO: Únete a nuestro canal para no perderte nada.")
        self.cta_edit.setFixedHeight(60)
        layout.addWidget(self.cta_edit)

    def get_call_to_action(self):
        return self.cta_edit.toPlainText().strip()