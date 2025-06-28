#!/usr/bin/env python3
"""
Diagnóstico específico para detectar CANALES vs GRUPOS
Herramienta para entender por qué no se detectan canales
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor
from core.config import Config

def main():
    print("📺 DIAGNÓSTICO: CANALES vs GRUPOS")
    print("=" * 50)
    print("Esta herramienta te ayuda a entender por qué no se detectan CANALES")
    print()
    
    # Usar token de configuración o pedir uno nuevo
    config = Config()
    bot_token = config.bot_token
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        bot_token = input("🤖 Ingresa tu bot token: ").strip()
    
    print()
    print("🔍 PASO 1: Inicializando extractor...")
    extractor = BotChannelIDExtractor(bot_token)
    
    # Test bot
    print("🔍 PASO 2: Verificando bot...")
    bot_test = extractor.test_bot_token()
    if not bot_test['success']:
        print(f"❌ Error: {bot_test['error']}")
        return
    
    print(f"✅ Bot: {bot_test['message']}")
    print()
    
    # Diagnóstico completo
    print("🔍 PASO 3: Diagnóstico detallado...")
    print("-" * 40)
    
    diagnosis = extractor.diagnose_channel_detection(limit=100)
    
    print(f"📊 RESUMEN:")
    print(f"   Total updates: {diagnosis['total_updates']}")
    print(f"   📺 Canales encontrados: {diagnosis['channels_found']}")
    print(f"   👥 Grupos encontrados: {diagnosis['groups_found']}")
    print(f"   🏢 Supergrupos encontrados: {diagnosis['supergroups_found']}")
    print(f"   💬 Chats privados: {diagnosis['private_chats']}")
    print()
    
    # Mostrar detalles de canales
    if diagnosis['channels_found'] > 0:
        print("📺 CANALES DETECTADOS:")
        print("-" * 30)
        for i, channel in enumerate(diagnosis['channel_details'], 1):
            username = f"@{channel['username']}" if channel['username'] else "Sin username"
            print(f"{i}. {channel['title']}")
            print(f"   ID: {channel['id']}")
            print(f"   Username: {username}")
            print(f"   Tipo: {channel['type']}")
            print(f"   Detectado via: {channel['detected_via']}")
            print()
    else:
        print("❌ NO SE DETECTARON CANALES")
        print()
    
    # Mostrar detalles de grupos
    if diagnosis['groups_found'] > 0:
        print("👥 GRUPOS DETECTADOS:")
        print("-" * 30)
        for i, group in enumerate(diagnosis['group_details'], 1):
            username = f"@{group['username']}" if group['username'] else "Sin username"
            print(f"{i}. {group['title']}")
            print(f"   ID: {group['id']}")
            print(f"   Username: {username}")
            print(f"   Tipo: {group['type']}")
            print(f"   Detectado via: {group['detected_via']}")
            print()
    
    # Mostrar recomendaciones
    print("💡 RECOMENDACIONES:")
    print("-" * 30)
    for rec in diagnosis['recommendations']:
        print(rec)
    print()
    
    # Si hay canales, verificar admin
    if diagnosis['channels_found'] > 0:
        print("🔍 PASO 4: Verificando permisos de admin en CANALES...")
        print("-" * 50)
        
        admin_channels = extractor.get_admin_channels_only()
        
        if admin_channels:
            print(f"✅ Eres admin en {len(admin_channels)} canales:")
            for channel in admin_channels:
                print(f"   📺 {channel['title']} (ID: {channel['id']})")
            
            # Guardar resultados
            with open('mis_canales_admin.txt', 'w', encoding='utf-8') as f:
                f.write("CANALES donde soy administrador:\n")
                f.write("=" * 40 + "\n\n")
                for channel in admin_channels:
                    f.write(f"Nombre: {channel['title']}\n")
                    f.write(f"ID: {channel['id']}\n")
                    f.write(f"Username: {channel.get('username', 'Sin username')}\n")
                    f.write(f"Tipo: {channel['type']}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"💾 Resultados guardados en: mis_canales_admin.txt")
        else:
            print("❌ No eres admin en ningún canal detectado")
    else:
        print("⚠️  No se detectaron canales para verificar permisos")
    
    print()
    print("📖 GUÍA RÁPIDA:")
    print("=" * 30)
    print("🔸 CANAL = Solo admins pueden enviar mensajes")
    print("🔸 GRUPO = Todos los miembros pueden enviar mensajes")
    print("🔸 SUPERGRUPO = Grupo con más funciones")
    print()
    print("Para detectar CANALES:")
    print("1. Ve al canal donde el bot es admin")
    print("2. Envía un mensaje EN el canal")
    print("3. Ejecuta este script nuevamente")
    print()

if __name__ == "__main__":
    main()
