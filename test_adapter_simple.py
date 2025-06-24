#!/usr/bin/env python3
"""
Test simple del adaptador
"""
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from database.connection_adapter import execute_query, execute_update
    
    print("=== Test Adaptador Simple ===")
    
    # Probar consulta de productos
    productos = execute_query("""
        SELECT p.*, p.categoria as categoria_nombre 
        FROM productos p 
        WHERE p.activo = 1
        ORDER BY p.nombre
    """)
    
    print(f"Productos encontrados: {len(productos) if productos else 0}")
    
    if productos:
        for p in productos[:3]:  # Mostrar solo los primeros 3
            print(f"  - {p['nombre']}: ${p['precio']} (Stock: {p['stock']})")
    
    print("✅ Adaptador funcionando correctamente")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
