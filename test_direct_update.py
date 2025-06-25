#!/usr/bin/env python3
"""
Test directo de SQLite sin adaptador
"""
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

try:
    print("=== TEST UPDATE DIRECTO EN SQLITE ===")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener un producto
    cursor.execute("SELECT id, nombre, stock FROM productos LIMIT 1")
    producto = cursor.fetchone()
    
    if producto:
        print(f"Producto: {producto['nombre']} (ID: {producto['id']}, Stock: {producto['stock']})")
        
        nuevo_stock = producto['stock'] + 10
        print(f"Actualizando stock a: {nuevo_stock}")
        
        # Actualizar
        cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto['id']))
        conn.commit()
        
        print(f"Filas afectadas: {cursor.rowcount}")
        
        # Verificar
        cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto['id'],))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"Stock después de actualización: {resultado['stock']}")
            if resultado['stock'] == nuevo_stock:
                print("✅ Actualización exitosa")
            else:
                print("❌ Error en actualización")
        
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
