from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QHBoxLayout
from PySide6.QtCore import Qt

# Puedes mejorar la lógica de sugerencia usando una API o una base de datos de hashtags
def suggest_hashtags(text):
    # Lógica simple: palabras clave + hashtags populares
    keywords = set(word.strip("#.,!¡?¿").lower() for word in text.split() if len(word) > 3)
    base_hashtags = {
        "psicologia": ["#psicologia", "#mente", "#bienestar"],
        "salud": ["#salud", "#bienestar", "#vida"],
        "motivacion": ["#motivacion", "#inspiracion", "#exito"],
        "deporte": ["#deporte", "#fitness", "#salud"],
        "dinero": ["#dinero", "#finanzas", "#emprendimiento"],
        "amor": ["#amor", "#relaciones", "#pareja"],
        "tecnologia": ["#tecnologia", "#innovacion", "#futuro"],
        "negocios": ["#negocios", "#empresa", "#emprender"],
        "educacion": ["#educacion", "#aprendizaje", "#escuela"],
        "marketing": ["#marketing", "#publicidad", "#ventas"],
    }
    hashtags = set()
    for k, tags in base_hashtags.items():
        if k in keywords:
            hashtags.update(tags)
    # Si no hay sugerencias, usa palabras clave como hashtags
    if not hashtags:
        hashtags = {"#" + k for k in list(keywords)[:5]}
    return sorted(hashtags)

class HashtagSuggesterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Hashtags sugeridos")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Palabras clave del post (se actualiza automáticamente)")
        layout.addWidget(self.input_edit)

        btn_row = QHBoxLayout()
        self.suggest_btn = QPushButton("Sugerir hashtags")
        self.suggest_btn.clicked.connect(self.suggest)
        btn_row.addWidget(self.suggest_btn)
        layout.addLayout(btn_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.input_edit.textChanged.connect(self.suggest)

    def suggest(self):
        text = self.input_edit.text()
        hashtags = suggest_hashtags(text)
        self.list_widget.clear()
        for tag in hashtags:
            self.list_widget.addItem(tag)

    def get_hashtags(self):
        return " ".join(self.list_widget.item(i).text() for i in range(self.list_widget.count()))