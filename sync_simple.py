#!/usr/bin/env python3
"""
Sincronización directa y simple desde Render
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def sync_render_to_local():
    """Sincronizar datos de Render a local"""
    print("=== INICIANDO SINCRONIZACIÓN ===")
    
    # Conectar a Render
    print("1. Conectando a Render...")
    render_conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        cursor_factory=RealDictCursor
    )
    print("✅ Conectado a Render")
    
    # Conectar a local
    print("2. Conectando a BD local...")
    local_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    local_conn = sqlite3.connect(local_path)
    local_conn.row_factory = sqlite3.Row
    print("✅ Conectado a BD local")
    
    render_cursor = render_conn.cursor()
    local_cursor = local_conn.cursor()
    
    # Limpiar tabla productos
    print("3. Limpiando productos existentes...")
    local_cursor.execute("DELETE FROM productos")
    print("✅ Productos limpiados")
    
    # Sincronizar productos
    print("4. Descargando productos de Render...")
    render_cursor.execute("SELECT * FROM productos WHERE activo = true ORDER BY id")
    productos = render_cursor.fetchall()
    
    print(f"   Encontrados {len(productos)} productos activos")
    
    for prod in productos:
        local_cursor.execute("""
            INSERT INTO productos 
            (id, nombre, precio, categoria, stock, descripcion, codigo_barras, activo, fecha_creacion, fecha_modificacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod['id'],
            prod['nombre'],
            float(prod['precio']),  # Convertir Decimal a float
            prod['categoria'] or 'General',
            prod['stock'] or 0,
            prod['descripcion'] or '',
            prod['codigo_barras'] or '',
            1,  # activo = True
            prod['fecha_creacion'] or datetime.now(),
            prod['fecha_modificacion'] or datetime.now()
        ))
    
    print(f"✅ {len(productos)} productos sincronizados")
    
    # Sincronizar categorías
    print("5. Descargando categorías...")
    try:
        render_cursor.execute("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL")
        categorias_desde_productos = render_cursor.fetchall()
        
        # Limpiar categorías
        local_cursor.execute("DELETE FROM categorias")
        
        # Insertar categorías únicas
        categorias_unicas = set()
        for cat in categorias_desde_productos:
            if cat['categoria'] and cat['categoria'] not in categorias_unicas:
                categorias_unicas.add(cat['categoria'])
                local_cursor.execute("""
                    INSERT INTO categorias (nombre, descripcion, activo)
                    VALUES (?, ?, ?)
                """, (cat['categoria'], f'Categoría {cat["categoria"]}', 1))
        
        print(f"✅ {len(categorias_unicas)} categorías sincronizadas")
        
    except Exception as e:
        print(f"⚠️ Error con categorías: {e}")
    
    # Sincronizar vendedores
    print("6. Descargando vendedores...")
    try:
        render_cursor.execute("SELECT * FROM vendedores ORDER BY id")
        vendedores = render_cursor.fetchall()
        
        # Limpiar vendedores
        local_cursor.execute("DELETE FROM vendedores")
        
        for vend in vendedores:
            local_cursor.execute("""
                INSERT INTO vendedores (id, nombre, activo)
                VALUES (?, ?, ?)
            """, (vend['id'], vend['nombre'], 1))
        
        print(f"✅ {len(vendedores)} vendedores sincronizados")
        
    except Exception as e:
        print(f"⚠️ Error con vendedores: {e}")
    
    # Guardar cambios
    print("7. Guardando cambios...")
    local_conn.commit()
    
    # Cerrar conexiones
    render_cursor.close()
    render_conn.close()
    local_cursor.close()
    local_conn.close()
    
    print("✅ SINCRONIZACIÓN COMPLETADA")
    
    # Verificar resultados
    print("\n=== VERIFICACIÓN FINAL ===")
    verify_conn = sqlite3.connect(local_path)
    verify_cursor = verify_conn.cursor()
    
    verify_cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
    productos_count = verify_cursor.fetchone()[0]
    print(f"Productos activos en local: {productos_count}")
    
    if productos_count > 0:
        verify_cursor.execute("SELECT id, nombre, precio, categoria, stock FROM productos WHERE activo = 1 LIMIT 5")
        productos_muestra = verify_cursor.fetchall()
        print("\nPrimeros 5 productos:")
        for p in productos_muestra:
            print(f"  {p[0]}: {p[1]} - ${p[2]} - {p[3]} - Stock: {p[4]}")
    
    verify_cursor.close()
    verify_conn.close()

if __name__ == "__main__":
    try:
        sync_render_to_local()
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        print(traceback.format_exc())
