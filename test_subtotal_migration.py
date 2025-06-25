#!/usr/bin/env python3
"""
Test de migración de subtotal
"""
import sys
import os
import sqlite3
sys.path.insert(0, os.getcwd())

# Test directo de la migración
db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar estructura de detalle_ventas
    cursor.execute("PRAGMA table_info(detalle_ventas)")
    columns = cursor.fetchall()
    
    print("Columnas en detalle_ventas:")
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")
    
    # Verificar si existe la columna subtotal
    column_names = [col[1] for col in columns]
    
    if 'subtotal' not in column_names:
        print("\nAgregando columna subtotal...")
        cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN subtotal DECIMAL(10,2)")
        
        # Actualizar registros existentes
        cursor.execute("UPDATE detalle_ventas SET subtotal = cantidad * precio_unitario WHERE subtotal IS NULL")
        
        conn.commit()
        print("✅ Columna subtotal agregada y datos actualizados")
    else:
        print("✅ La columna subtotal ya existe")
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM detalle_ventas")
    count = cursor.fetchone()[0]
    print(f"\nTotal registros en detalle_ventas: {count}")
    
    if count > 0:
        cursor.execute("SELECT venta_id, producto_id, cantidad, precio_unitario, subtotal FROM detalle_ventas LIMIT 3")
        detalles = cursor.fetchall()
        
        print("\nPrimeros 3 registros:")
        for d in detalles:
            print(f"  Venta: {d[0]}, Producto: {d[1]}, Cant: {d[2]}, Precio: {d[3]}, Subtotal: {d[4]}")
    
    conn.close()
    print("\n✅ Test completado")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
