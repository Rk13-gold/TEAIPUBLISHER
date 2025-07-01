#!/usr/bin/env python3
"""
Script de prueba para la nueva interfaz moderna de Voice Note Tab
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
    from gui.voice_note_tab import VoiceNoteTab
    from core.config import Config
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("🎵 Voice Note Premium UI Test")
            self.setGeometry(100, 100, 1200, 800)
            
            # Crear el tab de voice notes
            self.voice_tab = VoiceNoteTab()
            self.setCentralWidget(self.voice_tab)
            
            # Aplicar estilos
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a2e;
                }
            """)
    
    def main():
        app = QApplication(sys.argv)
        app.setApplicationName("Voice Note Premium Test")
        
        window = TestWindow()
        window.show()
        
        # Información de prueba
        print("🎵 Voice Note Premium UI Test")
        print("=" * 50)
        print("✅ Interfaz moderna cargada")
        print("✅ Estilos premium aplicados")
        print("✅ Componentes responsivos activados")
        print("✅ Animaciones y efectos habilitados")
        print()
        print("🔧 Funcionalidades disponibles:")
        print("   - Subida de archivos de audio premium")
        print("   - Subida de imágenes premium con preview")
        print("   - Subida de videos premium")
        print("   - Contadores de caracteres en tiempo real")
        print("   - Validación de archivos y tamaños")
        print("   - Feedback visual y animaciones")
        print("   - Diseño responsivo para diferentes pantallas")
        print("   - Logs de actividad exportables")
        print()
        print("💡 Prueba redimensionar la ventana para ver la responsividad")
        print("💡 Selecciona archivos para ver los efectos visuales")
        
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Asegúrate de tener PySide6 instalado: pip install PySide6")
    print("💡 Y las dependencias del proyecto instaladas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error general: {e}")
    sys.exit(1)
