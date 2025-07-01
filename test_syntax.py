#!/usr/bin/env python3
"""
Test de sintaxis del archivo publish_tab.py
"""

import ast

def test_syntax():
    try:
        with open('gui/publish_tab.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Compilar el código para verificar la sintaxis
        ast.parse(code)
        print("✅ La sintaxis del archivo publish_tab.py es correcta")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"Línea {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_syntax()
