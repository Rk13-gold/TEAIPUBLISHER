from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QHBoxLayout, QGroupBox, QTextEdit
from PySide6.QtCore import Qt

# Sugerencia de hashtags mejorada
def suggest_hashtags(text):
    keywords = set(word.strip("#.,!¡?¿()[]{}").lower() for word in text.split() if len(word) > 3)
    base_hashtags = {
        "psicologia": ["#psicologia", "#mente", "#bienestar", "#mentalidad"],
        "salud": ["#salud", "#bienestar", "#vida", "#wellness"],
        "motivacion": ["#motivacion", "#inspiracion", "#exito", "#goals"],
        "deporte": ["#deporte", "#fitness", "#salud", "#gym"],
        "dinero": ["#dinero", "#finanzas", "#emprendimiento", "#riqueza"],
        "amor": ["#amor", "#relaciones", "#pareja", "#corazon"],
        "tecnologia": ["#tecnologia", "#innovacion", "#futuro", "#tech"],
        "negocios": ["#negocios", "#empresa", "#emprender", "#business"],
        "educacion": ["#educacion", "#aprendizaje", "#conocimiento", "#learning"],
        "marketing": ["#marketing", "#publicidad", "#ventas", "#branding"],
        "lifestyle": ["#lifestyle", "#vida", "#personal", "#daily"],
        "espiritual": ["#espiritual", "#crecimiento", "#mindfulness", "#zen"],
        "trabajo": ["#trabajo", "#carrera", "#profesional", "#empleo"],
        "familia": ["#familia", "#hijos", "#padres", "#hogar"],
        "viajes": ["#viajes", "#turismo", "#aventura", "#travel"],
        "comida": ["#comida", "#cocina", "#recetas", "#food"],
        "arte": ["#arte", "#creatividad", "#diseño", "#artista"],
        "musica": ["#musica", "#audio", "#melodia", "#ritmo"],
        "podcast": ["#podcast", "#audio", "#contenido", "#voicenote"],
        "premium": ["#premium", "#exclusivo", "#vip", "#elite"]
    }
    
    hashtags = set()
    for k, tags in base_hashtags.items():
        if any(keyword in k or k in keyword for keyword in keywords):
            hashtags.update(tags[:3])  # Máximo 3 por categoría
    
    # Hashtags generales populares
    general_tags = ["#viral", "#trending", "#follow", "#like", "#share", "#motivation", "#success", "#life"]
    hashtags.update(general_tags[:2])
    
    # Si no hay sugerencias específicas, crear de palabras clave
    if len(hashtags) < 5:
        for keyword in list(keywords)[:3]:
            if len(keyword) > 3:
                hashtags.add(f"#{keyword}")
    
    return sorted(list(hashtags)[:8])  # Máximo 8 hashtags

class HashtagSuggesterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Grupo para hashtags
        group = QGroupBox("📍 Hashtags")
        group_layout = QVBoxLayout()

        # Campo de entrada para hashtags manuales
        self.hashtags_edit = QTextEdit()
        self.hashtags_edit.setPlaceholderText("Escribe hashtags o palabras clave...")
        self.hashtags_edit.setMaximumHeight(60)
        group_layout.addWidget(self.hashtags_edit)

        # Botón para sugerir
        suggest_btn = QPushButton("🎯 Sugerir Hashtags")
        suggest_btn.clicked.connect(self.suggest_from_content)
        group_layout.addWidget(suggest_btn)

        # Lista de hashtags sugeridos
        self.suggested_list = QListWidget()
        self.suggested_list.setMaximumHeight(80)
        self.suggested_list.itemDoubleClicked.connect(self.add_hashtag_to_text)
        group_layout.addWidget(self.suggested_list)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def suggest_from_content(self):
        """Sugerir hashtags basado en el contenido del post"""
        parent_widget = self.parent()
        content = ""
        
        # Intentar obtener contenido del post principal
        if hasattr(parent_widget, 'title_edit'):
            content += parent_widget.title_edit.text() + " "
        if hasattr(parent_widget, 'edit_area'):
            content += parent_widget.edit_area.toPlainText() + " "
        
        # Si no hay contenido, usar el texto del campo de hashtags
        if not content.strip():
            content = self.hashtags_edit.toPlainText()
        
        hashtags = suggest_hashtags(content)
        self.suggested_list.clear()
        for tag in hashtags:
            self.suggested_list.addItem(tag)

    def add_hashtag_to_text(self, item):
        """Agregar hashtag al campo de texto"""
        hashtag = item.text()
        current_text = self.hashtags_edit.toPlainText()
        if hashtag not in current_text:
            if current_text and not current_text.endswith(" "):
                current_text += " "
            current_text += hashtag
            self.hashtags_edit.setPlainText(current_text)

    def get_hashtags(self):
        """Obtener hashtags como string"""
        return self.hashtags_edit.toPlainText().strip()

    def clear_hashtags(self):
        """Limpiar hashtags"""
        self.hashtags_edit.clear()
        self.suggested_list.clear()