from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QGroupBox, QPushButton, QHBoxLayout

class CallToActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Grupo para CTA
        group = QGroupBox("🎯 Llamada a la Acción")
        group_layout = QVBoxLayout()

        self.cta_edit = QTextEdit()
        self.cta_edit.setPlaceholderText("Ejemplo: ¡Únete a nuestro canal premium!\nO: Comenta tu opinión abajo 👇")
        self.cta_edit.setMaximumHeight(80)
        group_layout.addWidget(self.cta_edit)

        # Botones de CTA predefinidos
        quick_cta_layout = QHBoxLayout()
        
        cta_options = [
            "💬 ¡Comenta tu opinión!",
            "👍 Dale like si te gustó",
            "🔔 Activa las notificaciones",
            "📢 Comparte con tus amigos"
        ]
        
        for cta in cta_options:
            btn = QPushButton(cta.split(' ', 1)[0])  # Solo el emoji
            btn.setMaximumWidth(40)
            btn.setToolTip(cta)
            btn.clicked.connect(lambda checked, text=cta: self.add_quick_cta(text))
            quick_cta_layout.addWidget(btn)
        
        quick_cta_layout.addStretch()
        group_layout.addLayout(quick_cta_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def add_quick_cta(self, cta_text):
        """Agregar CTA rápido"""
        current = self.cta_edit.toPlainText()
        if current and not current.endswith('\n'):
            current += '\n'
        current += cta_text
        self.cta_edit.setPlainText(current)

    def get_call_to_action(self):
        return self.cta_edit.toPlainText().strip()

    def clear_cta(self):
        """Limpiar CTA"""
        self.cta_edit.clear()