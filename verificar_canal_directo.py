#!/usr/bin/env python3
"""
Verificador directo de canales por ID o username
Útil si conoces el ID o username de tu canal
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.bot_channel_extractor import BotChannelIDExtractor
from core.config import Config

def main():
    print("🔍 VERIFICADOR DIRECTO DE CANALES")
    print("=" * 40)
    print("Si conoces el ID o @username de tu canal, puedes verificarlo directamente")
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
    
    print(f"✅ Bot: {bot_test['message']}")
    print()
    
    while True:
        print("Opciones:")
        print("1. Verificar canal por @username")
        print("2. Verificar canal por ID numérico")
        print("3. Salir")
        
        opcion = input("Selecciona (1-3): ").strip()
        
        if opcion == '3':
            break
        elif opcion == '1':
            username = input("Ingresa el @username del canal (con @): ").strip()
            if not username.startswith('@'):
                username = '@' + username
            verificar_canal(extractor, username)
        elif opcion == '2':
            try:
                canal_id = input("Ingresa el ID numérico del canal: ").strip()
                if not canal_id.startswith('-'):
                    canal_id = '-' + canal_id
                verificar_canal(extractor, canal_id)
            except ValueError:
                print("❌ ID inválido")
        else:
            print("❌ Opción inválida")
        
        print()

def verificar_canal(extractor, canal_id):
    """Verificar un canal específico"""
    print(f"🔍 Verificando canal: {canal_id}")
    print("-" * 30)
    
    # Obtener info del canal
    channel_info = extractor.get_channel_info_by_id(canal_id)
    
    if not channel_info:
        print(f"❌ No se pudo acceder al canal {canal_id}")
        print("💡 Posibles razones:")
        print("   - El bot no está en el canal")
        print("   - El canal no existe")
        print("   - El ID/username es incorrecto")
        return
    
    print(f"✅ Canal encontrado:")
    print(f"   📺 Nombre: {channel_info['title']}")
    print(f"   🆔 ID: {channel_info['id']}")
    print(f"   🔗 Username: {channel_info.get('username', 'Sin username')}")
    print(f"   📝 Tipo: {channel_info['type']}")
    if channel_info.get('description'):
        print(f"   📄 Descripción: {channel_info['description'][:100]}...")
    if channel_info.get('member_count'):
        print(f"   👥 Miembros: {channel_info['member_count']}")
    
    # Verificar permisos de admin
    print()
    print("🔍 Verificando permisos de administrador...")
    admin_info = extractor.check_admin_permissions(channel_info['id'])
    
    if admin_info.get('is_admin', False):
        print("✅ ¡Eres ADMINISTRADOR en este canal!")
        print(f"   📊 Status: {admin_info['status']}")
        
        if admin_info.get('permissions'):
            print("   🔑 Permisos:")
            permissions = admin_info['permissions']
            for perm, value in permissions.items():
                emoji = "✅" if value else "❌"
                perm_name = perm.replace('can_', '').replace('_', ' ').title()
                print(f"      {emoji} {perm_name}")
        
        # Guardar resultado
        with open('canal_verificado_directo.txt', 'w', encoding='utf-8') as f:
            f.write(f"Canal verificado directamente:\n")
            f.write(f"Nombre: {channel_info['title']}\n")
            f.write(f"ID: {channel_info['id']}\n")
            f.write(f"Username: {channel_info.get('username', 'Sin username')}\n")
            f.write(f"Tipo: {channel_info['type']}\n")
            f.write(f"Admin: SÍ\n")
            f.write(f"Status: {admin_info['status']}\n")
        
        print("💾 Información guardada en: canal_verificado_directo.txt")
    else:
        print("❌ No eres administrador en este canal")
        if admin_info.get('error'):
            print(f"   Error: {admin_info['error']}")

if __name__ == "__main__":
    main()
