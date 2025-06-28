#!/usr/bin/env python3
"""
Script específico para extraer solo los IDs de canales/grupos donde el bot es administrador
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.bot_channel_extractor import quick_extract_ids_only, extract_admin_channel_ids_only

def extract_admin_ids():
    """Extraer solo los IDs de canales donde el bot es admin"""
    # Tu token del config.py
    bot_token = '8033359786:AAH919qQ2iv2lYZZYuFlvb51PIgP1mNmRLY'
    
    print("🎯 EXTRACTOR DE IDs DE CANALES ADMINISTRATIVOS")
    print("=" * 60)
    print(f"Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
    print()
    
    try:
        # Método 1: Función rápida
        print("📋 MÉTODO 1: Extracción rápida")
        print("-" * 30)
        channel_ids = quick_extract_ids_only(bot_token)
        
        if channel_ids:
            print("\n" + "="*50)
            print("🎯 RESULTADO FINAL - IDs PARA USAR:")
            print("="*50)
            
            for i, channel_id in enumerate(channel_ids, 1):
                print(f"{i}. {channel_id}")
            
            print("="*50)
            
            # Guardar en archivo
            print("\n💾 Guardando IDs en archivo...")
            filename = "admin_channel_ids.txt"
            with open(filename, 'w') as f:
                for channel_id in channel_ids:
                    f.write(f"{channel_id}\n")
            
            print(f"✅ IDs guardados en: {filename}")
            
            # Para usar en la aplicación
            print("\n💡 CÓMO USAR ESTOS IDs:")
            print("1. Copia los IDs de arriba")
            print("2. Ve a la aplicación principal: python main.py")
            print("3. Ve a la pestaña: '🤖 Admin Channels'")
            print("4. Pega los IDs en el área de búsqueda")
            print("5. Haz clic en '🔍 Search by ID'")
            
            return channel_ids
        else:
            print("\n❌ No se encontraron canales donde el bot sea administrador")
            print("\n💡 Posibles soluciones:")
            print("• Asegúrate de que el bot es administrador en algunos canales")
            print("• Envía mensajes al bot desde los canales donde es admin")
            print("• Verifica que el token del bot sea correcto")
            return []
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return []

def main():
    """Función principal"""
    channel_ids = extract_admin_ids()
    
    if channel_ids:
        print(f"\n🎉 ÉXITO: Se encontraron {len(channel_ids)} IDs de canales administrados")
        
        # Mostrar de forma lista para copiar
        print("\n📋 COPIAR ESTOS IDs (uno por línea):")
        print("-" * 40)
        for channel_id in channel_ids:
            print(channel_id)
        print("-" * 40)
        
    else:
        print("\n😞 No se pudieron extraer IDs de canales")
    
    print("\nPresiona Enter para salir...")
    input()

if __name__ == "__main__":
    main()
