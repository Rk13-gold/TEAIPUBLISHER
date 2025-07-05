#!/usr/bin/env python3
"""
Test de ancho consistente de mensajes en Telegram
Simula la publicación con diferentes tipos de contenido para verificar
que todos los mensajes tengan el mismo ancho visual.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_message_width_formatting():
    """Test the message width formatting"""
    
    # Simular el método format_message_width
    def format_message_width(text, base_width=50):
        """Format message to have consistent visual width across all post components"""
        # Add invisible unicode spaces for consistent width
        width_padding = "⠀" * base_width  # U+2800 (Braille Pattern Blank)
        
        # Add padding line for visual consistency
        formatted_text = f"{text}\n{width_padding}"
        
        return formatted_text
    
    print("🧪 Prueba de formateo de ancho consistente")
    print("=" * 60)
    
    # Simular diferentes tipos de mensajes
    messages = [
        {
            "type": "📝 Mensaje Principal",
            "content": "Este es el contenido principal del post con imagen y texto"
        },
        {
            "type": "🎵 Audio Premium", 
            "content": "👑 Audio Motivacional\n\n💎 Contenido Premium Exclusivo - Máxima Calidad 🔒"
        },
        {
            "type": "🎯 CTA y Hashtags",
            "content": "¡Comparte si te gustó! 👍\n#viral #motivacion #exito"
        },
        {
            "type": "🔗 Botones",
            "content": "🤔 El momento de la verdad ha llegado... ¿Cuál de estas opciones cambiará tu destino para siempre?"
        }
    ]
    
    for msg in messages:
        print(f"\n{msg['type']}:")
        print("-" * 40)
        formatted = format_message_width(msg['content'])
        print(f"'{formatted}'")
        print(f"Longitud total: {len(formatted)} caracteres")
        print(f"Líneas: {len(formatted.splitlines())}")
    
    print("\n✅ Prueba completada")
    print("\nTodos los mensajes deberían tener:")
    print("- Una línea invisible al final para mantener el ancho")
    print("- Longitud consistente visualmente")
    print("- Formateo compatible con Telegram")

def test_invisible_characters():
    """Test different invisible characters for width padding"""
    
    print("\n🔍 Prueba de caracteres invisibles")
    print("=" * 40)
    
    # Diferentes opciones de caracteres invisibles
    invisible_chars = [
        ("⠀", "Braille Pattern Blank (U+2800)"),
        ("‌", "Zero Width Non-Joiner (U+200C)"),
        ("​", "Zero Width Space (U+200B)"), 
        (" ", "Regular Space (U+0020)"),
        ("⁣", "Invisible Separator (U+2063)")
    ]
    
    test_text = "Mensaje de prueba"
    
    for char, description in invisible_chars:
        padding = char * 50
        formatted = f"{test_text}\n{padding}"
        print(f"{description}:")
        print(f"  Texto: '{formatted}'")
        print(f"  Longitud: {len(formatted)}")
        print()

if __name__ == "__main__":
    test_message_width_formatting()
    test_invisible_characters()
    
    print("\n🚀 Para probar en producción:")
    print("1. Ejecuta: python main.py")
    print("2. Ve a la pestaña 'Publicar'")
    print("3. Crea un post con imagen, audio, CTA y botones")
    print("4. Publica y verifica que todos los mensajes tengan el mismo ancho")
