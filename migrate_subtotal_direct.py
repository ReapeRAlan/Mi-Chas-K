#!/usr/bin/env python3
"""
Migración directa de subtotal
"""
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar estructura actual
cursor.execute("PRAGMA table_info(detalle_ventas)")
columns = cursor.fetchall()

print("Columnas actuales en detalle_ventas:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

column_names = [col[1] for col in columns]

if 'subtotal' not in column_names:
    print("\nAgregando columna subtotal...")
    cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN subtotal DECIMAL(10,2)")
    
    # Actualizar registros existentes
    cursor.execute("UPDATE detalle_ventas SET subtotal = cantidad * precio_unitario WHERE subtotal IS NULL")
    
    conn.commit()
    print("✅ Migración completada")
else:
    print("✅ La columna subtotal ya existe")

conn.close()
