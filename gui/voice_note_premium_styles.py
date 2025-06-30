"""
Estilos modernos y responsivos para la pestaña de contenido premium
Diseñado para crear una experiencia viral y persuasiva
Compatible con diferentes resoluciones y dispositivos
"""

class VoiceNotePremiumStyles:
    
    @staticmethod
    def get_main_styles():
        """Estilos principales optimizados para rendimiento"""
        return """
        /* Base Widget Styles */
        QWidget {
            background-color: #1a1a2e;
            color: #ffffff;
            font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
            font-size: 12px;
            border: none;
        }
        
        /* Premium Header Styles */
        QFrame#premium_header {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #16213e, stop:0.5 #1a1a2e, stop:1 #16213e);
            border: 2px solid #ffd700;
            border-radius: 15px;
            padding: 15px;
            margin: 10px;
            min-height: 80px;
        }
        
        QLabel#premium_title {
            font-size: 20px;
            font-weight: bold;
            color: #ffd700;
            text-align: center;
            background: transparent;
        }
        
        QLabel#channel_info {
            font-size: 13px;
            color: #e6e6fa;
            background: transparent;
            padding: 5px;
        }
        
        /* Modern Tab Styles */
        QTabWidget::pane {
            border: 2px solid #4a4a7c;
            border-radius: 10px;
            background-color: #16213e;
            margin-top: 5px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2d2d5f, stop:1 #1a1a2e);
            color: #ffffff;
            padding: 12px 20px;
            margin-right: 3px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-weight: bold;
            font-size: 13px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffd700, stop:1 #ffb347);
            color: #1a1a2e;
            font-weight: bold;
        }
        
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a4a7c, stop:1 #2d2d5f);
        }
        
        /* Modern Group Box Styles */
        QGroupBox {
            font-size: 14px;
            font-weight: bold;
            color: #ffd700;
            border: 2px solid #4a4a7c;
            border-radius: 12px;
            margin: 15px 5px;
            padding-top: 20px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(26,26,46,0.8), stop:1 rgba(22,33,62,0.8));
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            padding: 5px 12px;
            background-color: #1a1a2e;
            border: 1px solid #ffd700;
            border-radius: 8px;
            color: #ffd700;
        }
        
        /* Premium Button Styles */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4a4a7c, stop:0.5 #6a5acd, stop:1 #4a4a7c);
            color: #ffffff;
            border: 2px solid #6a5acd;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: bold;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6a5acd, stop:0.5 #8a7dd8, stop:1 #6a5acd);
            border: 2px solid #8a7dd8;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2d2d5f, stop:0.5 #4a4a7c, stop:1 #2d2d5f);
        }
        
        QPushButton:disabled {
            background-color: #2d2d5f;
            color: #666666;
            border: 2px solid #333333;
        }
        
        /* Special Premium Upload Button */
        QPushButton#premium_upload {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6b6b, stop:0.3 #ffd700, stop:0.7 #ffd700, stop:1 #ff6b6b);
            color: #1a1a2e;
            font-size: 14px;
            font-weight: bold;
            border: 3px solid #ffd700;
            border-radius: 15px;
            padding: 15px 25px;
            min-height: 25px;
        }
        
        QPushButton#premium_upload:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff8e8e, stop:0.3 #ffed4a, stop:0.7 #ffed4a, stop:1 #ff8e8e);
            border: 3px solid #ffed4a;
        }
        
        QPushButton#premium_upload:disabled {
            background: #2d2d5f;
            color: #666666;
            border: 3px solid #333333;
        }
        
        /* Modern Input Styles */
        QLineEdit {
            background-color: #2d2d5f;
            color: #ffffff;
            border: 2px solid #4a4a7c;
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 13px;
            min-height: 15px;
        }
        
        QLineEdit:focus {
            border: 2px solid #ffd700;
            background-color: #16213e;
        }
        
        QTextEdit {
            background-color: #2d2d5f;
            color: #ffffff;
            border: 2px solid #4a4a7c;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
            line-height: 1.4;
        }
        
        QTextEdit:focus {
            border: 2px solid #ffd700;
            background-color: #16213e;
        }
        
        /* ComboBox Modern Style */
        QComboBox {
            background-color: #2d2d5f;
            color: #ffffff;
            border: 2px solid #4a4a7c;
            border-radius: 8px;
            padding: 8px 15px;
            font-size: 13px;
            min-height: 20px;
        }
        
        QComboBox:hover {
            border: 2px solid #6a5acd;
        }
        
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #ffffff;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2d2d5f;
            color: #ffffff;
            border: 2px solid #4a4a7c;
            selection-background-color: #6a5acd;
        }
        
        /* SpinBox Styles */
        QSpinBox {
            background-color: #2d2d5f;
            color: #ffffff;
            border: 2px solid #4a4a7c;
            border-radius: 8px;
            padding: 8px 15px;
            font-size: 13px;
            min-height: 20px;
        }
        
        QSpinBox:focus {
            border: 2px solid #ffd700;
        }
        
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #4a4a7c;
            border: none;
            width: 20px;
        }
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: #6a5acd;
        }
        
        /* Label Styles */
        QLabel {
            color: #e6e6fa;
            font-size: 13px;
            background: transparent;
            padding: 5px;
        }
        
        QLabel#file_label {
            background-color: #16213e;
            border: 2px dashed #4a4a7c;
            border-radius: 8px;
            color: #ffd700;
            font-weight: bold;
            padding: 15px;
            text-align: center;
        }
        
        /* Preview Label */
        QLabel#preview {
            background-color: #16213e;
            border: 2px solid #4a4a7c;
            border-radius: 12px;
            padding: 10px;
            text-align: center;
            color: #888888;
        }
        
        /* Modern Progress Bar */
        QProgressBar {
            background-color: #2d2d5f;
            border: 2px solid #4a4a7c;
            border-radius: 8px;
            text-align: center;
            color: #ffffff;
            font-weight: bold;
            height: 25px;
            margin: 10px 5px;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ffd700, stop:1 #ffb347);
            border-radius: 6px;
        }
        
        /* Scroll Area Styles */
        QScrollArea {
            background: transparent;
            border: none;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d5f;
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a4a7c;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6a5acd;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        
        /* Frame Styles */
        QFrame#upload_zone {
            background-color: rgba(22, 33, 62, 0.5);
            border: 2px dashed #4a4a7c;
            border-radius: 10px;
            padding: 10px;
        }
        
        QFrame#preview_frame {
            background-color: rgba(22, 33, 62, 0.7);
            border: 1px solid #4a4a7c;
            border-radius: 8px;
            padding: 10px;
        }
        """

    @staticmethod
    def get_responsive_mobile_styles():
        """Estilos para dispositivos móviles/ventanas pequeñas"""
        return """
        /* Mobile/Small Screen Adaptations */
        QTabBar::tab {
            padding: 8px 12px;
            font-size: 11px;
            min-width: 80px;
        }
        
        QPushButton {
            padding: 8px 12px;
            font-size: 11px;
            min-height: 15px;
        }
        
        QPushButton#premium_upload {
            padding: 12px 20px;
            font-size: 12px;
            min-height: 20px;
        }
        
        QGroupBox {
            margin: 10px 2px;
            padding-top: 15px;
            font-size: 12px;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            padding: 6px 10px;
            font-size: 11px;
        }
        
        QLabel#premium_title {
            font-size: 16px;
        }
        
        QLabel#channel_info {
            font-size: 11px;
        }
        """
    
    @staticmethod
    def get_animation_styles():
        """Estilos para efectos y animaciones"""
        return """
        /* Animation and Effect Styles */
        QPushButton {
            transition: all 0.3s ease;
        }
        
        QPushButton:hover {
            transform: translateY(-2px);
        }
        
        QTabBar::tab:hover:!selected {
            transform: translateY(-1px);
        }
        
        QLineEdit:focus, QTextEdit:focus {
            transition: border-color 0.3s ease;
        }
        
        /* Success States */
        .success-state {
            background-color: rgba(0, 255, 136, 0.1);
            border: 2px solid #00ff88;
            color: #00ff88;
        }
        
        .error-state {
            background-color: rgba(255, 107, 107, 0.1);
            border: 2px solid #ff6b6b;
            color: #ff6b6b;
        }
        
        .warning-state {
            background-color: rgba(255, 215, 0, 0.1);
            border: 2px solid #ffd700;
            color: #ffd700;
        }
        """
