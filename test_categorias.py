#!/usr/bin/env python3
"""
Test para verificar que las categorías funcionan correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection, execute_query
from database.models import Categoria

def test_categorias():
    print("🧪 Probando funcionamiento de categorías...")
    
    try:
        # Test 1: Obtener todas las categorías
        print("\n📋 Test 1: Obtener todas las categorías")
        categorias = Categoria.get_all()
        print(f"Categorías encontradas: {len(categorias)}")
        for cat in categorias:
            print(f"  - ID: {cat.id}, Nombre: {cat.nombre}, Activo: {cat.activo}")
        
        # Test 2: Obtener solo nombres de categorías
        print("\n📝 Test 2: Obtener nombres de categorías")
        nombres = Categoria.get_nombres_categoria()
        print(f"Nombres de categorías: {nombres}")
        
        # Test 3: Probar consultas COUNT
        print("\n🔢 Test 3: Consultas COUNT")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM productos WHERE activo = TRUE")
                result = cursor.fetchone()
                productos_count = result[0] if result else 0
                print(f"Productos activos: {productos_count}")
                
                cursor.execute("SELECT COUNT(*) as count FROM categorias WHERE activo = TRUE")
                result = cursor.fetchone()
                categorias_count = result[0] if result else 0
                print(f"Categorías activas: {categorias_count}")
                
                cursor.execute("SELECT COUNT(*) as count FROM ventas")
                result = cursor.fetchone()
                ventas_count = result[0] if result else 0
                print(f"Total de ventas: {ventas_count}")
        
        print("\n✅ ¡Todos los tests pasaron exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en los tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_categorias()
