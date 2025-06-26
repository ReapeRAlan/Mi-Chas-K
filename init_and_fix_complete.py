#!/usr/bin/env python3
"""
Script de inicialización y corrección completa del sistema
"""

import sqlite3
import json
import os
from datetime import datetime
from decimal import Decimal

def create_database_structure():
    """Crear estructura completa de la base de datos"""
    print("🏗️ Creando estructura de base de datos...")
    
    try:
        conn = sqlite3.connect('sistema_facturacion.db')
        cursor = conn.cursor()
        
        # Tabla de categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de vendedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE,
                telefono TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                categoria TEXT,
                codigo_barras TEXT UNIQUE,
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendedor_id INTEGER,
                fecha TEXT NOT NULL,
                total REAL NOT NULL,
                descuento REAL DEFAULT 0,
                impuesto REAL DEFAULT 0,
                estado TEXT DEFAULT 'completada',
                metodo_pago TEXT DEFAULT 'efectivo',
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendedor_id) REFERENCES vendedores(id)
            )
        """)
        
        # Tabla de detalle de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        # Tabla de cola de sincronización
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)
        
        conn.commit()
        print("✅ Estructura de base de datos creada")
        
        # Insertar datos de ejemplo
        insert_sample_data(cursor)
        conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando estructura: {e}")
        return False

def insert_sample_data(cursor):
    """Insertar datos de ejemplo"""
    print("📝 Insertando datos de ejemplo...")
    
    try:
        # Categorías
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                      ("Bebidas", "Bebidas y refrescos"))
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                      ("Snacks", "Aperitivos y botanas"))
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                      ("Limpieza", "Productos de limpieza"))
        
        # Vendedores
        cursor.execute("INSERT OR IGNORE INTO vendedores (nombre, email) VALUES (?, ?)", 
                      ("Juan Pérez", "juan@michaska.com"))
        cursor.execute("INSERT OR IGNORE INTO vendedores (nombre, email) VALUES (?, ?)", 
                      ("María García", "maria@michaska.com"))
        
        # Productos
        productos = [
            ("Coca Cola 600ml", "Refresco de cola", 2.50, 100, "Bebidas", "7501234567890"),
            ("Papas Sabritas", "Papas fritas sabor natural", 1.75, 50, "Snacks", "7501234567891"),
            ("Detergente Ariel", "Detergente en polvo 1kg", 5.99, 25, "Limpieza", "7501234567892"),
            ("Agua Natural 1L", "Agua purificada", 1.25, 200, "Bebidas", "7501234567893"),
            ("Galletas Marías", "Galletas dulces", 1.50, 75, "Snacks", "7501234567894")
        ]
        
        for producto in productos:
            cursor.execute("""
                INSERT OR IGNORE INTO productos 
                (nombre, descripcion, precio, stock, categoria, codigo_barras) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, producto)
        
        print("✅ Datos de ejemplo insertados")
        
    except Exception as e:
        print(f"❌ Error insertando datos: {e}")

def create_sample_sync_issues():
    """Crear problemas de sincronización de ejemplo para probar las correcciones"""
    print("🧪 Creando problemas de sincronización de ejemplo...")
    
    try:
        conn = sqlite3.connect('sistema_facturacion.db')
        cursor = conn.cursor()
        
        # Problema 1: Expresión SQL en datos
        problematic_data_1 = {
            'data': {
                'id': 1,
                'nombre': 'Producto Test',
                'stock': 'COALESCE(stock, 0) - 1',  # Expresión SQL problemática
                'precio': 25.99,
                'activo': True
            },
            'original_query': 'UPDATE productos SET stock = COALESCE(stock, 0) - 1 WHERE id = ?',
            'original_params': [1]
        }
        
        cursor.execute("""
            INSERT INTO sync_queue (table_name, operation, data, timestamp)
            VALUES (?, ?, ?, ?)
        """, ('productos', 'UPDATE', json.dumps(problematic_data_1), datetime.now().isoformat()))
        
        # Problema 2: Boolean mal convertido
        problematic_data_2 = {
            'data': {
                'id': 2,
                'nombre': 'Categoría Test',
                'activo': 1,  # Debería ser boolean
                'descripcion': 'Test'
            }
        }
        
        cursor.execute("""
            INSERT INTO sync_queue (table_name, operation, data, timestamp)
            VALUES (?, ?, ?, ?)
        """, ('categorias', 'UPDATE', json.dumps(problematic_data_2), datetime.now().isoformat()))
        
        # Problema 3: UPDATE vacío (solo metadatos)
        problematic_data_3 = {
            'data': {
                'id': 3,
                'original_query': 'UPDATE ventas SET ...',
                'metadata': {'test': True},
                'timestamp': '2024-01-01'
            }
        }
        
        cursor.execute("""
            INSERT INTO sync_queue (table_name, operation, data, timestamp)
            VALUES (?, ?, ?, ?)
        """, ('ventas', 'UPDATE', json.dumps(problematic_data_3), datetime.now().isoformat()))
        
        # Problema 4: Orden incorrecto (detalle_ventas antes que ventas)
        problematic_data_4 = {
            'data': {
                'venta_id': 999,  # Venta que puede no existir
                'producto_id': 1,
                'cantidad': 2,
                'precio_unitario': 10.00,
                'subtotal': 20.00
            }
        }
        
        # Insertar con timestamp que lo haría procesar antes
        early_timestamp = datetime.now().replace(hour=0, minute=0, second=0)
        cursor.execute("""
            INSERT INTO sync_queue (table_name, operation, data, timestamp)
            VALUES (?, ?, ?, ?)
        """, ('detalle_ventas', 'INSERT', json.dumps(problematic_data_4), early_timestamp.isoformat()))
        
        conn.commit()
        conn.close()
        
        print("✅ Problemas de ejemplo creados")
        return True
        
    except Exception as e:
        print(f"❌ Error creando problemas: {e}")
        return False

def apply_sync_fixes():
    """Aplicar todas las correcciones de sincronización"""
    print("🔧 Aplicando correcciones de sincronización...")
    
    try:
        conn = sqlite3.connect('sistema_facturacion.db')
        cursor = conn.cursor()
        
        # 1. Mostrar estado inicial
        cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
        initial_status = cursor.fetchall()
        print("📊 Estado inicial:")
        for status, count in initial_status:
            print(f"  {status}: {count}")
        
        # 2. Limpiar expresiones SQL
        print("\n🧹 Limpiando expresiones SQL...")
        cursor.execute("SELECT id, data FROM sync_queue WHERE status = 'pending'")
        items = cursor.fetchall()
        
        cleaned_count = 0
        for item_id, data_json in items:
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                # Limpiar datos
                clean_data = {}
                for key, value in data_dict.items():
                    # Excluir metadatos
                    if key in ['original_query', 'original_params', 'timestamp', 'metadata', 'tags']:
                        continue
                    
                    # Excluir expresiones SQL
                    if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', 'SELECT']):
                        print(f"  🗑️ Removiendo: {key} = {value}")
                        continue
                    
                    # Convertir boolean apropiadamente
                    if isinstance(value, bool):
                        if key == 'activo':
                            clean_data[key] = value
                        else:
                            clean_data[key] = 1 if value else 0
                    elif isinstance(value, (int, str)) and key == 'activo':
                        # Convertir a boolean
                        clean_data[key] = bool(int(value))
                    elif value is not None:
                        clean_data[key] = value
                
                # Actualizar
                data['data'] = clean_data
                cursor.execute("UPDATE sync_queue SET data = ? WHERE id = ?", 
                             (json.dumps(data), item_id))
                cleaned_count += 1
                
            except Exception as e:
                print(f"  ❌ Error limpiando {item_id}: {e}")
        
        print(f"✅ {cleaned_count} elementos limpiados")
        
        # 3. Marcar UPDATEs vacíos
        print("\n🗑️ Marcando UPDATEs vacíos...")
        cursor.execute("""
            SELECT id, data FROM sync_queue 
            WHERE status = 'pending' AND operation = 'UPDATE'
        """)
        
        update_items = cursor.fetchall()
        skipped_count = 0
        
        for item_id, data_json in update_items:
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                valid_fields = sum(1 for k, v in data_dict.items() 
                                 if k != 'id' and v is not None)
                
                if valid_fields == 0:
                    cursor.execute("UPDATE sync_queue SET status = 'skipped' WHERE id = ?", 
                                 (item_id,))
                    skipped_count += 1
                    print(f"  🗑️ UPDATE vacío: ID {item_id}")
                
            except Exception as e:
                print(f"  ❌ Error verificando {item_id}: {e}")
        
        print(f"✅ {skipped_count} UPDATEs vacíos marcados")
        
        # 4. Reordenar por dependencias
        print("\n📋 Reordenando por dependencias...")
        priority_order = {
            'categorias': 1, 'vendedores': 2, 'productos': 3, 
            'ventas': 4, 'detalle_ventas': 5
        }
        
        cursor.execute("""
            SELECT id, table_name, operation FROM sync_queue 
            WHERE status = 'pending' ORDER BY id
        """)
        
        pending_items = cursor.fetchall()
        
        for i, (item_id, table_name, operation) in enumerate(pending_items):
            table_priority = priority_order.get(table_name, 6)
            op_priority = {'INSERT': 0, 'UPDATE': 1, 'DELETE': 2}.get(operation, 3)
            
            new_timestamp = datetime.now().replace(
                microsecond=table_priority * 100000 + op_priority * 10000 + i
            )
            
            cursor.execute("UPDATE sync_queue SET timestamp = ? WHERE id = ?", 
                         (new_timestamp.isoformat(), item_id))
        
        print(f"✅ {len(pending_items)} elementos reordenados")
        
        # 5. Mostrar estado final
        cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
        final_status = cursor.fetchall()
        print("\n📊 Estado final:")
        for status, count in final_status:
            print(f"  {status}: {count}")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Correcciones aplicadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando correcciones: {e}")
        return False

def test_improved_adapter():
    """Probar el adaptador mejorado"""
    print("\n🧪 Probando adaptador mejorado...")
    
    try:
        # Importar y probar
        import sys
        sys.path.append('.')
        
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        adapter = ImprovedDatabaseAdapter()
        
        # Test básico de conexión
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM productos")
            product_count = cursor.fetchone()[0]
            print(f"✅ Conexión OK - {product_count} productos encontrados")
        
        # Test de estado de sync
        status = adapter.get_sync_status()
        print(f"✅ Estado de sync: {status}")
        
        # Test de limpieza
        test_data = {
            'id': 1,
            'nombre': 'Test',
            'stock': 'COALESCE(stock, 0)',
            'activo': True
        }
        
        clean = adapter._clean_data_for_sync(test_data, 'productos')
        
        if 'stock' not in clean:
            print("✅ Limpieza de SQL funciona")
        else:
            print("❌ Limpieza de SQL falló")
            return False
        
        if clean.get('activo') is True:
            print("✅ Conversión boolean funciona")
        else:
            print("❌ Conversión boolean falló")
            return False
        
        print("🎉 Adaptador mejorado funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando adaptador: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 INICIALIZACIÓN Y CORRECCIÓN COMPLETA DEL SISTEMA")
    print("=" * 60)
    
    # Paso 1: Crear estructura de BD
    if not create_database_structure():
        print("❌ Falló la creación de la base de datos")
        return
    
    # Paso 2: Crear problemas de ejemplo
    if not create_sample_sync_issues():
        print("❌ Falló la creación de problemas de ejemplo")
        return
    
    # Paso 3: Aplicar correcciones
    if not apply_sync_fixes():
        print("❌ Fallaron las correcciones")
        return
    
    # Paso 4: Probar adaptador mejorado
    if not test_improved_adapter():
        print("❌ Falló la prueba del adaptador")
        return
    
    print("\n" + "=" * 60)
    print("🎉 SISTEMA COMPLETAMENTE INICIALIZADO Y CORREGIDO")
    print("✅ Base de datos creada con estructura completa")
    print("✅ Datos de ejemplo insertados")  
    print("✅ Problemas de sincronización corregidos")
    print("✅ Adaptador mejorado funcionando")
    print("=" * 60)

if __name__ == '__main__':
    main()
