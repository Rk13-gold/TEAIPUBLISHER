"""
Estilos modernos y responsivos para Telegram AI Publisher
Sistema de diseño viral y persuasivo
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor
from PySide6.QtWidgets import QApplication

class ModernStyles:
    # Colores del tema viral moderno
    COLORS = {
        'primary': '#1DA1F2',           # Azul Twitter
        'secondary': '#14171A',         # Negro profundo
        'accent': '#1991DA',            # Azul accent
        'success': '#17BF63',           # Verde éxito
        'warning': '#FFAD1F',           # Naranja advertencia
        'danger': '#E0245E',            # Rojo peligro
        'purple': '#794BC4',            # Morado viral
        'gradient_start': '#667eea',     # Gradiente inicio
        'gradient_end': '#764ba2',       # Gradiente fin
        'background_dark': '#15202B',    # Fondo oscuro
        'background_light': '#192734',   # Fondo claro
        'card_bg': '#1E2732',           # Fondo de tarjetas
        'text_primary': '#FFFFFF',       # Texto principal
        'text_secondary': '#8899A6',     # Texto secundario
        'border': '#38444D',            # Bordes
        'hover': '#1B2836',             # Hover
        'glass': 'rgba(255,255,255,0.1)' # Efecto cristal
    }
    
    # Fuentes responsivas
    @staticmethod
    def get_font_sizes():
        """Obtener tamaños de fuente adaptables"""
        return {
            'title': 24,
            'subtitle': 18,
            'body': 14,
            'caption': 12,
            'button': 14,
            'emoji': 20
        }
    
    @staticmethod
    def get_main_window_style():
        """Estilo principal de la ventana"""
        return f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {ModernStyles.COLORS['background_dark']},
                stop:1 {ModernStyles.COLORS['background_light']});
            color: {ModernStyles.COLORS['text_primary']};
        }}
        
        QWidget {{
            background-color: transparent;
            color: {ModernStyles.COLORS['text_primary']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        """
    
    @staticmethod
    def get_group_box_style():
        """Estilo para GroupBox con efecto de cristal"""
        return f"""
        QGroupBox {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255,255,255,0.15),
                stop:1 rgba(255,255,255,0.05));
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 15px;
            margin-top: 10px;
            padding-top: 15px;
            color: {ModernStyles.COLORS['text_primary']};
            font-weight: bold;
            font-size: 14px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            top: 5px;
            color: {ModernStyles.COLORS['primary']};
            font-weight: bold;
            font-size: 15px;
        }}
        
        QGroupBox:hover {{
            border-color: {ModernStyles.COLORS['primary']};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(25,145,218,0.2),
                stop:1 rgba(25,145,218,0.1));
        }}
        """
    
    @staticmethod
    def get_button_style():
        """Botones modernos con efectos visuales"""
        return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['accent']});
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 12px 20px;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {ModernStyles.COLORS['accent']},
                stop:1 {ModernStyles.COLORS['primary']});
            transform: scale(1.05);
        }}
        
        QPushButton:pressed {{
            background: {ModernStyles.COLORS['secondary']};
            transform: scale(0.98);
        }}
        
        QPushButton:disabled {{
            background: {ModernStyles.COLORS['border']};
            color: {ModernStyles.COLORS['text_secondary']};
        }}
        
        /* Botón principal de publicar */
        QPushButton#publish_button {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {ModernStyles.COLORS['success']},
                stop:1 {ModernStyles.COLORS['primary']});
            font-size: 16px;
            font-weight: bold;
            padding: 15px 30px;
            min-height: 25px;
            border-radius: 15px;
        }}
        
        QPushButton#publish_button:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1ED760,
                stop:1 {ModernStyles.COLORS['success']});
            box-shadow: 0 5px 15px rgba(23,191,99,0.4);
        }}
        
        /* Botones de emoji */
        QPushButton#emoji_button {{
            background: transparent;
            border: 2px solid {ModernStyles.COLORS['border']};
            border-radius: 20px;
            font-size: 20px;
            padding: 8px;
            min-width: 40px;
            max-width: 40px;
            min-height: 40px;
            max-height: 40px;
        }}
        
        QPushButton#emoji_button:hover {{
            background: {ModernStyles.COLORS['primary']};
            border-color: {ModernStyles.COLORS['primary']};
            transform: rotate(10deg) scale(1.1);
        }}
        """
    
    @staticmethod
    def get_input_style():
        """Estilos para campos de entrada"""
        return f"""
        QLineEdit, QTextEdit {{
            background: {ModernStyles.COLORS['card_bg']};
            border: 2px solid {ModernStyles.COLORS['border']};
            border-radius: 10px;
            padding: 12px 15px;
            color: {ModernStyles.COLORS['text_primary']};
            font-size: 14px;
            selection-background-color: {ModernStyles.COLORS['primary']};
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {ModernStyles.COLORS['primary']};
            background: {ModernStyles.COLORS['background_light']};
            box-shadow: 0 0 10px rgba(29,161,242,0.3);
        }}
        
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {ModernStyles.COLORS['text_secondary']};
            font-style: italic;
        }}
        
        /* Campo de título especial */
        QLineEdit#title_edit {{
            font-size: 16px;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernStyles.COLORS['card_bg']},
                stop:1 rgba(121,75,196,0.1));
            border: 2px solid {ModernStyles.COLORS['purple']};
        }}
        """
    
    @staticmethod
    def get_list_style():
        """Estilos para listas y widgets de selección"""
        return f"""
        QListWidget {{
            background: {ModernStyles.COLORS['card_bg']};
            border: 1px solid {ModernStyles.COLORS['border']};
            border-radius: 10px;
            padding: 5px;
            color: {ModernStyles.COLORS['text_primary']};
            alternate-background-color: {ModernStyles.COLORS['hover']};
        }}
        
        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['purple']});
            color: white;
        }}
        
        QListWidget::item:hover {{
            background: {ModernStyles.COLORS['hover']};
        }}
        
        QComboBox {{
            background: {ModernStyles.COLORS['card_bg']};
            border: 2px solid {ModernStyles.COLORS['border']};
            border-radius: 8px;
            padding: 8px 12px;
            color: {ModernStyles.COLORS['text_primary']};
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {ModernStyles.COLORS['primary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {ModernStyles.COLORS['text_primary']};
        }}
        """
    
    @staticmethod
    def get_progress_style():
        """Estilos para barras de progreso y logs"""
        return f"""
        QProgressBar {{
            background: {ModernStyles.COLORS['card_bg']};
            border: 2px solid {ModernStyles.COLORS['border']};
            border-radius: 10px;
            text-align: center;
            color: {ModernStyles.COLORS['text_primary']};
            font-weight: bold;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernStyles.COLORS['success']},
                stop:0.5 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['purple']});
            border-radius: 8px;
        }}
        
        /* Log de progreso */
        QTextEdit#progress_log {{
            background: {ModernStyles.COLORS['secondary']};
            border: 2px solid {ModernStyles.COLORS['success']};
            border-radius: 10px;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            color: {ModernStyles.COLORS['success']};
        }}
        """
    
    @staticmethod
    def get_tab_style():
        """Estilos para pestañas"""
        return f"""
        QTabWidget::pane {{
            background: transparent;
            border: none;
        }}
        
        QTabBar::tab {{
            background: {ModernStyles.COLORS['card_bg']};
            border: 2px solid {ModernStyles.COLORS['border']};
            border-bottom: none;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            padding: 12px 20px;
            margin-right: 5px;
            color: {ModernStyles.COLORS['text_secondary']};
            font-weight: bold;
        }}
        
        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['accent']});
            color: white;
            border-color: {ModernStyles.COLORS['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background: {ModernStyles.COLORS['hover']};
            border-color: {ModernStyles.COLORS['primary']};
        }}
        """
    
    @staticmethod
    def get_label_style():
        """Estilos para etiquetas"""
        return f"""
        QLabel {{
            color: {ModernStyles.COLORS['text_primary']};
            font-size: 14px;
        }}
        
        QLabel#title_label {{
            color: {ModernStyles.COLORS['primary']};
            font-size: 18px;
            font-weight: bold;
        }}
        
        QLabel#subtitle_label {{
            color: {ModernStyles.COLORS['purple']};
            font-size: 16px;
            font-weight: bold;
        }}
        
        QLabel#hashtags_display {{
            color: {ModernStyles.COLORS['primary']};
            font-size: 12px;
            font-weight: bold;
            background: rgba(29,161,242,0.1);
            border-radius: 5px;
            padding: 5px 10px;
        }}
        """
    
    @staticmethod
    def get_scroll_style():
        """Estilos para barras de desplazamiento"""
        return f"""
        QScrollBar:vertical {{
            background: {ModernStyles.COLORS['card_bg']};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['purple']});
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {ModernStyles.COLORS['accent']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background: {ModernStyles.COLORS['card_bg']};
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ModernStyles.COLORS['primary']},
                stop:1 {ModernStyles.COLORS['purple']});
            border-radius: 6px;
            min-width: 20px;
        }}
        """
    
    @staticmethod
    def get_complete_stylesheet():
        """Obtener hoja de estilos completa"""
        return (
            ModernStyles.get_main_window_style() +
            ModernStyles.get_group_box_style() +
            ModernStyles.get_button_style() +
            ModernStyles.get_input_style() +
            ModernStyles.get_list_style() +
            ModernStyles.get_progress_style() +
            ModernStyles.get_tab_style() +
            ModernStyles.get_label_style() +
            ModernStyles.get_scroll_style()
        )
    
    @staticmethod
    def apply_responsive_sizing(widget, base_width=1200, base_height=800):
        """Aplicar dimensionado responsivo"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Calcular factores de escala
        width_factor = min(screen_width * 0.9, base_width * 1.2) / base_width
        height_factor = min(screen_height * 0.9, base_height * 1.2) / base_height
        
        # Aplicar dimensiones responsivas
        new_width = int(base_width * width_factor)
        new_height = int(base_height * height_factor)
        
        widget.resize(new_width, new_height)
        
        # Centrar en pantalla
        center_x = (screen_width - new_width) // 2
        center_y = (screen_height - new_height) // 2
        widget.move(center_x, center_y)
        
        return width_factor, height_factor
    
    @staticmethod
    def setup_viral_animations(widget):
        """Configurar animaciones virales para widgets"""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        from PySide6.QtGui import QGraphicsOpacityEffect
        
        # Efecto de opacidad
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        
        # Animación de aparición
        widget.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        widget.fade_animation.setDuration(500)
        widget.fade_animation.setStartValue(0.0)
        widget.fade_animation.setEndValue(1.0)
        widget.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        return widget.fade_animation
