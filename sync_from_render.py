#!/usr/bin/env python3
"""
Script para sincronizar datos desde Render a la base de datos local
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

def clear_local_database():
    """Limpiar la base de datos local"""
    db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Eliminar datos existentes
        cursor.execute("DELETE FROM productos")
        cursor.execute("DELETE FROM categorias")
        cursor.execute("DELETE FROM vendedores")
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM detalle_ventas")
        
        print("✅ Base de datos local limpiada")
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error limpiando BD local: {e}")

def download_from_render():
    """Descargar datos desde Render"""
    try:
        # Conectar a Render
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
        local_conn = sqlite3.connect(os.path.join(os.getcwd(), 'data', 'local_database.db'))
        local_conn.row_factory = sqlite3.Row
        
        print("✅ Conectado a BD local")
        
        render_cursor = render_conn.cursor()
        local_cursor = local_conn.cursor()
        
        # Sincronizar categorias
        print("Sincronizando categorias...")
        render_cursor.execute("SELECT * FROM categorias ORDER BY id")
        categorias = render_cursor.fetchall()
        
        for cat in categorias:
            local_cursor.execute("""
                INSERT OR REPLACE INTO categorias (id, nombre, descripcion, activo)
                VALUES (?, ?, ?, ?)
            """, (cat['id'], cat['nombre'], cat.get('descripcion', ''), cat.get('activo', True)))
        
        print(f"✅ {len(categorias)} categorias sincronizadas")
        
        # Sincronizar productos
        print("Sincronizando productos...")
        render_cursor.execute("SELECT * FROM productos ORDER BY id")
        productos = render_cursor.fetchall()
        
        for prod in productos:
            # Obtener nombre de categoria si tiene categoria_id
            categoria_nombre = 'General'
            if 'categoria_id' in prod and prod['categoria_id']:
                for cat in categorias:
                    if cat['id'] == prod['categoria_id']:
                        categoria_nombre = cat['nombre']
                        break
            elif 'categoria' in prod and prod['categoria']:
                categoria_nombre = prod['categoria']
            
            local_cursor.execute("""
                INSERT OR REPLACE INTO productos 
                (id, nombre, precio, categoria, stock, descripcion, codigo_barras, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prod['id'], 
                prod['nombre'], 
                prod['precio'], 
                categoria_nombre,
                prod.get('stock', 0),
                prod.get('descripcion', ''),
                prod.get('codigo_barras', ''),
                prod.get('activo', True),
                prod.get('fecha_creacion', datetime.now())
            ))
        
        print(f"✅ {len(productos)} productos sincronizados")
        
        # Sincronizar vendedores
        try:
            render_cursor.execute("SELECT * FROM vendedores ORDER BY id")
            vendedores = render_cursor.fetchall()
            
            for vend in vendedores:
                local_cursor.execute("""
                    INSERT OR REPLACE INTO vendedores (id, nombre, activo)
                    VALUES (?, ?, ?)
                """, (vend['id'], vend['nombre'], vend.get('activo', True)))
            
            print(f"✅ {len(vendedores)} vendedores sincronizados")
        except Exception as e:
            print(f"⚠️ Error sincronizando vendedores: {e}")
        
        # Sincronizar ventas (últimas 100)
        try:
            render_cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 100")
            ventas = render_cursor.fetchall()
            
            for venta in ventas:
                local_cursor.execute("""
                    INSERT OR REPLACE INTO ventas 
                    (id, fecha, total, metodo_pago, vendedor, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    venta['id'],
                    venta['fecha'],
                    venta['total'],
                    venta.get('metodo_pago', 'Efectivo'),
                    venta.get('vendedor', 'Sistema'),
                    venta.get('observaciones', '')
                ))
            
            print(f"✅ {len(ventas)} ventas sincronizadas")
            
            # Sincronizar items/detalles de ventas
            venta_ids = [v['id'] for v in ventas]
            if venta_ids:
                # Probar ambos nombres de tabla
                try:
                    render_cursor.execute(f"SELECT * FROM items_venta WHERE venta_id IN ({','.join(map(str, venta_ids))})")
                    items = render_cursor.fetchall()
                    tabla_items = 'items_venta'
                except:
                    render_cursor.execute(f"SELECT * FROM detalle_ventas WHERE venta_id IN ({','.join(map(str, venta_ids))})")
                    items = render_cursor.fetchall()
                    tabla_items = 'detalle_ventas'
                
                for item in items:
                    local_cursor.execute("""
                        INSERT OR REPLACE INTO detalle_ventas 
                        (id, venta_id, producto_id, cantidad, precio_unitario)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        item['id'],
                        item['venta_id'],
                        item['producto_id'],
                        item['cantidad'],
                        item['precio_unitario']
                    ))
                
                print(f"✅ {len(items)} items de venta sincronizados desde {tabla_items}")
                
        except Exception as e:
            print(f"⚠️ Error sincronizando ventas: {e}")
        
        # Guardar cambios
        local_conn.commit()
        
        # Cerrar conexiones
        render_cursor.close()
        render_conn.close()
        local_cursor.close()
        local_conn.close()
        
        print("✅ Sincronización completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante sincronización: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def verify_local_data():
    """Verificar datos en la base de datos local"""
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(), 'data', 'local_database.db'))
        cursor = conn.cursor()
        
        # Contar registros
        tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
        
        print("\n=== VERIFICACIÓN DE DATOS LOCALES ===")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} registros")
        
        # Mostrar algunos productos
        print("\n=== PRODUCTOS LOCALES (primeros 5) ===")
        cursor.execute("SELECT id, nombre, precio, categoria, stock FROM productos LIMIT 5")
        productos = cursor.fetchall()
        
        for p in productos:
            print(f"  {p[0]}: {p[1]} - ${p[2]} - {p[3]} - Stock: {p[4]}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando datos locales: {e}")

def main():
    print("=== SINCRONIZACIÓN DE DATOS DESDE RENDER ===")
    
    # Limpiar base de datos local
    clear_local_database()
    
    # Descargar desde Render
    if download_from_render():
        # Verificar datos
        verify_local_data()
    else:
        print("❌ Falló la sincronización")

if __name__ == "__main__":
    main()
