from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QLineEdit, QTextEdit
)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt
from services.telegram_metrics import get_channel_info, get_last_posts, get_enhanced_client, batch_get_channels_info
import asyncio
from services.gumroad import get_gumroad_products, get_gumroad_sales

class Dashboard(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.channel_username = getattr(config, "telegram_channel_username", "t.me/audioblaze")
        self.gumroad_token = getattr(config, "gumroad_token", "mpA3A42htA7Xu8H-oiu4VDYbIUbYGNEeullkQYQJkCU")
        self.setAutoFillBackground(True)
        self.init_ui()
        # Temporarily commented out to prevent API errors on startup
        # self.load_metrics()
        # self.load_gumroad_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(18)
        self.main_layout.setContentsMargins(16, 16, 16, 16)

        # --- Métricas principales (tarjetas) ---
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(16)
        self.card_subs = self.metric_card("👥", "Suscriptores", "...")
        self.card_growth = self.metric_card("📈", "Crecimiento", "...")
        self.card_engagement = self.metric_card("💬", "Engagement", "...")
        self.card_last_post = self.metric_card("🕒", "Último post", "...")
        self.metrics_layout.addWidget(self.card_subs)
        self.metrics_layout.addWidget(self.card_growth)
        self.metrics_layout.addWidget(self.card_engagement)
        self.metrics_layout.addWidget(self.card_last_post)
        self.main_layout.addLayout(self.metrics_layout)

        # --- Botón de carga manual ---
        refresh_layout = QHBoxLayout()
        self.manual_refresh_btn = QPushButton("🔄 Cargar métricas del canal")
        self.manual_refresh_btn.clicked.connect(self.load_metrics)
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.manual_refresh_btn)
        refresh_layout.addStretch()
        self.main_layout.addLayout(refresh_layout)

        # --- Información del canal ---
        channel_group = QGroupBox("Información del canal")
        channel_layout = QVBoxLayout()
        self.label_channel = QLabel(f"Canal: <b>{self.channel_username}</b>")
        self.label_channel.setFont(QFont("Poppins", 13, QFont.Bold))
        self.label_channel.setTextFormat(Qt.RichText)
        self.label_desc = QLabel("Descripción: ...")
        self.label_desc.setWordWrap(True)
        channel_layout.addWidget(self.label_channel)
        channel_layout.addWidget(self.label_desc)
        channel_group.setLayout(channel_layout)
        self.main_layout.addWidget(channel_group)

        # --- Tabs de control ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self.activity_tab(), "Actividad")
        self.tabs.addTab(self.posts_tab(), "Posts")
        self.tabs.addTab(self.users_tab(), "Usuarios")
        self.tabs.addTab(self.automation_tab(), "Automatizaciones")
        self.tabs.addTab(self.gumroad_tab(), "Gumroad")
        self.tabs.addTab(self.settings_tab(), "Configuración")
        self.main_layout.addWidget(self.tabs)

        # --- Espacio exclusivo para el creador ---
        creator_box = QGroupBox()
        creator_layout = QVBoxLayout()
        creator_label = QLabel("Sebastian Lara Developers & Programming")
        creator_label.setObjectName("creator")
        creator_label.setAlignment(Qt.AlignCenter)
        creator_layout.addWidget(creator_label)
        creator_box.setLayout(creator_layout)
        self.main_layout.addWidget(creator_box)

        # --- Botón de recarga ---
        reload_layout = QHBoxLayout()
        self.reload_btn = QPushButton(QIcon("assets/icons/refresh.svg"), "Actualizar métricas")
        self.reload_btn.clicked.connect(self.load_metrics)
        reload_layout.addStretch()
        reload_layout.addWidget(self.reload_btn)
        self.main_layout.addLayout(reload_layout)
        self.main_layout.addStretch()

    def metric_card(self, icon, title, value):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(card)
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setFont(QFont("Poppins", 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        value_label = QLabel(value)
        value_label.setFont(QFont("Poppins", 16, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.value_label = value_label  # Para actualizar luego
        return card

    def activity_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setPlaceholderText("Aquí aparecerán notificaciones y eventos recientes del canal/grupo...")
        layout.addWidget(QLabel("Actividad reciente"))
        layout.addWidget(self.activity_log)
        return tab

    def posts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.posts_table = QTableWidget(0, 5)
        self.posts_table.setHorizontalHeaderLabels(["Título", "Fecha", "Vistas", "Reacciones", "Engagement"])
        self.posts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.posts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.posts_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(QLabel("Últimos posts"))
        layout.addWidget(self.posts_table)
        return tab

    def users_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(["Usuario", "Rol", "Actividad"])
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(QLabel("Miembros del canal/grupo"))
        layout.addWidget(self.users_table)
        return tab

    def automation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        auto_box = QGroupBox("Reglas de automatización")
        auto_layout = QVBoxLayout()
        self.keyword_box = QLineEdit()
        self.keyword_box.setPlaceholderText("Palabra clave para respuesta automática")
        self.auto_response = QTextEdit()
        self.auto_response.setPlaceholderText("Respuesta automática")
        self.save_rule_btn = QPushButton("Guardar regla")
        auto_layout.addWidget(self.keyword_box)
        auto_layout.addWidget(self.auto_response)
        auto_layout.addWidget(self.save_rule_btn)
        auto_box.setLayout(auto_layout)
        layout.addWidget(auto_box)
        return tab

    def gumroad_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.gumroad_products_table = QTableWidget(0, 3)
        self.gumroad_products_table.setHorizontalHeaderLabels(["Nombre", "Precio", "Link"])
        layout.addWidget(QLabel("Productos/Scripts en Gumroad"))
        layout.addWidget(self.gumroad_products_table)
        self.gumroad_sales_table = QTableWidget(0, 3)
        self.gumroad_sales_table.setHorizontalHeaderLabels(["Comprador", "Producto", "Fecha"])
        layout.addWidget(QLabel("Ventas en Gumroad"))
        layout.addWidget(self.gumroad_sales_table)
        tab.setLayout(layout)
        return tab

    def settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Configuración del canal/grupo"))
        self.channel_edit = QLineEdit(self.channel_username)
        self.channel_edit.setPlaceholderText("Username o link del canal/grupo")
        layout.addWidget(self.channel_edit)
        self.gumroad_token_edit = QLineEdit(self.gumroad_token)
        self.gumroad_token_edit.setPlaceholderText("Token de Gumroad")
        layout.addWidget(self.gumroad_token_edit)
        self.save_config_btn = QPushButton("Guardar configuración")
        self.save_config_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_config_btn)
        return tab

    def save_config(self):
        self.channel_username = self.channel_edit.text()
        self.gumroad_token = self.gumroad_token_edit.text()
        # Aquí puedes guardar los tokens en tu config o archivo según tu lógica
        self.load_gumroad_data()
        self.load_metrics()

    def load_gumroad_data(self):
        if not self.gumroad_token:
            return
        try:
            products = get_gumroad_products(self.gumroad_token)
            self.gumroad_products_table.setRowCount(len(products))
            for row, prod in enumerate(products):
                self.gumroad_products_table.setItem(row, 0, QTableWidgetItem(prod.get("name", "")))
                self.gumroad_products_table.setItem(row, 1, QTableWidgetItem(str(prod.get("price", ""))))
                self.gumroad_products_table.setItem(row, 2, QTableWidgetItem(prod.get("short_url", "")))
            sales = get_gumroad_sales(self.gumroad_token)
            self.gumroad_sales_table.setRowCount(len(sales))
            for row, sale in enumerate(sales):
                self.gumroad_sales_table.setItem(row, 0, QTableWidgetItem(sale.get("buyer_email", "")))
                self.gumroad_sales_table.setItem(row, 1, QTableWidgetItem(sale.get("product_name", "")))
                self.gumroad_sales_table.setItem(row, 2, QTableWidgetItem(sale.get("sale_timestamp", "")))
        except Exception as e:
            QMessageBox.critical(self, "Error Gumroad", str(e))

    def load_metrics(self):
        """Load channel metrics with improved caching and error handling"""
        try:
            # Show loading message
            self.card_subs.value_label.setText("Loading...")
            self.card_growth.value_label.setText("Loading...")
            self.card_engagement.value_label.setText("Loading...")
            self.card_last_post.value_label.setText("Loading...")
            
            # Use enhanced client with caching
            info = get_channel_info(self.channel_username, force_refresh=False)
            
            if info:
                self.card_subs.value_label.setText(str(info.get("subscribers", "N/A")))
                self.card_growth.value_label.setText("N/A")  # Will be calculated from monitoring
                self.card_engagement.value_label.setText("...")
                self.card_last_post.value_label.setText("...")

                # Update description
                description = info.get("about", "No description available")
                self.label_desc.setText(f"Descripción: {description}")
                
                # Update channel title with ID
                channel_id = info.get("id", "Unknown")
                title = info.get("title", "Unknown Channel")
                self.label_channel.setText(f"Canal: <b>{title}</b> (ID: {channel_id})")
            else:
                self.card_subs.value_label.setText("Error")
                self.label_desc.setText("Descripción: No se pudo cargar la información del canal")

            # Load posts with enhanced information
            posts = get_last_posts(self.channel_username, limit=5)
            self.posts_table.setRowCount(len(posts))
            
            total_engagement = 0
            total_views = 0
            
            for row, post in enumerate(posts):
                title = (post.get("text", "") or "")[:30].replace('\n', ' ')
                date_str = str(post.get("date", ""))
                views = post.get("views", 0) or 0
                reactions = post.get("reactions", 0) or 0
                replies = post.get("replies", 0) or 0
                forwards = post.get("forwards", 0) or 0
                media_type = post.get("media_type", "")
                
                # Add media indicator to title
                if media_type:
                    title = f"[{media_type.upper()}] {title}"
                
                self.posts_table.setItem(row, 0, QTableWidgetItem(title))
                self.posts_table.setItem(row, 1, QTableWidgetItem(date_str))
                self.posts_table.setItem(row, 2, QTableWidgetItem(str(views)))
                
                # Enhanced reactions display
                total_reactions = reactions + replies + forwards
                self.posts_table.setItem(row, 3, QTableWidgetItem(f"{total_reactions} (R:{reactions}, F:{forwards})"))
                
                # Calculate engagement rate
                if views > 0:
                    engagement = (total_reactions / views) * 100
                    self.posts_table.setItem(row, 4, QTableWidgetItem(f"{engagement:.2f}%"))
                    total_engagement += engagement
                else:
                    self.posts_table.setItem(row, 4, QTableWidgetItem("0%"))
                
                # Safely add to total views
                total_views += views
                
                # Enhanced activity log
                self.activity_log.append(
                    f"[{date_str}] {title} | Views: {views} | "
                    f"Reactions: {reactions} | Replies: {replies} | Forwards: {forwards}"
                )
            
            # Calculate and display metrics
            if posts:
                avg_engagement = total_engagement / len(posts)
                self.card_engagement.value_label.setText(f"{avg_engagement:.2f}%")
                
                # Show last post date
                last_post_date = posts[0].get("date", "N/A")
                self.card_last_post.value_label.setText(str(last_post_date))
                
                # Calculate growth estimation (basic) - with null safety
                if len(posts) >= 2:
                    # Safely handle None values in views
                    recent_views = [p.get("views", 0) or 0 for p in posts[:2]]
                    older_views = [p.get("views", 0) or 0 for p in posts[-2:]]
                    
                    recent_avg_views = sum(recent_views) / 2
                    older_avg_views = sum(older_views) / 2
                    
                    if older_avg_views > 0:
                        growth = ((recent_avg_views - older_avg_views) / older_avg_views) * 100
                        self.card_growth.value_label.setText(f"{growth:+.1f}%")
            else:
                self.card_engagement.value_label.setText("N/A")
                self.card_last_post.value_label.setText("N/A")
                self.card_growth.value_label.setText("N/A")
                
        except Exception as e:
            error_msg = f"Error al cargar métricas: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            
            # Set error states
            self.card_subs.value_label.setText("Error")
            self.card_growth.value_label.setText("Error")
            self.card_engagement.value_label.setText("Error")
            self.card_last_post.value_label.setText("Error")
            
            # Log error
            self.activity_log.append(f"[ERROR] {error_msg}")