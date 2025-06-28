#!/usr/bin/env python3
"""
Guía paso a paso para detectar canales con el bot
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor

def guia_paso_a_paso():
    """Guía interactiva para configurar y detectar canales"""
    print("🤖 GUÍA: Cómo hacer que el bot detecte tus canales")
    print("=" * 60)
    
    # Paso 1: Token
    print("\n📝 PASO 1: Configurar el Bot Token")
    print("-" * 30)
    bot_token = input("Ingresa tu bot token (de @BotFather): ").strip()
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Necesitas un token válido de @BotFather")
        print("💡 Ve a @BotFather → /newbot → Copia el token")
        return
    
    # Probar token
    print("\n🔍 Probando token...")
    extractor = BotChannelIDExtractor(bot_token)
    bot_test = extractor.test_bot_token()
    
    if not bot_test['success']:
        print(f"❌ Error con el token: {bot_test['error']}")
        return
    
    print(f"✅ Bot conectado: {bot_test['message']}")
    
    # Paso 2: Instrucciones para configurar canal
    print(f"\n📝 PASO 2: Configurar tu Canal")
    print("-" * 30)
    print("🔧 Para CADA canal donde quieres que funcione el bot:")
    print()
    print("1️⃣ Ve a tu canal en Telegram")
    print("2️⃣ Toca el nombre del canal (arriba)")
    print("3️⃣ Toca '⚙️ Configuración' o 'Editar'")
    print("4️⃣ Toca 'Administradores'")
    print("5️⃣ Toca 'Añadir administrador'")
    print(f"6️⃣ Busca: @{bot_test['bot_username']}")
    print("7️⃣ Añádelo con estos permisos:")
    print("    ✅ Publicar mensajes")
    print("    ✅ Editar mensajes del canal")
    print("    ✅ Eliminar mensajes")
    
    input("\n👉 Presiona ENTER cuando hayas añadido el bot a tus canales...")
    
    # Paso 3: Generar actividad
    print(f"\n📝 PASO 3: Generar Actividad en los Canales")
    print("-" * 30)
    print("🔥 Para que el bot detecte tus canales, necesita recibir mensajes.")
    print("En CADA canal donde añadiste el bot, escribe UNO de estos mensajes:")
    print()
    print("💬 Opciones de mensajes:")
    print("   • /start")
    print("   • Hola bot")
    print("   • Test")
    print("   • Cualquier mensaje")
    print()
    print("⚡ O también puedes:")
    print(f"   • Mencionar al bot: @{bot_test['bot_username']}")
    print("   • Reenviar un mensaje del canal al bot privado")
    
    input("\n👉 Presiona ENTER cuando hayas enviado mensajes en tus canales...")
    
    # Paso 4: Detectar canales
    print(f"\n📝 PASO 4: Detectar Canales")
    print("-" * 30)
    print("🔍 Ahora vamos a buscar los canales...")
    
    # Verificar updates primero
    print("\n📡 Verificando updates recientes...")
    channels = extractor.get_channel_ids_from_updates(limit=100)
    
    if not channels:
        print("❌ No se encontraron canales en los updates")
        print("\n💡 Posibles causas:")
        print("   • No has enviado mensajes en los canales")
        print("   • El bot no está añadido como administrador")
        print("   • Los mensajes son muy antiguos")
        print("\n🔄 Solución:")
        print("   1. Verifica que el bot esté en los canales como admin")
        print("   2. Envía un mensaje nuevo en cada canal")
        print("   3. Vuelve a ejecutar este script")
        return
    
    print(f"✅ Encontrados {len(channels)} canales en updates!")
    print("\n📋 Canales detectados:")
    
    for i, channel in enumerate(channels, 1):
        username = f"@{channel['username']}" if channel.get('username') else "🔒 Privado"
        print(f"  {i}. {channel['title']}")
        print(f"     ID: {channel['id']}")
        print(f"     Usuario: {username}")
        print(f"     Tipo: {channel['type'].title()}")
        print()
    
    # Verificar permisos de admin
    print("🔧 Verificando permisos de administrador...")
    admin_channels = []
    
    for i, channel in enumerate(channels):
        print(f"Verificando {i+1}/{len(channels)}: {channel['title']}...")
        
        admin_info = extractor.check_admin_permissions(channel['id'])
        
        if admin_info.get('is_admin', False):
            admin_channels.append(channel)
            print(f"  ✅ Bot es administrador")
        else:
            print(f"  ❌ Bot NO es administrador")
            print(f"     Error: {admin_info.get('error', 'Sin permisos')}")
    
    # Resultados finales
    print(f"\n🎯 RESULTADOS FINALES")
    print("=" * 40)
    print(f"📊 Canales detectados: {len(channels)}")
    print(f"🔧 Canales donde es admin: {len(admin_channels)}")
    
    if admin_channels:
        print(f"\n✅ IDs de canales donde el bot es administrador:")
        for channel in admin_channels:
            print(f"   {channel['id']} - {channel['title']}")
        
        # Guardar IDs
        save_option = input(f"\n💾 ¿Guardar las {len(admin_channels)} IDs en archivo? (s/n): ").strip().lower()
        if save_option in ['s', 'si', 'y', 'yes']:
            filename = "mis_canales_admin.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# IDs de canales donde el bot es administrador\n")
                f.write(f"# Total: {len(admin_channels)} canales\n\n")
                for channel in admin_channels:
                    f.write(f"# {channel['title']} ({channel['type']})\n")
                    f.write(f"{channel['id']}\n\n")
            
            print(f"✅ IDs guardadas en {filename}")
    
    else:
        print(f"\n⚠️  El bot no es administrador en ningún canal.")
        print("🔄 Para solucionarlo:")
        print("   1. Ve a cada canal")
        print("   2. Configuración → Administradores")
        print(f"   3. Busca @{bot_test['bot_username']}")
        print("   4. Dale permisos de administrador")
        print("   5. Vuelve a ejecutar este script")

def main():
    """Función principal"""
    print("🎯 Detector de Canales para Bot de Telegram")
    print("Esta guía te ayudará paso a paso")
    
    try:
        guia_paso_a_paso()
    except KeyboardInterrupt:
        print("\n\n⏹️ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
