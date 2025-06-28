#!/usr/bin/env python3
"""
Test rápido de la herramienta de extracción de IDs de canales
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.bot_channel_extractor import BotChannelIDExtractor

def test_bot_token():
    """Test the bot token and extract channel IDs"""
    # Tu token del config.py
    bot_token = '8033359786:AAH919qQ2iv2lYZZYuFlvb51PIgP1mNmRLY'
    
    print("🤖 Probando herramienta de extracción de IDs de canales")
    print("=" * 60)
    
    try:
        # Crear el extractor
        extractor = BotChannelIDExtractor(bot_token)
        
        # Probar el token
        print("🔍 Probando token del bot...")
        result = extractor.test_bot_token()
        
        if result['success']:
            print("✅ Token válido!")
            print(f"Bot: @{result['bot_username']} ({result['bot_name']})")
            print(f"ID del Bot: {result['bot_id']}")
            print()
            
            # Buscar canales donde el bot es admin
            print("📡 Buscando canales donde el bot es administrador...")
            print("(Esto puede tomar unos segundos...)")
            print()
            
            admin_channels = extractor.get_admin_channels()
            
            if admin_channels:
                print(f"🎯 ¡Encontrados {len(admin_channels)} canales/grupos!")
                print("=" * 60)
                
                for i, channel in enumerate(admin_channels, 1):
                    username_str = f"@{channel['username']}" if channel['username'] else "Privado"
                    print(f"{i:2d}. {channel['title']}")
                    print(f"    ID: {channel['id']}")
                    print(f"    Username: {username_str}")
                    print(f"    Tipo: {channel['type'].title()}")
                    print(f"    Estado: {channel['admin_status'].title()}")
                    print()
                
                print("📋 LISTA DE IDs PARA COPIAR:")
                print("-" * 30)
                for channel in admin_channels:
                    print(channel['id'])
                
                return True
            else:
                print("❌ No se encontraron canales donde el bot sea administrador")
                print()
                print("Posibles razones:")
                print("• El bot no es administrador en ningún canal")
                print("• El bot necesita recibir mensajes primero en los canales")
                print("• Los canales no han tenido actividad reciente")
                print()
                print("💡 Sugerencia: Envía un mensaje al bot desde los canales donde es admin")
                return False
        else:
            print("❌ Token inválido o error:")
            print(f"   {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_token()
    
    if success:
        print("\n✅ ¡Extracción completada exitosamente!")
    else:
        print("\n❌ La extracción no fue exitosa")
    
    print("\n💡 También puedes usar:")
    print("   python extract_channel_ids.py  # Para interfaz interactiva")
    print("   python utils/channel_id_extractor_gui.py  # Para interfaz gráfica")
