#!/usr/bin/env python3
"""
Test del adaptador actualizado
"""
import sys
import os
sys.path.insert(0, os.getcwd())

print("=== PROBANDO ADAPTADOR ACTUALIZADO ===")

try:
    from database.connection_adapter import execute_query
    
    # Verificar productos
    productos = execute_query("""
        SELECT id, nombre, precio, categoria, stock, activo 
        FROM productos 
        WHERE activo = 1 
        ORDER BY nombre
        LIMIT 10
    """)
    
    print(f"Productos encontrados: {len(productos) if productos else 0}")
    
    if productos:
        print("\nProductos en la base de datos:")
        for p in productos:
            print(f"  {p['id']}: {p['nombre']} - ${p['precio']} - {p['categoria']} - Stock: {p['stock']}")
    else:
        print("❌ No se encontraron productos")
    
    # Verificar categorías
    categorias = execute_query("SELECT * FROM categorias ORDER BY nombre")
    print(f"\nCategorías encontradas: {len(categorias) if categorias else 0}")
    
    if categorias:
        for c in categorias:
            print(f"  - {c['nombre']}: {c['descripcion']}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
