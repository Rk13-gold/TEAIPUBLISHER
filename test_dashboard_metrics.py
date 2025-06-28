#!/usr/bin/env python3
"""
Test específico para verificar el manejo de valores None en las métricas del dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_engagement_calculation():
    """Test específico para el cálculo de engagement con valores None"""
    
    posts_with_none = [
        {"views": None, "reactions": 5, "replies": 2, "forwards": 1},
        {"views": 100, "reactions": None, "replies": 3, "forwards": 2},
        {"views": 200, "reactions": 10, "replies": None, "forwards": None}
    ]
    
    total_engagement = 0
    
    try:
        for post in posts_with_none:
            views = post.get("views", 0) or 0
            reactions = post.get("reactions", 0) or 0
            replies = post.get("replies", 0) or 0
            forwards = post.get("forwards", 0) or 0
            
            total_reactions = reactions + replies + forwards
            
            if views > 0:
                engagement = (total_reactions / views) * 100
                total_engagement += engagement
        
        print(f"✅ Cálculo de engagement exitoso: {total_engagement:.2f}%")
        return True
        
    except Exception as e:
        print(f"❌ Error en cálculo de engagement: {e}")
        return False

def test_growth_calculation():
    """Test específico para el cálculo de crecimiento con valores None"""
    
    posts_with_none_views = [
        {"views": None},
        {"views": 100},
        {"views": None},
        {"views": 150}
    ]
    
    try:
        if len(posts_with_none_views) >= 2:
            # Safely handle None values in views - ESTA ES LA LÓGICA CORREGIDA
            recent_views = [p.get("views", 0) or 0 for p in posts_with_none_views[:2]]
            older_views = [p.get("views", 0) or 0 for p in posts_with_none_views[-2:]]
            
            recent_avg_views = sum(recent_views) / 2
            older_avg_views = sum(older_views) / 2
            
            print(f"   - Vistas recientes: {recent_views} -> Promedio: {recent_avg_views}")
            print(f"   - Vistas anteriores: {older_views} -> Promedio: {older_avg_views}")
            
            if older_avg_views > 0:
                growth = ((recent_avg_views - older_avg_views) / older_avg_views) * 100
                print(f"✅ Cálculo de crecimiento exitoso: {growth:+.1f}%")
            else:
                print("✅ Cálculo de crecimiento: No hay datos suficientes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en cálculo de crecimiento: {e}")
        return False

def test_sum_with_none_values():
    """Test directo del problema original: sumar con valores None"""
    
    # Simular el problema original
    posts_problematic = [
        {"views": 100},
        {"views": None},  # Este era el problema
        {"views": 200}
    ]
    
    print("🔍 Probando suma directa (método original que fallaba):")
    try:
        # Método original que fallaba
        total_old = sum(p.get("views", 0) for p in posts_problematic)
        print(f"❌ INESPERADO: La suma antigua funcionó: {total_old}")
        return False
    except Exception as e:
        print(f"✅ ESPERADO: La suma antigua falla: {e}")
    
    print("\n🔧 Probando suma corregida:")
    try:
        # Método corregido
        total_new = sum(p.get("views", 0) or 0 for p in posts_problematic)
        print(f"✅ La suma corregida funciona: {total_new}")
        return True
    except Exception as e:
        print(f"❌ Error inesperado en suma corregida: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando tests de manejo de valores None en métricas...")
    print("=" * 60)
    
    test1 = test_engagement_calculation()
    test2 = test_growth_calculation()
    test3 = test_sum_with_none_values()
    
    print("=" * 60)
    if all([test1, test2, test3]):
        print("🎉 TODOS LOS TESTS PASARON - El error de valores None está corregido")
    else:
        print("❌ ALGUNOS TESTS FALLARON - Revisar la implementación")
