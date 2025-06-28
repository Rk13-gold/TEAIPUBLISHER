#!/usr/bin/env python3
"""
Diagnóstico avanzado para detectar por qué no se encuentran canales
"""
import sys
import os
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor

def diagnostico_completo():
    """Diagnóstico paso a paso para encontrar el problema"""
    print("🔧 DIAGNÓSTICO AVANZADO - Detector de Canales")
    print("=" * 60)
    
    # Paso 1: Token
    print("\n📝 PASO 1: Verificar Bot Token")
    print("-" * 30)
    bot_token = input("Ingresa tu bot token: ").strip()
    
    if not bot_token:
        print("❌ Token vacío")
        return
    
    extractor = BotChannelIDExtractor(bot_token)
    
    # Paso 2: Test del bot
    print("\n🔍 PASO 2: Probando conexión del bot...")
    bot_test = extractor.test_bot_token()
    
    if not bot_test['success']:
        print(f"❌ Error con el token: {bot_test['error']}")
        return
    
    print(f"✅ Bot conectado correctamente:")
    print(f"   Nombre: {bot_test['bot_name']}")
    print(f"   Username: @{bot_test['bot_username']}")
    print(f"   ID: {bot_test['bot_id']}")
    
    # Paso 3: Verificar updates RAW
    print(f"\n🔍 PASO 3: Verificando updates RAW...")
    print("Esto muestra TODOS los updates recientes del bot")
    
    try:
        # Obtener updates directamente
        raw_updates = extractor._make_request('getUpdates', {'limit': 100})
        
        if not raw_updates:
            print("❌ No se pudieron obtener updates")
            print("💡 Posibles causas:")
            print("   • El bot nunca ha recibido mensajes")
            print("   • Los updates son muy antiguos")
            print("   • Problema de conectividad")
            return
        
        print(f"📊 Total updates encontrados: {len(raw_updates)}")
        
        if len(raw_updates) == 0:
            print("❌ No hay updates recientes")
            print("🔥 SOLUCIÓN: Envía un mensaje al bot AHORA:")
            print(f"   1. Ve a @{bot_test['bot_username']} en Telegram")
            print("   2. Envía: /start")
            print("   3. Vuelve a ejecutar este diagnóstico")
            return
        
        # Analizar cada update
        print(f"\n📋 Analizando {len(raw_updates)} updates...")
        
        canales_encontrados = []
        chats_privados = []
        otros_updates = []
        
        for i, update in enumerate(raw_updates):
            update_id = update.get('update_id', 'unknown')
            print(f"\n📄 Update #{i+1} (ID: {update_id}):")
            
            chat = None
            update_type = "unknown"
            
            # Detectar tipo de update
            if 'message' in update:
                chat = update['message'].get('chat')
                update_type = "message"
                print(f"   Tipo: Mensaje directo")
                
            elif 'channel_post' in update:
                chat = update['channel_post'].get('chat')
                update_type = "channel_post"
                print(f"   Tipo: Post de canal")
                
            elif 'edited_channel_post' in update:
                chat = update['edited_channel_post'].get('chat')
                update_type = "edited_channel_post"
                print(f"   Tipo: Post editado de canal")
                
            else:
                otros_updates.append(update)
                print(f"   Tipo: Otro ({list(update.keys())})")
                continue
            
            if chat:
                chat_id = chat.get('id')
                chat_title = chat.get('title', chat.get('first_name', 'Sin nombre'))
                chat_type = chat.get('type', 'unknown')
                chat_username = chat.get('username')
                
                print(f"   Chat ID: {chat_id}")
                print(f"   Nombre: {chat_title}")
                print(f"   Tipo: {chat_type}")
                print(f"   Username: @{chat_username}" if chat_username else "   Username: Sin username (privado)")
                
                # Clasificar el chat
                if chat_type in ['channel', 'supergroup', 'group']:
                    canales_encontrados.append({
                        'id': chat_id,
                        'title': chat_title,
                        'type': chat_type,
                        'username': chat_username,
                        'update_type': update_type
                    })
                elif chat_type == 'private':
                    chats_privados.append(chat)
        
        # Resumen de análisis
        print(f"\n📊 RESUMEN DE ANÁLISIS:")
        print("=" * 40)
        print(f"🏢 Canales/Grupos encontrados: {len(canales_encontrados)}")
        print(f"👤 Chats privados: {len(chats_privados)}")
        print(f"❓ Otros updates: {len(otros_updates)}")
        
        # Mostrar canales encontrados
        if canales_encontrados:
            print(f"\n📋 CANALES/GRUPOS DETECTADOS:")
            print("-" * 40)
            
            for i, canal in enumerate(canales_encontrados, 1):
                username_str = f"@{canal['username']}" if canal['username'] else "🔒 Privado"
                print(f"{i}. {canal['title']}")
                print(f"   ID: {canal['id']}")
                print(f"   Tipo: {canal['type'].title()}")
                print(f"   Username: {username_str}")
                print(f"   Detectado via: {canal['update_type']}")
                print()
        else:
            print(f"\n❌ NO SE ENCONTRARON CANALES EN LOS UPDATES")
            print("🔥 ESTO SIGNIFICA:")
            print("   • El bot NO ha recibido mensajes de canales")
            print("   • O los mensajes son muy antiguos")
            
        # Paso 4: Verificar permisos de admin si hay canales
        if canales_encontrados:
            print(f"\n🔍 PASO 4: Verificando permisos de administrador...")
            print("-" * 50)
            
            admin_count = 0
            
            for canal in canales_encontrados:
                print(f"\n🔧 Verificando: {canal['title']} ({canal['id']})")
                
                admin_info = extractor.check_admin_permissions(canal['id'])
                
                if admin_info.get('is_admin', False):
                    admin_count += 1
                    status = admin_info.get('status', 'unknown')
                    print(f"   ✅ BOT ES ADMINISTRADOR (Status: {status})")
                    
                    # Mostrar permisos específicos
                    permissions = admin_info.get('permissions', {})
                    if permissions:
                        print(f"   🔑 Permisos:")
                        for perm, value in permissions.items():
                            if value:
                                perm_name = perm.replace('can_', '').replace('_', ' ').title()
                                print(f"      ✅ {perm_name}")
                else:
                    error = admin_info.get('error', 'Sin permisos de admin')
                    print(f"   ❌ NO ES ADMINISTRADOR - {error}")
            
            print(f"\n🎯 RESULTADO FINAL:")
            print("=" * 30)
            print(f"📊 Canales detectados: {len(canales_encontrados)}")
            print(f"🔧 Canales donde es admin: {admin_count}")
            
            if admin_count == 0:
                print(f"\n⚠️  EL BOT NO ES ADMINISTRADOR EN NINGÚN CANAL")
                print("🔧 SOLUCIÓN:")
                print("   1. Ve a cada canal en Telegram")
                print("   2. Configuración → Administradores")
                print(f"   3. Añade @{bot_test['bot_username']} como administrador")
                print("   4. Dale permisos de 'Publicar mensajes'")
            else:
                print(f"\n🎉 ¡PERFECTO! El bot funciona correctamente")
                
        else:
            print(f"\n🚨 PROBLEMA PRINCIPAL: NO HAY CANALES EN LOS UPDATES")
            print("=" * 55)
            print("🔧 PASOS PARA SOLUCIONARLO:")
            print("1️⃣ Ve a tu canal en Telegram")
            print("2️⃣ Añade el bot como administrador:")
            print("   • Configuración → Administradores")
            print(f"   • Añadir → @{bot_test['bot_username']}")
            print("   • Dar permisos de administrador")
            print("3️⃣ Envía un mensaje EN EL CANAL:")
            print("   • /start")
            print("   • O cualquier mensaje")
            print("4️⃣ Vuelve a ejecutar este diagnóstico")
            print()
            print("💡 IMPORTANTE: El mensaje debe enviarse DESDE el canal")
            print("   No al bot privado, sino como post del canal")
            
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

def test_canal_especifico():
    """Test de un canal específico por ID o username"""
    print("\n🎯 TEST DE CANAL ESPECÍFICO")
    print("=" * 30)
    
    bot_token = input("Bot token: ").strip()
    canal_id = input("ID del canal o @username: ").strip()
    
    if not bot_token or not canal_id:
        print("❌ Faltan datos")
        return
    
    extractor = BotChannelIDExtractor(bot_token)
    
    print(f"\n🔍 Buscando canal: {canal_id}")
    
    # Obtener info del canal
    canal_info = extractor.get_channel_info_by_id(canal_id)
    
    if not canal_info:
        print(f"❌ Canal no encontrado o sin acceso: {canal_id}")
        print("💡 Verifica que:")
        print("   • El ID/username sea correcto")
        print("   • El bot tenga acceso al canal")
        return
    
    print(f"✅ Canal encontrado:")
    print(f"   Nombre: {canal_info['title']}")
    print(f"   ID: {canal_info['id']}")
    print(f"   Tipo: {canal_info['type']}")
    print(f"   Miembros: {canal_info.get('member_count', 'Desconocido')}")
    
    # Verificar permisos
    print(f"\n🔧 Verificando permisos del bot...")
    admin_info = extractor.check_admin_permissions(canal_info['id'])
    
    if admin_info.get('is_admin', False):
        print(f"✅ El bot ES administrador")
        print(f"   Status: {admin_info.get('status', 'unknown')}")
    else:
        print(f"❌ El bot NO es administrador")
        print(f"   Error: {admin_info.get('error', 'Sin permisos')}")

def main():
    """Función principal"""
    print("🔧 Diagnóstico de Canales para Bot de Telegram")
    print("Herramienta para encontrar por qué no se detectan canales")
    print()
    print("Opciones:")
    print("1. Diagnóstico completo (recomendado)")
    print("2. Test de canal específico")
    print("3. Salir")
    
    while True:
        choice = input("\nSelecciona (1-3): ").strip()
        
        if choice == "1":
            diagnostico_completo()
            break
        elif choice == "2":
            test_canal_especifico()
            break
        elif choice == "3":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
