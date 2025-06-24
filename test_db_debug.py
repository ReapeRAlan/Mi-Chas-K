#!/usr/bin/env python3
"""
Script de depuración para verificar el estado de la base de datos
"""
import os
import sys
import sqlite3

print("=== Debug de Base de Datos ===")
print(f"Directorio actual: {os.getcwd()}")

# Verificar estructura de directorios
data_dir = os.path.join(os.getcwd(), 'data')
print(f"Directorio 'data' existe: {os.path.exists(data_dir)}")

db_path = os.path.join(data_dir, 'local_database.db')
print(f"Ruta de la BD: {db_path}")
print(f"BD existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    print(f"Tamaño del archivo: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tablas: {[t[0] for t in tables]}")
        
        # Verificar productos
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        print(f"Total productos: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, nombre, precio, stock, activo FROM productos LIMIT 5")
            productos = cursor.fetchall()
            print("Primeros 5 productos:")
            for p in productos:
                print(f"  {p[0]}: {p[1]} - ${p[2]} - Stock: {p[3]} - Activo: {p[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al consultar BD: {e}")

print("\n=== Probando Adaptador ===")
try:
    # Añadir el directorio actual al path
    sys.path.insert(0, os.getcwd())
    
    from database.connection_adapter import DatabaseAdapter
    print("✅ Adaptador importado correctamente")
    
    adapter = DatabaseAdapter()
    print("✅ Adaptador inicializado")
    
    # Probar consulta
    productos = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
    print(f"Consulta de productos: {productos}")
    
    # Listar algunos productos
    productos_list = adapter.execute_query("""
        SELECT id, nombre, precio, stock, activo 
        FROM productos 
        WHERE activo = 1 
        LIMIT 5
    """)
    print(f"Productos activos: {len(productos_list) if productos_list else 0}")
    
    for p in productos_list or []:
        print(f"  {p['id']}: {p['nombre']} - ${p['precio']} - Stock: {p['stock']}")
        
except Exception as e:
    import traceback
    print(f"❌ Error con adaptador: {e}")
    print(f"Traceback: {traceback.format_exc()}")
