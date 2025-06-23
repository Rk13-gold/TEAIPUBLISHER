import os

class Config:
    """Configuration settings for the application."""

    def __init__(self):
        # Database configuration
        self.database_path = os.path.join(os.path.dirname(__file__), 'database.db')
        
        # Telegram API configuration
        self.telegram_token = '8033359786:AAH919qQ2iv2lYZZYuFlvb51PIgP1mNmRLY'
        self.telegram_chat_id = '-1002369802047'
        
        # LM Studio configuration (actualizado para la versión actual)
        self.lm_studio_api_url = 'http://192.168.18.5:1234/v1/chat/completions'
        self.lm_studio_model = 'phi-3-mini-4k-instruct'  # Modelo por defecto, ajusta si usas otro
        self.lm_studio_api_key = ''  # Si tu LM Studio requiere API Key, colócala aquí, si no, déjalo vacío
        
        # Other settings
        self.max_post_length = 4096  # Maximum length for Telegram posts
        self.image_upload_path = os.path.join(os.path.dirname(__file__), 'uploads/images')

        # Validate paths
        self.validate()

    def validate(self):
        """Validate configuration settings."""
        if not os.path.exists(self.image_upload_path):
            os.makedirs(self.image_upload_path)