import os
import json
from pathlib import Path

class Config:
    """Configuration settings for the application."""

    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / "config.json"
        
        # Default configuration
        self._set_defaults()
        
        # Load configuration from file if exists
        self.load_config()
        
        # Validate paths and settings
        self.validate()

    def _set_defaults(self):
        """Set default configuration values"""
        # Database configuration
        self.database_path = os.path.join(os.path.dirname(__file__), 'database.db')
        
        # Telegram API configuration
        self.telegram_token = '7273716189:AAHymr5zkoATEHktovNCuKZfVq2YMO4qzC0'
        self.telegram_chat_id = '-1002215165925'
        
        # Telegram Bot API configuration for channel management
        self.bot_token = self.telegram_token  # Use same token for bot operations
        self.api_id = None  # Set this if you have Telegram API credentials
        self.api_hash = None  # Set this if you have Telegram API credentials
        self.session_name = 'telegram_session'
        self.phone_number = None  # For user authentication if needed
        
        # LM Studio configuration (actualizado para la versión actual)
        self.lm_studio_api_url = 'http://192.168.18.5:1234/v1/chat/completions'
        self.lm_studio_model = 'phi-3-mini-4k-instruct'  # Modelo por defecto, ajusta si usas otro
        self.lm_studio_api_key = ''  # Si tu LM Studio requiere API Key, colócala aquí, si no, déjalo vacío

        # Groq API configuration
        self.groq_api_key = ''
        self.groq_model = 'llama-3.1-8b-instant'
        self.groq_temperature = 0.8
        self.groq_max_tokens = 900
        self.groq_top_p = 0.9
        self.groq_prompt_template = 'ai_integration/prompt_presets/viral_post_template.json'
        
        # Application settings
        self.max_post_length = 4096  # Maximum length for Telegram posts
        self.image_upload_path = os.path.join(os.path.dirname(__file__), 'uploads/images')
        self.theme = 'dark'  # Default theme
        self.language = 'es'  # Default language
        self.auto_save = True  # Auto-save projects
        self.debug_mode = False  # Debug mode
        
        # Publishing settings
        self.publishing_delay = 1.5  # Delay between messages in seconds
        self.max_retries = 3  # Maximum retries for failed operations
        self.timeout = 30  # Timeout for API requests
        
        # Audio settings
        self.audio_quality = 'ultra'  # Always maximum quality
        self.audio_format = 'ogg'  # Preferred audio format
        
        # Content generation settings
        self.ai_temperature = 0.7  # AI generation temperature
        self.ai_max_tokens = 2048  # Maximum tokens for AI generation
        self.ai_model_fallback = 'gpt-3.5-turbo'  # Fallback model

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # Update configuration with loaded data
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                        
                print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading configuration: {e}")
            print("Using default configuration")

    def save_config(self):
        """Save current configuration to JSON file"""
        try:
            config_data = {
                'telegram_token': self.telegram_token,
                'telegram_chat_id': self.telegram_chat_id,
                'bot_token': self.bot_token,
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'session_name': self.session_name,
                'phone_number': self.phone_number,
                'lm_studio_api_url': self.lm_studio_api_url,
                'lm_studio_model': self.lm_studio_model,
                'lm_studio_api_key': self.lm_studio_api_key,
                'groq_api_key': self.groq_api_key,
                'groq_model': self.groq_model,
                'groq_temperature': self.groq_temperature,
                'groq_max_tokens': self.groq_max_tokens,
                'groq_top_p': self.groq_top_p,
                'groq_prompt_template': self.groq_prompt_template,
                'max_post_length': self.max_post_length,
                'theme': self.theme,
                'language': self.language,
                'auto_save': self.auto_save,
                'debug_mode': self.debug_mode,
                'publishing_delay': self.publishing_delay,
                'max_retries': self.max_retries,
                'timeout': self.timeout,
                'audio_quality': self.audio_quality,
                'audio_format': self.audio_format,
                'ai_temperature': self.ai_temperature,
                'ai_max_tokens': self.ai_max_tokens,
                'ai_model_fallback': self.ai_model_fallback
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
                
            print("✅ Configuration saved successfully")
            return True
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False

    def validate(self):
        """Validate configuration settings."""
        # Create necessary directories
        try:
            if not os.path.exists(self.image_upload_path):
                os.makedirs(self.image_upload_path)
                print(f"✅ Created upload directory: {self.image_upload_path}")
                
            # Validate database path
            db_dir = os.path.dirname(self.database_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                print(f"✅ Created database directory: {db_dir}")
                
            # Validate Telegram configuration
            if not self.telegram_token or not self.telegram_token.strip():
                print("⚠️ Warning: Telegram token is not configured")
                
            if not self.telegram_chat_id or not self.telegram_chat_id.strip():
                print("⚠️ Warning: Telegram chat ID is not configured")
                
            # Validate LM Studio configuration
            if not self.lm_studio_api_url or not self.lm_studio_api_url.strip():
                print("⚠️ Warning: LM Studio API URL is not configured")
                
            print("✅ Configuration validation completed")
            
        except Exception as e:
            print(f"❌ Error during configuration validation: {e}")

    def get_telegram_config(self):
        """Get Telegram configuration as dictionary"""
        return {
            'token': self.telegram_token,
            'chat_id': self.telegram_chat_id,
            'bot_token': self.bot_token,
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'session_name': self.session_name,
            'phone_number': self.phone_number
        }

    def get_ai_config(self):
        """Get AI configuration as dictionary"""
        return {
            'groq_api_key': self.groq_api_key,
            'groq_model': self.groq_model,
            'groq_temperature': self.groq_temperature,
            'groq_max_tokens': self.groq_max_tokens,
            'groq_top_p': self.groq_top_p,
            'groq_prompt_template': self.groq_prompt_template
        }

    def get_publishing_config(self):
        """Get publishing configuration as dictionary"""
        return {
            'delay': self.publishing_delay,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'max_post_length': self.max_post_length,
            'audio_quality': self.audio_quality,
            'audio_format': self.audio_format
        }

    def test_configuration(self):
        """Test if configuration is valid"""
        issues = []
        
        # Test Telegram configuration
        if not self.telegram_token or len(self.telegram_token.split(':')) != 2:
            issues.append("Invalid Telegram bot token format")
            
        if not self.telegram_chat_id:
            issues.append("Missing Telegram chat ID")
            
        # Test LM Studio configuration
        if not self.lm_studio_api_url or not self.lm_studio_api_url.startswith('http'):
            issues.append("Invalid LM Studio API URL")
            
        # Test file paths
        if not os.path.exists(os.path.dirname(self.database_path)):
            issues.append("Database directory does not exist")
            
        if not os.path.exists(self.image_upload_path):
            issues.append("Image upload directory does not exist")
            
        return len(issues) == 0, issues

    def check_telegram_bot_and_chat(self):
        """Validate the bot token and chat using Telegram Bot API.

        Returns: (ok: bool, message: str)
        """
        try:
            token = getattr(self, 'bot_token', None) or getattr(self, 'telegram_token', None)
            if not token:
                return False, "Bot token not configured"
            chat_id = getattr(self, 'telegram_chat_id', None)
            if not chat_id:
                return False, "Telegram chat ID not configured"
            # Local import to avoid module import cycles during startup
            from services.telegram_bot_client import TelegramBotClient
            client = TelegramBotClient(token)
            if not client.test_connection():
                return False, "Bot token invalid or cannot connect to Bot API"
            chat_info = client.get_chat_info(chat_id)
            if not chat_info:
                return False, f"Chat not found for ID/username: {chat_id}"
            perms = client.validate_bot_permissions(chat_id)
            status = perms.get('status') if perms else None
            if status not in ['administrator', 'creator']:
                # Allow non-admin too but warn
                return True, "Bot can see the chat but does not appear to be administrator. Ensure it has permission to send messages."
            return True, "Bot and chat validation OK"
        except Exception as e:
            return False, str(e)

    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self._set_defaults()
        self.save_config()
        print("✅ Configuration reset to defaults")

    def __str__(self):
        """String representation of configuration"""
        return f"""
Telegram AI Publisher Pro Configuration:
========================================
🤖 Telegram Token: {'✅ Configured' if self.telegram_token else '❌ Not configured'}
💬 Chat ID: {'✅ Configured' if self.telegram_chat_id else '❌ Not configured'}
🧠 LM Studio URL: {self.lm_studio_api_url}
🎨 Theme: {self.theme}
🌐 Language: {self.language}
📁 Database: {self.database_path}
📂 Uploads: {self.image_upload_path}
"""