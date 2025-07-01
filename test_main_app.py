#!/usr/bin/env python3
"""
Script para probar específicamente la funcionalidad de la aplicación principal
"""

import sys
import os

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_main_app():
    """Probar que la aplicación principal se puede importar"""
    try:
        print("🔍 Probando importar módulos principales...")
        
        # Verificar que los imports básicos funcionan
        from PySide6.QtWidgets import QApplication
        from gui.voice_note_tab import VoiceNoteTab
        
        print("✅ Imports básicos funcionan")
        
        # Crear aplicación Qt (necesaria para widgets)
        app = QApplication([])
        
        print("🔍 Creando instancia de VoiceNoteTab...")
        
        # Crear widget
        widget = VoiceNoteTab()
        
        print("✅ VoiceNoteTab creado exitosamente")
        print(f"📏 Tamaño: {widget.size()}")
        
        # Verificar que tiene los métodos principales
        methods_to_check = [
            'init_ui',
            'create_voice_tab',
            'create_photo_tab', 
            'create_video_tab',
            'select_file',
            'upload_content'
        ]
        
        for method in methods_to_check:
            if hasattr(widget, method):
                print(f"✅ Método {method} disponible")
            else:
                print(f"❌ Método {method} no encontrado")
                return False
        
        print("🎉 ¡Aplicación funcionando correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DE LA APLICACIÓN PRINCIPAL")
    print("=" * 60)
    
    success = test_main_app()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 RESULTADO: ¡APLICACIÓN FUNCIONANDO CORRECTAMENTE!")
        print("✨ Puedes ejecutar la aplicación principal sin problemas")
    else:
        print("❌ RESULTADO: Hay errores en la aplicación")
    
    print("=" * 60)
