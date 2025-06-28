#!/usr/bin/env python3
"""
Monitor en tiempo real para ver si el bot recibe mensajes del canal
"""
import sys
import os
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor

def monitor_tiempo_real():
    """Monitor que verifica updates cada 5 segundos"""
    print("📡 MONITOR EN TIEMPO REAL - Bot @CTRAUDIOBLAZEBot")
    print("=" * 60)
    
    bot_token = "8033359786:AAH919qQ2iv2lYZZYuFlvb51PIgP1mNmRLY"
    extractor = BotChannelIDExtractor(bot_token)
    
    # Verificar bot
    bot_info = extractor.test_bot_token()
    if not bot_info['success']:
        print(f"❌ Error: {bot_info['error']}")
        return
    
    print(f"✅ Monitoring bot: @{bot_info['bot_username']}")
    print()
    print("🔥 AHORA VE A TU CANAL Y ESCRIBE: /start")
    print("   (ESCRIBE EN EL CANAL, NO AL BOT PRIVADO)")
    print()
    print("👀 Monitoreando updates cada 5 segundos...")
    print("   Presiona Ctrl+C para parar")
    print("=" * 60)
    
    update_count_anterior = 0
    canales_detectados = set()
    
    try:
        while True:
            # Obtener updates
            raw_updates = extractor._make_request('getUpdates', {'limit': 50})
            
            if raw_updates:
                update_count_actual = len(raw_updates)
                
                # Si hay nuevos updates
                if update_count_actual > update_count_anterior:
                    print(f"\n🆕 NUEVO UPDATE DETECTADO! ({update_count_actual} updates total)")
                    
                    # Analizar el último update
                    ultimo_update = raw_updates[-1]
                    print(f"📄 Último update ID: {ultimo_update.get('update_id')}")
                    
                    # Verificar tipo de update
                    chat = None
                    tipo_update = "desconocido"
                    
                    if 'message' in ultimo_update:
                        chat = ultimo_update['message'].get('chat')
                        tipo_update = "message (chat privado/grupo)"
                        mensaje_texto = ultimo_update['message'].get('text', 'Sin texto')
                        print(f"📝 Mensaje: {mensaje_texto}")
                        
                    elif 'channel_post' in ultimo_update:
                        chat = ultimo_update['channel_post'].get('chat')
                        tipo_update = "channel_post (POST DE CANAL) ✅"
                        mensaje_texto = ultimo_update['channel_post'].get('text', 'Sin texto')
                        print(f"📝 Post del canal: {mensaje_texto}")
                        
                    elif 'edited_channel_post' in ultimo_update:
                        chat = ultimo_update['edited_channel_post'].get('chat')
                        tipo_update = "edited_channel_post (post editado)"
                        
                    print(f"🔍 Tipo: {tipo_update}")
                    
                    if chat:
                        chat_id = chat.get('id')
                        chat_title = chat.get('title', chat.get('first_name', 'Sin nombre'))
                        chat_type = chat.get('type')
                        chat_username = chat.get('username')
                        
                        print(f"💬 Chat detectado:")
                        print(f"   ID: {chat_id}")
                        print(f"   Nombre: {chat_title}")
                        print(f"   Tipo: {chat_type}")
                        print(f"   Username: @{chat_username}" if chat_username else "   Username: Sin username")
                        
                        # Si es canal/grupo, verificar admin
                        if chat_type in ['channel', 'supergroup', 'group']:
                            if chat_id not in canales_detectados:
                                canales_detectados.add(chat_id)
                                print(f"\n🎉 ¡CANAL/GRUPO DETECTADO POR PRIMERA VEZ!")
                                
                                # Verificar permisos de admin
                                print(f"🔧 Verificando permisos de admin...")
                                admin_info = extractor.check_admin_permissions(chat_id)
                                
                                if admin_info.get('is_admin', False):
                                    print(f"✅ ¡BOT ES ADMINISTRADOR!")
                                    print(f"   Status: {admin_info.get('status')}")
                                    print(f"🎯 ID DEL CANAL: {chat_id}")
                                    
                                    # Guardar ID
                                    with open("canal_detectado.txt", "w") as f:
                                        f.write(f"# Canal detectado: {chat_title}\n")
                                        f.write(f"{chat_id}\n")
                                    
                                    print(f"💾 ID guardada en: canal_detectado.txt")
                                else:
                                    print(f"❌ Bot NO es administrador")
                                    print(f"   Error: {admin_info.get('error')}")
                        
                        elif chat_type == 'private':
                            print(f"ℹ️  Esto es un mensaje privado, no un canal")
                    
                    update_count_anterior = update_count_actual
                    
                else:
                    # No hay nuevos updates
                    print(".", end="", flush=True)
                
            else:
                print("❌ No se pudieron obtener updates")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitor detenido")
        print(f"📊 Canales detectados en total: {len(canales_detectados)}")
        
        if canales_detectados:
            print(f"🎯 IDs de canales detectados:")
            for canal_id in canales_detectados:
                print(f"   {canal_id}")
        else:
            print(f"❌ No se detectaron canales")
            print(f"💡 Asegúrate de escribir EN EL CANAL, no al bot privado")

if __name__ == "__main__":
    monitor_tiempo_real()
