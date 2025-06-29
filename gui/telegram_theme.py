"""
Unified Theme System for Telegram AI Publisher
Provides consistent styling across all tabs and components
"""

from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

# Theme Colors
TELEGRAM_PRIMARY = "#2AABEE"
TELEGRAM_ACCENT = "#39B3F5"
TELEGRAM_DARK = "#000000"
TELEGRAM_CARD = "#23272b"
TELEGRAM_TEXT = "#FFFFFF"
TELEGRAM_TEXT_SECONDARY = "#B0B3B8"
TELEGRAM_SUCCESS = "#4CAF50"
TELEGRAM_WARNING = "#FF9800"
TELEGRAM_ERROR = "#F44336"
TELEGRAM_INFO = "#2196F3"

class TelegramTheme:
    """Unified theme manager for the application"""
    
    @staticmethod
    def apply_application_theme(app):
        """Apply the main application theme"""
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
        
        app.setStyleSheet(TelegramTheme.get_application_stylesheet())
    
    @staticmethod
    def get_application_stylesheet():
        """Get the main application stylesheet"""
        return f"""
            QMainWindow {{
                background-color: {TELEGRAM_DARK};
                color: {TELEGRAM_TEXT};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {TELEGRAM_CARD};
                background-color: {TELEGRAM_DARK};
            }}
            
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            
            QTabBar::tab {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            
            QTabBar::tab:hover {{
                background-color: {TELEGRAM_ACCENT};
                color: white;
            }}
        """
    
    @staticmethod
    def get_widget_stylesheet():
        """Get stylesheet for general widgets"""
        return f"""
            QWidget {{
                background-color: {TELEGRAM_DARK};
                color: {TELEGRAM_TEXT};
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {TELEGRAM_CARD};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: {TELEGRAM_DARK};
                color: {TELEGRAM_TEXT};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {TELEGRAM_PRIMARY};
            }}
            
            QLabel {{
                color: {TELEGRAM_TEXT};
                background-color: transparent;
            }}
            
            QLineEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QTextEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            
            QTextEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QPlainTextEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            
            QPlainTextEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QComboBox {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
                min-width: 150px;
            }}
            
            QComboBox:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {TELEGRAM_TEXT};
                margin-right: 5px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
                color: {TELEGRAM_TEXT};
            }}
            
            QCheckBox {{
                color: {TELEGRAM_TEXT};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {TELEGRAM_ACCENT};
                border-radius: 4px;
                background-color: {TELEGRAM_CARD};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {TELEGRAM_PRIMARY};
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QCheckBox::indicator:checked::after {{
                content: "✓";
                color: white;
                font-weight: bold;
            }}
            
            QSpinBox, QDoubleSpinBox {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            
            QSlider::groove:horizontal {{
                border: 1px solid {TELEGRAM_ACCENT};
                height: 8px;
                background: {TELEGRAM_CARD};
                margin: 2px 0;
                border-radius: 4px;
            }}
            
            QSlider::handle:horizontal {{
                background: {TELEGRAM_PRIMARY};
                border: 1px solid {TELEGRAM_ACCENT};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {TELEGRAM_ACCENT};
            }}
            
            QSlider::sub-page:horizontal {{
                background: {TELEGRAM_PRIMARY};
                border: 1px solid {TELEGRAM_ACCENT};
                height: 8px;
                border-radius: 4px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {TELEGRAM_ACCENT};
                background-color: {TELEGRAM_DARK};
                border-radius: 6px;
            }}
            
            QTabBar::tab {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid {TELEGRAM_ACCENT};
            }}
            
            QTabBar::tab:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
                border-bottom: 1px solid {TELEGRAM_PRIMARY};
            }}
            
            QTabBar::tab:hover {{
                background-color: {TELEGRAM_ACCENT};
                color: white;
            }}
            
            QListWidget {{
                background-color: {TELEGRAM_DARK};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                color: {TELEGRAM_TEXT};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {TELEGRAM_CARD};
            }}
            
            QListWidget::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            
            QListWidget::item:hover {{
                background-color: {TELEGRAM_CARD};
            }}
        """
    
    @staticmethod
    def get_button_stylesheet():
        """Get stylesheet for buttons"""
        return f"""
            QPushButton {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                margin: 2px;
                min-height: 20px;
            }}
            
            QPushButton:hover {{
                background-color: {TELEGRAM_ACCENT};
                color: white;
                border: 1px solid {TELEGRAM_PRIMARY};
            }}
            
            QPushButton:pressed {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            
            QPushButton:disabled {{
                background-color: #444;
                color: #888;
                border: 1px solid #555;
            }}
            
            /* Primary buttons */
            QPushButton.primary {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
                border: 1px solid {TELEGRAM_PRIMARY};
            }}
            
            QPushButton.primary:hover {{
                background-color: {TELEGRAM_ACCENT};
                border: 1px solid {TELEGRAM_ACCENT};
            }}
            
            /* Success buttons */
            QPushButton.success {{
                background-color: {TELEGRAM_SUCCESS};
                color: white;
                border: 1px solid {TELEGRAM_SUCCESS};
            }}
            
            QPushButton.success:hover {{
                background-color: #45A049;
                border: 1px solid #45A049;
            }}
            
            /* Warning buttons */
            QPushButton.warning {{
                background-color: {TELEGRAM_WARNING};
                color: white;
                border: 1px solid {TELEGRAM_WARNING};
            }}
            
            QPushButton.warning:hover {{
                background-color: #F57C00;
                border: 1px solid #F57C00;
            }}
            
            /* Error/Danger buttons */
            QPushButton.danger {{
                background-color: {TELEGRAM_ERROR};
                color: white;
                border: 1px solid {TELEGRAM_ERROR};
            }}
            
            QPushButton.danger:hover {{
                background-color: #D32F2F;
                border: 1px solid #D32F2F;
            }}
            
            /* Emoji buttons - special exception */
            QPushButton.emoji-btn {{
                background: none;
                color: none;
                font-weight: normal;
                margin: 0;
                padding: 4px;
                border: none;
                border-radius: 6px;
                min-height: 16px;
            }}
            
            QPushButton.emoji-btn:hover {{
                background-color: {TELEGRAM_CARD};
            }}
        """
    
    @staticmethod
    def get_table_stylesheet():
        """Get stylesheet for tables"""
        return f"""
            QTableWidget {{
                background-color: {TELEGRAM_DARK};
                alternate-background-color: {TELEGRAM_CARD};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
                color: {TELEGRAM_TEXT};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                gridline-color: {TELEGRAM_CARD};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {TELEGRAM_CARD};
            }}
            
            QTableWidget::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {TELEGRAM_PRIMARY};
                font-weight: bold;
            }}
            
            QScrollBar:vertical {{
                background-color: {TELEGRAM_CARD};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {TELEGRAM_ACCENT};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {TELEGRAM_PRIMARY};
            }}
            
            QScrollBar:horizontal {{
                background-color: {TELEGRAM_CARD};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {TELEGRAM_ACCENT};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {TELEGRAM_PRIMARY};
            }}
        """
    
    @staticmethod
    def get_progress_bar_stylesheet():
        """Get stylesheet for progress bars"""
        return f"""
            QProgressBar {{
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                text-align: center;
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                font-weight: bold;
            }}
            
            QProgressBar::chunk {{
                background-color: {TELEGRAM_PRIMARY};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def get_header_label_style():
        """Get style for header labels"""
        return f"font-size: 18px; font-weight: bold; color: {TELEGRAM_PRIMARY}; margin: 10px;"
    
    @staticmethod
    def get_subheader_label_style():
        """Get style for subheader labels"""
        return f"font-size: 14px; font-weight: bold; color: {TELEGRAM_ACCENT}; margin: 8px;"
    
    @staticmethod
    def get_description_label_style():
        """Get style for description labels"""
        return f"color: {TELEGRAM_TEXT_SECONDARY}; margin: 5px 10px;"
    
    @staticmethod
    def get_success_label_style():
        """Get style for success labels"""
        return f"color: {TELEGRAM_SUCCESS}; font-weight: bold;"
    
    @staticmethod
    def get_warning_label_style():
        """Get style for warning labels"""
        return f"color: {TELEGRAM_WARNING}; font-weight: bold;"
    
    @staticmethod
    def get_error_label_style():
        """Get style for error labels"""
        return f"color: {TELEGRAM_ERROR}; font-weight: bold;"
    
    @staticmethod
    def apply_theme_to_widget(widget):
        """Apply complete theme to any widget"""
        stylesheet = (
            TelegramTheme.get_widget_stylesheet() +
            TelegramTheme.get_button_stylesheet() +
            TelegramTheme.get_table_stylesheet() +
            TelegramTheme.get_progress_bar_stylesheet()
        )
        widget.setStyleSheet(stylesheet)
    
    @staticmethod
    def set_button_style(button, style_type="default"):
        """Set specific style for a button"""
        if style_type == "primary":
            button.setProperty("class", "primary")
        elif style_type == "success":
            button.setProperty("class", "success")
        elif style_type == "warning":
            button.setProperty("class", "warning")
        elif style_type == "danger":
            button.setProperty("class", "danger")
        elif style_type == "emoji":
            button.setProperty("class", "emoji-btn")
        
        # Force style refresh
        button.style().unpolish(button)
        button.style().polish(button)
    
    @staticmethod
    def apply_scroll_area_theme(scroll_area):
        """Apply scroll area theme"""
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {TELEGRAM_DARK};
            }}
            QScrollBar:vertical {{
                background-color: {TELEGRAM_CARD};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {TELEGRAM_ACCENT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {TELEGRAM_PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
    
    @staticmethod
    def apply_widget_theme(widget):
        """Apply general widget theme"""
        widget.setStyleSheet(TelegramTheme.get_widget_stylesheet())
    
    @staticmethod
    def apply_button_theme(button, style="primary"):
        """Apply button theme"""
        if style == "primary":
            button.setStyleSheet(TelegramTheme.get_button_stylesheet())
        elif style == "secondary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {TELEGRAM_CARD};
                    color: {TELEGRAM_TEXT};
                    border: 1px solid {TELEGRAM_TEXT_SECONDARY};
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {TELEGRAM_TEXT_SECONDARY};
                    color: {TELEGRAM_DARK};
                }}
                QPushButton:pressed {{
                    background-color: {TELEGRAM_PRIMARY};
                    color: white;
                }}
            """)
    
    @staticmethod
    def apply_label_theme(label, style="primary"):
        """Apply label theme"""
        if style == "primary":
            label.setStyleSheet(f"""
                QLabel {{
                    color: {TELEGRAM_TEXT};
                    font-weight: bold;
                }}
            """)
        elif style == "secondary":
            label.setStyleSheet(f"""
                QLabel {{
                    color: {TELEGRAM_TEXT_SECONDARY};
                }}
            """)
        elif style == "title":
            label.setStyleSheet(f"""
                QLabel {{
                    color: {TELEGRAM_TEXT};
                    font-size: 18px;
                    font-weight: bold;
                }}
            """)
    
    @staticmethod
    def apply_table_theme(table):
        """Apply table theme"""
        table.setStyleSheet(TelegramTheme.get_table_stylesheet())
    
    @staticmethod
    def apply_card_theme(card):
        """Apply card theme to QFrame or QGroupBox"""
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_TEXT_SECONDARY};
                border-radius: 8px;
                padding: 10px;
            }}
            QGroupBox {{
                background-color: {TELEGRAM_CARD};
                border: 2px solid {TELEGRAM_TEXT_SECONDARY};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                color: {TELEGRAM_TEXT};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {TELEGRAM_TEXT};
            }}
        """)
    
    @staticmethod
    def apply_dialog_theme(dialog):
        """Apply dialog theme"""
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {TELEGRAM_DARK};
                color: {TELEGRAM_TEXT};
            }}
        """)
    
    @staticmethod
    def apply_input_theme(input_widget):
        """Apply input theme for QLineEdit and QTextEdit"""
        input_widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            QTextEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            QTextEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            QPlainTextEdit {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            QPlainTextEdit:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
        """)
    
    @staticmethod
    def apply_combobox_theme(combobox):
        """Apply combobox theme"""
        combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
                min-width: 150px;
            }}
            QComboBox:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {TELEGRAM_TEXT};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
                color: {TELEGRAM_TEXT};
            }}
        """)
    
    @staticmethod
    def apply_spinbox_theme(spinbox):
        """Apply spinbox theme"""
        spinbox.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                padding: 8px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
        """)
    
    @staticmethod
    def apply_checkbox_theme(checkbox):
        """Apply checkbox theme"""
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {TELEGRAM_TEXT};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {TELEGRAM_ACCENT};
                border-radius: 4px;
                background-color: {TELEGRAM_CARD};
            }}
            QCheckBox::indicator:checked {{
                background-color: {TELEGRAM_PRIMARY};
                border: 2px solid {TELEGRAM_PRIMARY};
            }}
        """)
    
    @staticmethod
    def apply_slider_theme(slider):
        """Apply slider theme"""
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {TELEGRAM_ACCENT};
                height: 8px;
                background: {TELEGRAM_CARD};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {TELEGRAM_PRIMARY};
                border: 1px solid {TELEGRAM_ACCENT};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {TELEGRAM_ACCENT};
            }}
            QSlider::sub-page:horizontal {{
                background: {TELEGRAM_PRIMARY};
                border: 1px solid {TELEGRAM_ACCENT};
                height: 8px;
                border-radius: 4px;
            }}
        """)
    
    @staticmethod
    def apply_tab_widget_theme(tab_widget):
        """Apply tab widget theme"""
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {TELEGRAM_ACCENT};
                background-color: {TELEGRAM_DARK};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid {TELEGRAM_ACCENT};
            }}
            QTabBar::tab:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
                border-bottom: 1px solid {TELEGRAM_PRIMARY};
            }}
            QTabBar::tab:hover {{
                background-color: {TELEGRAM_ACCENT};
                color: white;
            }}
        """)
    
    @staticmethod
    def apply_list_widget_theme(list_widget):
        """Apply list widget theme"""
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {TELEGRAM_DARK};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                color: {TELEGRAM_TEXT};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {TELEGRAM_CARD};
            }}
            QListWidget::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {TELEGRAM_CARD};
            }}
        """)
    
    @staticmethod
    def apply_list_theme(list_widget):
        """Apply list theme - alias for apply_list_widget_theme"""
        TelegramTheme.apply_list_widget_theme(list_widget)
    
    @staticmethod
    def apply_tree_widget_theme(tree_widget):
        """Apply tree widget theme"""
        tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {TELEGRAM_DARK};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                color: {TELEGRAM_TEXT};
                selection-background-color: {TELEGRAM_PRIMARY};
                selection-color: white;
            }}
            QTreeWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {TELEGRAM_CARD};
            }}
            QTreeWidget::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            QTreeWidget::item:hover {{
                background-color: {TELEGRAM_CARD};
            }}
        """)
    
    @staticmethod
    def apply_text_browser_theme(text_browser):
        """Apply text browser theme"""
        text_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 6px;
                color: {TELEGRAM_TEXT};
                font-size: 14px;
                padding: 8px;
            }}
        """)
    
    @staticmethod
    def apply_frame_theme(frame):
        """Apply frame theme"""
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_TEXT_SECONDARY};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
    
    @staticmethod
    def apply_groupbox_theme(groupbox):
        """Apply groupbox theme"""
        groupbox.setStyleSheet(f"""
            QGroupBox {{
                background-color: {TELEGRAM_CARD};
                border: 2px solid {TELEGRAM_TEXT_SECONDARY};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                color: {TELEGRAM_TEXT};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {TELEGRAM_TEXT};
            }}
        """)
    
    @staticmethod
    def apply_status_bar_theme(status_bar):
        """Apply status bar theme"""
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                border-top: 1px solid {TELEGRAM_ACCENT};
            }}
        """)
    
    @staticmethod
    def apply_menu_bar_theme(menu_bar):
        """Apply menu bar theme"""
        menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                border-bottom: 1px solid {TELEGRAM_ACCENT};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 8px 16px;
            }}
            QMenuBar::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
            QMenu {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                border: 1px solid {TELEGRAM_ACCENT};
            }}
            QMenu::item {{
                padding: 8px 16px;
            }}
            QMenu::item:selected {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
        """)
    
    @staticmethod
    def apply_toolbar_theme(toolbar):
        """Apply toolbar theme"""
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {TELEGRAM_CARD};
                border: 1px solid {TELEGRAM_ACCENT};
                spacing: 4px;
            }}
            QToolButton {{
                background-color: {TELEGRAM_CARD};
                color: {TELEGRAM_TEXT};
                border: 1px solid {TELEGRAM_ACCENT};
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
            }}
            QToolButton:hover {{
                background-color: {TELEGRAM_ACCENT};
                color: white;
            }}
            QToolButton:pressed {{
                background-color: {TELEGRAM_PRIMARY};
                color: white;
            }}
        """)

# Additional utility functions for quick theme application
def apply_telegram_compact_theme(app):
    """Apply the complete Telegram theme to the application"""
    TelegramTheme.apply_application_theme(app)

def apply_widget_styles(widget):
    """Apply all widget styles to a widget"""
    TelegramTheme.apply_theme_to_widget(widget)