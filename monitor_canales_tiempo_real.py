#!/usr/bin/env python3
"""
Monitor en tiempo real para detectar canales
Ejecuta este script y luego envía mensajes en tus canales
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor
from core.config import Config

def monitor_channels():
    print("📺 MONITOR DE CANALES EN TIEMPO REAL")
    print("=" * 50)
    print("🎯 INSTRUCCIONES:")
    print("1. Deja este script ejecutándose")
    print("2. Ve a tus canales donde el bot es admin")
    print("3. Envía un mensaje EN cada canal")
    print("4. Observa cómo se detectan aquí")
    print()
    print("Presiona Ctrl+C para detener")
    print("=" * 50)
    print()
    
    # Usar token de configuración
    config = Config()
    bot_token = config.bot_token
    
    extractor = BotChannelIDExtractor(bot_token)
    
    # Verificar bot
    bot_test = extractor.test_bot_token()
    if not bot_test['success']:
        print(f"❌ Error: {bot_test['error']}")
        return
    
    print(f"✅ Bot conectado: {bot_test['message']}")
    print("🔍 Monitoreando updates...")
    print()
    
    last_update_id = 0
    detected_channels = set()
    detected_groups = set()
    
    try:
        while True:
            # Obtener updates nuevos
            updates = extractor._make_request('getUpdates', {
                'offset': last_update_id + 1,
                'limit': 100,
                'timeout': 5
            })
            
            if updates:
                for update in updates:
                    last_update_id = update['update_id']
                    chat = None
                    message_type = "unknown"
                    
                    # Verificar tipo de update
                    if 'message' in update:
                        chat = update['message'].get('chat')
                        message_type = "message"
                    elif 'channel_post' in update:
                        chat = update['channel_post'].get('chat')
                        message_type = "channel_post"
                    elif 'edited_channel_post' in update:
                        chat = update['edited_channel_post'].get('chat')
                        message_type = "edited_channel_post"
                    
                    if chat:
                        chat_type = chat.get('type', 'unknown')
                        chat_id = chat['id']
                        chat_title = chat.get('title', 'Unknown')
                        
                        # Solo mostrar canales y grupos (no chats privados)
                        if chat_type in ['channel', 'supergroup', 'group']:
                            timestamp = time.strftime("%H:%M:%S")
                            
                            if chat_type == 'channel':
                                if chat_id not in detected_channels:
                                    detected_channels.add(chat_id)
                                    print(f"🎉 [{timestamp}] ¡CANAL DETECTADO!")
                                    print(f"    📺 {chat_title}")
                                    print(f"    🆔 ID: {chat_id}")
                                    print(f"    🔍 Via: {message_type}")
                                    
                                    # Verificar si es admin
                                    admin_info = extractor.check_admin_permissions(chat_id)
                                    if admin_info.get('is_admin', False):
                                        print(f"    ✅ ¡Eres ADMIN en este canal!")
                                        
                                        # Guardar en archivo
                                        with open('canal_detectado_monitor.txt', 'a', encoding='utf-8') as f:
                                            f.write(f"[{timestamp}] CANAL DETECTADO:\n")
                                            f.write(f"Nombre: {chat_title}\n")
                                            f.write(f"ID: {chat_id}\n")
                                            f.write(f"Admin: SÍ\n")
                                            f.write("-" * 30 + "\n")
                                        
                                        print(f"    💾 Guardado en: canal_detectado_monitor.txt")
                                    else:
                                        print(f"    ❌ No eres admin en este canal")
                                    print()
                            
                            elif chat_type in ['supergroup', 'group']:
                                if chat_id not in detected_groups:
                                    detected_groups.add(chat_id)
                                    emoji = "🏢" if chat_type == 'supergroup' else "👥"
                                    print(f"📍 [{timestamp}] {chat_type.upper()} detectado:")
                                    print(f"    {emoji} {chat_title} (ID: {chat_id})")
                                    print()
            
            # Pequeña pausa
            time.sleep(2)
            
    except KeyboardInterrupt:
        print()
        print("🛑 Monitor detenido")
        
        if detected_channels:
            print(f"📊 RESUMEN: Se detectaron {len(detected_channels)} canales")
        else:
            print("📊 RESUMEN: No se detectaron canales nuevos")
            print("💡 Recuerda: Envía mensajes EN los canales como administrador")
        
        if detected_groups:
            print(f"📊 También se detectaron {len(detected_groups)} grupos/supergrupos")

if __name__ == "__main__":
    monitor_channels()
