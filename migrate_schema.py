#!/usr/bin/env python3
"""
Script para verificar y migrar el esquema de la base de datos
"""
import os
import sqlite3

db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener el esquema actual de productos
    cursor.execute("PRAGMA table_info(productos)")
    columns = cursor.fetchall()
    
    print("Esquema actual de la tabla productos:")
    for col in columns:
        print(f"  {col[1]} {col[2]} (nullable: {not col[3]}) default: {col[4]}")
    
    # Verificar si existe la columna categoria
    column_names = [col[1] for col in columns]
    
    if 'categoria' not in column_names:
        print("\n❌ Falta la columna 'categoria'")
        
        if 'categoria_id' in column_names:
            print("✅ Existe 'categoria_id', creando columna 'categoria'")
            
            # Agregar columna categoria
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
            
            # Migrar datos de categoria_id a categoria (si es necesario)
            cursor.execute("""
                UPDATE productos 
                SET categoria = CASE 
                    WHEN categoria_id = 1 THEN 'Chascas'
                    WHEN categoria_id = 2 THEN 'Bebidas' 
                    WHEN categoria_id = 3 THEN 'Comida'
                    ELSE 'General'
                END
                WHERE categoria IS NULL OR categoria = 'General'
            """)
            
            print("✅ Columna 'categoria' agregada y datos migrados")
        else:
            print("Agregando columna 'categoria'...")
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
            print("✅ Columna 'categoria' agregada")
    
    # Verificar productos existentes
    cursor.execute("SELECT COUNT(*) FROM productos")
    count = cursor.fetchone()[0]
    print(f"\nProductos existentes: {count}")
    
    # Verificar si existe la columna descripcion
    if 'descripcion' not in column_names:
        print("Agregando columna 'descripcion'...")
        cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT")
        print("✅ Columna 'descripcion' agregada")
    
    # Verificar si existe la columna codigo_barras
    if 'codigo_barras' not in column_names:
        print("Agregando columna 'codigo_barras'...")
        cursor.execute("ALTER TABLE productos ADD COLUMN codigo_barras TEXT")
        print("✅ Columna 'codigo_barras' agregada")
    
    # Verificar si existe la columna fecha_modificacion
    if 'fecha_modificacion' not in column_names:
        print("Agregando columna 'fecha_modificacion'...")
        cursor.execute("ALTER TABLE productos ADD COLUMN fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Columna 'fecha_modificacion' agregada")
    
    if count == 0:
        print("Insertando productos de ejemplo...")
        cursor.execute("""
            INSERT INTO productos (nombre, precio, categoria, stock, descripcion, activo) 
            VALUES 
            ('Chasca Original', 15.50, 'Chascas', 100, 'Chasca tradicional', 1),
            ('Chasca Especial', 18.00, 'Chascas', 80, 'Chasca con ingredientes especiales', 1),
            ('Coca Cola 600ml', 12.00, 'Bebidas', 50, 'Refresco de cola', 1),
            ('Agua Natural 500ml', 8.00, 'Bebidas', 75, 'Agua purificada', 1),
            ('Papas Fritas', 10.00, 'Comida', 60, 'Papas fritas caseras', 1),
            ('Sandwich Mixto', 22.00, 'Comida', 30, 'Sandwich de jamón y queso', 1),
            ('Dulces Variados', 5.00, 'General', 200, 'Dulces surtidos', 1),
            ('Cigarros', 25.00, 'General', 40, 'Cigarrillos', 1)
        """)
        print("✅ Productos de ejemplo insertados")
    
    conn.commit()
    
    # Verificar productos activos
    cursor.execute("SELECT id, nombre, precio, stock, activo, categoria FROM productos WHERE activo = 1")
    productos = cursor.fetchall()
    
    print(f"\nProductos activos ({len(productos)}):")
    for p in productos:
        print(f"  {p[0]}: {p[1]} - ${p[2]} - Stock: {p[3]} - Categoría: {p[5]}")
    
    conn.close()
    print("\n✅ Migración completada exitosamente")

except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
