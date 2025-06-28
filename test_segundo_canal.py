#!/usr/bin/env python3
"""
Script para probar detección del segundo canal
Ejecuta después de enviar un mensaje en el segundo canal
"""

import asyncio
from utils.bot_channel_extractor import BotChannelExtractor

async def test_segundo_canal():
    """Prueba la detección después de actividad en el segundo canal"""
    extractor = BotChannelExtractor()
    
    print("🔍 Buscando canales después de actividad reciente...")
    print("=" * 50)
    
    # Obtener canales donde es admin
    admin_channels = await extractor.get_admin_channels_detailed()
    
    print(f"📊 Total canales admin encontrados: {len(admin_channels)}")
    print()
    
    for i, channel in enumerate(admin_channels, 1):
        print(f"{i}. {channel['name']}")
        print(f"   ID: {channel['id']}")
        print(f"   Tipo: {channel['type']}")
        print(f"   Username: {channel.get('username', 'Sin username')}")
        print()
    
    # Guardar resultados
    if admin_channels:
        with open('mis_canales_admin_actualizados.txt', 'w', encoding='utf-8') as f:
            f.write("Canales donde el bot es administrador:\n")
            f.write("=" * 40 + "\n\n")
            for channel in admin_channels:
                f.write(f"Nombre: {channel['name']}\n")
                f.write(f"ID: {channel['id']}\n")
                f.write(f"Tipo: {channel['type']}\n")
                f.write(f"Username: {channel.get('username', 'Sin username')}\n")
                f.write("-" * 30 + "\n")
        
        print(f"💾 Resultados guardados en: mis_canales_admin_actualizados.txt")
    
    await extractor.close()

if __name__ == "__main__":
    asyncio.run(test_segundo_canal())
