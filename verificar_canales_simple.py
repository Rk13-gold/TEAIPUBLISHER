#!/usr/bin/env python3
"""
Script simplificado para detectar el problema con los canales
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor

def verificar_problema():
    """Verificación paso a paso del problema"""
    print("🔍 VERIFICACIÓN RÁPIDA - ¿Por qué no se detectan canales?")
    print("=" * 60)
    
    # Obtener token
    bot_token = input("\n🤖 Ingresa tu bot token: ").strip()
    
    if not bot_token:
        print("❌ Token vacío")
        return
    
    # Crear extractor
    extractor = BotChannelIDExtractor(bot_token)
    
    # 1. Verificar bot
    print("\n1️⃣ Verificando bot...")
    bot_info = extractor.test_bot_token()
    
    if not bot_info['success']:
        print(f"❌ Error: {bot_info['error']}")
        return
    
    print(f"✅ Bot conectado: @{bot_info['bot_username']}")
    
    # 2. Verificar updates RAW
    print("\n2️⃣ Verificando updates recientes...")
    
    try:
        raw_updates = extractor._make_request('getUpdates', {'limit': 50})
        
        if not raw_updates:
            print("❌ No hay updates")
            print("\n🔥 SOLUCIÓN:")
            print(f"   1. Ve a @{bot_info['bot_username']} en Telegram")
            print("   2. Envía: /start")
            print("   3. Vuelve a ejecutar este script")
            return
        
        print(f"✅ {len(raw_updates)} updates encontrados")
        
        # 3. Analizar updates
        print("\n3️⃣ Analizando updates...")
        
        canales = []
        for update in raw_updates:
            chat = None
            
            if 'message' in update:
                chat = update['message'].get('chat')
            elif 'channel_post' in update:
                chat = update['channel_post'].get('chat')
            elif 'edited_channel_post' in update:
                chat = update['edited_channel_post'].get('chat')
            
            if chat and chat.get('type') in ['channel', 'supergroup', 'group']:
                canal_info = {
                    'id': chat['id'],
                    'title': chat.get('title', 'Sin nombre'),
                    'type': chat.get('type'),
                    'username': chat.get('username')
                }
                
                # Evitar duplicados
                if not any(c['id'] == canal_info['id'] for c in canales):
                    canales.append(canal_info)
        
        if not canales:
            print("❌ No se encontraron canales en los updates")
            print("\n🔥 ESTO SIGNIFICA:")
            print("   • El bot NO ha recibido mensajes de canales")
            print("   • Solo ha recibido mensajes privados")
            print("\n✅ SOLUCIÓN:")
            print("   1. Ve a tu canal en Telegram")
            print("   2. Escribe un mensaje EN EL CANAL (no al bot privado)")
            print("   3. Ejemplo: /start o 'hola'")
            print("   4. Vuelve a ejecutar este script")
            return
        
        print(f"✅ {len(canales)} canales detectados:")
        
        for i, canal in enumerate(canales, 1):
            username = f"@{canal['username']}" if canal['username'] else "🔒 Privado"
            print(f"   {i}. {canal['title']} - {username}")
        
        # 4. Verificar permisos
        print(f"\n4️⃣ Verificando permisos de administrador...")
        
        admin_canales = []
        
        for canal in canales:
            print(f"\n🔧 {canal['title']}:")
            
            admin_info = extractor.check_admin_permissions(canal['id'])
            
            if admin_info.get('is_admin', False):
                admin_canales.append(canal)
                print(f"   ✅ Es administrador")
            else:
                print(f"   ❌ NO es administrador")
                print(f"   Razón: {admin_info.get('error', 'Sin permisos')}")
        
        # 5. Resultado final
        print(f"\n🎯 RESULTADO FINAL:")
        print("=" * 30)
        print(f"📊 Canales detectados: {len(canales)}")
        print(f"🔧 Canales admin: {len(admin_canales)}")
        
        if admin_canales:
            print(f"\n🎉 ¡FUNCIONA! IDs de canales admin:")
            for canal in admin_canales:
                print(f"   {canal['id']} - {canal['title']}")
                
            # Guardar IDs
            with open("canales_admin_detectados.txt", "w", encoding="utf-8") as f:
                f.write("# Canales donde el bot es administrador\n\n")
                for canal in admin_canales:
                    f.write(f"# {canal['title']}\n")
                    f.write(f"{canal['id']}\n\n")
            
            print(f"\n💾 IDs guardadas en: canales_admin_detectados.txt")
        else:
            print(f"\n⚠️  El bot NO es administrador en ningún canal")
            print("🔧 Para solucionarlo:")
            for canal in canales:
                print(f"   • {canal['title']}: Hacer al bot administrador")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_problema()
