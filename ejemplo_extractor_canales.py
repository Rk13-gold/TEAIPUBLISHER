#!/usr/bin/env python3
"""
Ejemplo de uso del Bot Channel Extractor
Muestra cómo usar el sistema unificado programáticamente
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor, extract_admin_channel_ids_only

def ejemplo_basico():
    """Ejemplo básico de extracción de IDs de canales admin"""
    print("🤖 Ejemplo Básico - Extracción de IDs de Canales Admin")
    print("=" * 60)
    
    # IMPORTANTE: Reemplaza con tu token real
    bot_token = "YOUR_BOT_TOKEN_HERE"
    
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Por favor, configura tu bot token real en la variable 'bot_token'")
        print("   Puedes obtener un token de @BotFather en Telegram")
        return
    
    try:
        # Método 1: Extracción rápida (solo IDs)
        print("\n📡 Método 1: Extracción Rápida (solo IDs)")
        print("-" * 40)
        
        success, channel_ids, message = extract_admin_channel_ids_only(
            bot_token=bot_token,
            verbose=True,
            comprehensive=False
        )
        
        if success:
            print(f"\n✅ {message}")
            print("📋 IDs encontradas:")
            for i, channel_id in enumerate(channel_ids, 1):
                print(f"  {i}. {channel_id}")
        else:
            print(f"❌ Error: {message}")
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def ejemplo_detallado():
    """Ejemplo detallado usando la clase directamente"""
    print("\n\n🔍 Ejemplo Detallado - Usando la Clase Directamente")
    print("=" * 60)
    
    # IMPORTANTE: Reemplaza con tu token real
    bot_token = "YOUR_BOT_TOKEN_HERE"
    
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Por favor, configura tu bot token real en la variable 'bot_token'")
        return
    
    try:
        # Crear instancia del extractor
        extractor = BotChannelIDExtractor(bot_token)
        
        # Paso 1: Probar el token del bot
        print("\n🔍 Paso 1: Probando token del bot...")
        bot_test = extractor.test_bot_token()
        
        if not bot_test['success']:
            print(f"❌ Error con el token: {bot_test['error']}")
            return
        
        print(f"✅ {bot_test['message']}")
        
        # Paso 2: Buscar canal específico (opcional)
        print("\n🔍 Paso 2: Ejemplo de búsqueda específica")
        channel_to_search = input("Ingresa un @username o ID de canal para buscar (o presiona Enter para omitir): ").strip()
        
        if channel_to_search:
            channel_info = extractor.get_channel_info_by_id(channel_to_search)
            
            if channel_info:
                print(f"✅ Canal encontrado:")
                print(f"   Nombre: {channel_info['title']}")
                print(f"   ID: {channel_info['id']}")
                print(f"   Tipo: {channel_info['type']}")
                print(f"   Miembros: {channel_info.get('member_count', 'Desconocido')}")
                
                # Verificar permisos del bot
                admin_info = extractor.check_admin_permissions(channel_info['id'])
                if admin_info['is_admin']:
                    print(f"   Estado: 🔧 Administrador ({admin_info['status']})")
                else:
                    print(f"   Estado: 👥 Miembro o sin acceso")
            else:
                print(f"❌ Canal no encontrado: {channel_to_search}")
        
        # Paso 3: Extracción completa
        print("\n📡 Paso 3: Extracción completa de canales admin")
        print("¿Qué tipo de escaneo quieres realizar?")
        print("1. Rápido (basado en updates recientes)")
        print("2. Completo (más lento pero más exhaustivo)")
        
        choice = input("Selecciona (1 o 2, por defecto 1): ").strip() or "1"
        
        if choice == "2":
            print("🚀 Iniciando escaneo completo...")
            admin_channels = extractor.get_comprehensive_admin_channels(
                include_member_channels=False
            )
        else:
            print("⚡ Iniciando escaneo rápido...")
            admin_channels = extractor.get_admin_channels_detailed(
                check_from_updates=True
            )
        
        # Mostrar resultados
        print(f"\n🎯 Resultados: {len(admin_channels)} canales encontrados")
        print("=" * 50)
        
        if admin_channels:
            for i, channel in enumerate(admin_channels, 1):
                username = f"@{channel['username']}" if channel.get('username') else "Privado"
                is_admin = channel.get('is_admin', True)  # Por defecto True para compatibilidad
                status_emoji = "🔧" if is_admin else "👥"
                
                print(f"{i:2d}. {channel['title']}")
                print(f"    ID: {channel['id']}")
                print(f"    Username: {username}")
                print(f"    Tipo: {channel['type'].title()}")
                print(f"    Estado: {status_emoji} {channel.get('admin_status', 'Unknown').title()}")
                print()
            
            # Opción para guardar
            save_option = input("¿Quieres guardar los IDs en un archivo? (s/n): ").strip().lower()
            if save_option in ['s', 'si', 'y', 'yes']:
                filename = "extracted_admin_channels.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# Canales donde el bot es administrador\n")
                    f.write(f"# Total: {len(admin_channels)} canales\n\n")
                    
                    for channel in admin_channels:
                        f.write(f"# {channel['title']} ({channel['type']})\n")
                        f.write(f"{channel['id']}\n\n")
                
                print(f"💾 IDs guardados en {filename}")
        else:
            print("ℹ️  No se encontraron canales donde el bot sea administrador.")
            print("💡 Asegúrate de que:")
            print("   - El bot esté añadido a los canales/grupos")
            print("   - El bot tenga permisos de administrador")
            print("   - El bot haya recibido mensajes recientes en los canales")
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

def mostrar_ayuda():
    """Muestra información de ayuda"""
    print("🤖 Bot Channel ID Extractor - Ejemplos de Uso")
    print("=" * 50)
    print()
    print("📋 Este script demuestra cómo usar el sistema para extraer")
    print("   IDs de canales y grupos donde tu bot es administrador.")
    print()
    print("🔧 Pasos para usar:")
    print("   1. Obtén un token de bot de @BotFather en Telegram")
    print("   2. Añade tu bot a los canales/grupos como administrador")
    print("   3. Configura el token en este script")
    print("   4. Ejecuta el script")
    print()
    print("📊 Tipos de información que puedes obtener:")
    print("   • IDs de canales/grupos")
    print("   • Nombres y tipos de canales")
    print("   • Estado de permisos del bot")
    print("   • Información detallada de canales específicos")
    print()
    print("🚀 Métodos disponibles:")
    print("   • Escaneo rápido (basado en updates)")
    print("   • Escaneo completo (más exhaustivo)")
    print("   • Búsqueda de canales específicos")
    print()

def main():
    """Función principal"""
    print("🤖 Bot Channel ID Extractor - Ejemplos")
    print("Selecciona una opción:")
    print("1. Ejemplo básico (extracción rápida)")
    print("2. Ejemplo detallado (interactivo)")
    print("3. Mostrar ayuda")
    print("4. Salir")
    
    while True:
        choice = input("\n👉 Selecciona (1-4): ").strip()
        
        if choice == "1":
            ejemplo_basico()
            break
        elif choice == "2":
            ejemplo_detallado()
            break
        elif choice == "3":
            mostrar_ayuda()
            break
        elif choice == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Por favor selecciona 1, 2, 3 o 4.")

if __name__ == "__main__":
    main()
