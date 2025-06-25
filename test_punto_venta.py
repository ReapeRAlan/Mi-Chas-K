#!/usr/bin/env python3
"""
Test directo del punto de venta
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from database.connection_adapter import execute_query

print("=== Test Punto de Venta ===")

# Consulta exacta del punto de venta
productos = execute_query("""
    SELECT p.*, p.categoria as categoria_nombre 
    FROM productos p 
    WHERE p.activo = 1
    ORDER BY p.nombre
""")

print(f"Productos encontrados: {len(productos) if productos else 0}")

if productos:
    print("\nProductos disponibles:")
    for p in productos:
        print(f"  ID: {p['id']}")
        print(f"  Nombre: {p['nombre']}")
        print(f"  Precio: ${p['precio']}")
        print(f"  Stock: {p['stock']}")
        print(f"  Categoría: {p.get('categoria_nombre', 'N/A')}")
        print(f"  Activo: {p['activo']}")
        print("  ---")
else:
    print("❌ No hay productos disponibles")
