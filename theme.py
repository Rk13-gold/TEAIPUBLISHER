TELEGRAM_PRIMARY = "#2AABEE"
TELEGRAM_ACCENT = "#39B3F5"
TELEGRAM_DARK = "#000000"
TELEGRAM_CARD = "#000000"
TELEGRAM_TEXT = "#FFFFFF"

def apply_telegram_compact_theme(app):
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(0, 0, 0))  # Fondo negro puro
    palette.setColor(QPalette.WindowText, QColor(245, 247, 250))
    palette.setColor(QPalette.Base, QColor(0, 0, 0))
    palette.setColor(QPalette.AlternateBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipBase, QColor(245, 247, 250))
    palette.setColor(QPalette.ToolTipText, QColor(245, 247, 250))
    palette.setColor(QPalette.Text, QColor(245, 247, 250))
    palette.setColor(QPalette.Button, QColor(42, 171, 238))
    palette.setColor(QPalette.ButtonText, QColor("white"))
    palette.setColor(QPalette.Highlight, QColor(57, 179, 245))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(palette)
    app.setStyleSheet("""
        QPushButton {
            background: #23272b;
            color: #fff;
            border-radius: 6px;
            padding: 6px 18px;
            font-weight: bold;
            margin: 2px;
        }
        QPushButton:hover {
            background: #39B3F5;
        }
        /* EXCEPCIÓN: los botones de emoji no deben forzar color ni fondo */
        QPushButton.emoji-btn {
            background: none;
            color: none;
            font-weight: normal;
            margin: 0;
            padding: 0;
            border-radius: 6px;
        }
        QPushButton.emoji-btn:hover {
            background: #23272b;
        }
    """)