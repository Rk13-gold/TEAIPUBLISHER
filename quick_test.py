#!/usr/bin/env python3
"""
Test simple y rápido para verificar que todos los errores están solucionados
"""

def test_imports():
    """Verificar que todos los imports funcionan"""
    try:
        print("🔍 Verificando imports...")
        
        # Test imports básicos
        from PySide6.QtWidgets import QApplication, QWidget
        from PySide6.QtCore import QThread, Signal
        from PySide6.QtGui import QPixmap
        
        print("✅ Imports de PySide6 funcionan")
        
        # Test imports del proyecto
        from gui.voice_note_tab import VoiceNoteTab, MediaUploadWorker
        from services.config_voice import VOICE_DEST_CHANNEL_ID
        
        print("✅ Imports del proyecto funcionan")
        print(f"✅ Canal configurado: {VOICE_DEST_CHANNEL_ID}")
        
        # Verificar que las clases están bien definidas
        assert callable(VoiceNoteTab)
        assert callable(MediaUploadWorker)
        
        print("✅ Clases válidas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_syntax():
    """Verificar sintaxis compilando el archivo"""
    try:
        print("🔍 Verificando sintaxis...")
        
        import py_compile
        py_compile.compile('gui/voice_note_tab.py', doraise=True)
        
        print("✅ Sintaxis correcta")
        return True
        
    except py_compile.PyCompileError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 VERIFICACIÓN RÁPIDA DE ERRORES")
    print("=" * 50)
    
    syntax_ok = check_syntax()
    imports_ok = test_imports() if syntax_ok else False
    
    print("\n" + "=" * 50)
    
    if syntax_ok and imports_ok:
        print("🎉 ¡TODO CORRECTO! No hay errores")
        print("✨ La aplicación debería funcionar ahora")
    else:
        print("❌ Aún hay errores que corregir")
    
    print("=" * 50)
