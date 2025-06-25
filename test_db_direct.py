#!/usr/bin/env python3
"""
Test directo de la base de datos local
"""
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

print(f"Verificando base de datos: {db_path}")
print(f"Archivo existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    print(f"Tamaño: {os.path.getsize(db_path)} bytes")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Contar productos
    cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
    count = cursor.fetchone()[0]
    print(f"Productos activos: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, nombre, precio, categoria, stock FROM productos WHERE activo = 1 ORDER BY nombre LIMIT 10")
        productos = cursor.fetchall()
        
        print("\nProductos encontrados:")
        for p in productos:
            print(f"  {p[0]}: {p[1]} - ${p[2]} - {p[3]} - Stock: {p[4]}")
    
    # Contar categorías
    cursor.execute("SELECT COUNT(*) FROM categorias")
    cat_count = cursor.fetchone()[0]
    print(f"\nCategorías: {cat_count}")
    
    if cat_count > 0:
        cursor.execute("SELECT nombre FROM categorias ORDER BY nombre")
        categorias = cursor.fetchall()
        print("Categorías:", [c[0] for c in categorias])
    
    conn.close()
else:
    print("❌ La base de datos no existe")
