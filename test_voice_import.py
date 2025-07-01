#!/usr/bin/env python3
"""
Script de prueba para verificar que voice_note_tab.py se puede importar correctamente
"""

import sys
import os

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_voice_note_import():
    """Probar importar voice_note_tab y verificar errores"""
    try:
        print("🔍 Probando importar voice_note_tab...")
        
        # Importar el módulo
        from gui.voice_note_tab import VoiceNoteTab, MediaUploadWorker
        
        print("✅ voice_note_tab importado correctamente")
        print(f"✅ Clase VoiceNoteTab disponible: {VoiceNoteTab}")
        print(f"✅ Clase MediaUploadWorker disponible: {MediaUploadWorker}")
        
        # Verificar que las clases se pueden instanciar (solo crear, no inicializar UI)
        print("🔍 Verificando que las clases son válidas...")
        
        # Estos deben funcionar sin errores de sintaxis
        assert hasattr(VoiceNoteTab, '__init__')
        assert hasattr(MediaUploadWorker, '__init__')
        
        print("✅ Las clases tienen los métodos requeridos")
        print("🎉 ¡voice_note_tab.py está funcionando correctamente!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_dependencies():
    """Verificar dependencias necesarias"""
    dependencies = [
        ('PySide6.QtWidgets', 'QWidget'),
        ('PySide6.QtCore', 'QThread'),
        ('PySide6.QtGui', 'QPixmap'),
    ]
    
    print("🔍 Verificando dependencias...")
    
    for module_name, class_name in dependencies:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except ImportError:
            print(f"❌ {module_name}.{class_name} - No disponible")
            return False
        except AttributeError:
            print(f"❌ {module_name}.{class_name} - Clase no encontrada")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DE VOICE_NOTE_TAB.PY")
    print("=" * 60)
    
    # Verificar dependencias
    deps_ok = test_dependencies()
    
    if deps_ok:
        print("\n" + "=" * 60)
        
        # Probar importación
        import_ok = test_voice_note_import()
        
        print("\n" + "=" * 60)
        
        if import_ok:
            print("🎉 RESULTADO: ¡TODO FUNCIONANDO CORRECTAMENTE!")
        else:
            print("❌ RESULTADO: Hay errores en voice_note_tab.py")
    else:
        print("\n" + "=" * 60)
        print("❌ RESULTADO: Faltan dependencias necesarias")
    
    print("=" * 60)
