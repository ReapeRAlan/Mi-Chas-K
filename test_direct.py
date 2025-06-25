#!/usr/bin/env python3
"""
Test directo simple
"""
import os
import sys
import sqlite3

# Test básico de SQLite
print("=== Test SQLite Directo ===")
db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
print(f"BD Path: {db_path}")
print(f"BD existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
        count = cursor.fetchone()[0]
        print(f"Productos activos: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE activo = 1 LIMIT 3")
            productos = cursor.fetchall()
            print("Primeros productos:")
            for p in productos:
                print(f"  {p[0]}: {p[1]} - ${p[2]} (Stock: {p[3]})")
        
        conn.close()
        print("✅ Test SQLite exitoso")
        
    except Exception as e:
        print(f"❌ Error SQLite: {e}")

# Test de importación básica
print("\n=== Test Importación ===")
try:
    # Cambiar al directorio del proyecto
    os.chdir('/home/ghost/Escritorio/Mi-Chas-K')
    sys.path.insert(0, '/home/ghost/Escritorio/Mi-Chas-K')
    
    # Test importación
    from database.connection_adapter import execute_query
    print("✅ Importación exitosa")
    
    # Test consulta
    productos = execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = 1")
    print(f"✅ Consulta exitosa: {productos}")
    
except Exception as e:
    import traceback
    print(f"❌ Error importación: {e}")
    print(traceback.format_exc())
