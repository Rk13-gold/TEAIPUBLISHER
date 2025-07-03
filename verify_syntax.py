#!/usr/bin/env python3
"""
Script de verificación de sintaxis para publish_tab.py
"""
import ast
import sys

def verify_syntax(file_path):
    """Verifica la sintaxis de un archivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            source = file.read()
        
        # Verificar sintaxis básica
        ast.parse(source)
        print(f"✅ Sintaxis correcta en {file_path}")
        
        # Verificar líneas problemáticas específicas
        lines = source.split('\n')
        
        # Buscar problemas comunes
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Verificar indentación inconsistente
            if line and not line[0].isspace() and line[0] not in ['#', '\n', '\r']:
                if any(char in line for char in ['\t']) and any(char in line for char in ['    ']):
                    print(f"⚠️  Línea {i}: Posible mezcla de tabs y espacios")
            
            # Verificar corchetes y paréntesis balanceados
            if stripped.count('(') != stripped.count(')'):
                print(f"⚠️  Línea {i}: Paréntesis no balanceados: {stripped}")
            
            if stripped.count('[') != stripped.count(']'):
                print(f"⚠️  Línea {i}: Corchetes no balanceados: {stripped}")
            
            if stripped.count('{') != stripped.count('}'):
                print(f"⚠️  Línea {i}: Llaves no balanceadas: {stripped}")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en {file_path}:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error al verificar {file_path}: {e}")
        return False

if __name__ == "__main__":
    file_path = "gui/publish_tab.py"
    success = verify_syntax(file_path)
    
    if success:
        print("\n🎉 Archivo verificado correctamente - Sin errores de sintaxis detectados")
    else:
        print("\n💥 Se encontraron errores que necesitan corrección")
        sys.exit(1)
