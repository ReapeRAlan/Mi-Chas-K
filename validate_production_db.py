#!/usr/bin/env python3
"""
Script para validar y corregir la estructura de la base de datos en producción
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def get_database_url():
    """Obtener la URL de la base de datos"""
    # Intentar obtener desde variables de entorno
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Intentar leer desde .env
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip().strip('"\'')
                        break
        except FileNotFoundError:
            pass
    
    return db_url

def check_table_structure(cursor, table_name):
    """Verificar la estructura de una tabla"""
    print(f"\n🔍 Estructura de la tabla '{table_name}':")
    
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    if columns:
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
            if col['column_default']:
                print(f"    Default: {col['column_default']}")
    else:
        print(f"  ❌ Tabla '{table_name}' no encontrada")
    
    return len(columns) > 0

def add_missing_columns(cursor):
    """Agregar columnas faltantes"""
    print("\n🔧 Verificando y agregando columnas faltantes...")
    
    try:
        # Verificar si existe la columna 'estado' en ventas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ventas' AND column_name = 'estado'
        """)
        
        if not cursor.fetchone():
            print("➕ Agregando columna 'estado' a tabla 'ventas'...")
            cursor.execute("""
                ALTER TABLE ventas 
                ADD COLUMN estado VARCHAR(50) DEFAULT 'Completada'
            """)
            print("✅ Columna 'estado' agregada exitosamente")
        else:
            print("✅ Columna 'estado' ya existe")
        
        # Verificar otras columnas que pueden faltar
        missing_columns = [
            ("ventas", "descuento", "DECIMAL(10,2) DEFAULT 0.0"),
            ("ventas", "impuestos", "DECIMAL(10,2) DEFAULT 0.0"),
            ("ventas", "observaciones", "TEXT DEFAULT ''")
        ]
        
        for table, column, definition in missing_columns:
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            """)
            
            if not cursor.fetchone():
                print(f"➕ Agregando columna '{column}' a tabla '{table}'...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"✅ Columna '{column}' agregada exitosamente")
            else:
                print(f"✅ Columna '{column}' ya existe en '{table}'")
        
    except Exception as e:
        print(f"❌ Error al agregar columnas: {e}")
        return False
    
    return True

def validate_foreign_keys(cursor):
    """Validar y corregir problemas de foreign keys"""
    print("\n🔗 Validando foreign keys...")
    
    try:
        # Verificar registros órfanos en detalle_ventas
        cursor.execute("""
            SELECT COUNT(*) as orphans
            FROM detalle_ventas dv
            LEFT JOIN ventas v ON dv.venta_id = v.id
            WHERE v.id IS NULL
        """)
        
        orphans = cursor.fetchone()['orphans']
        if orphans > 0:
            print(f"⚠️ Encontrados {orphans} registros órfanos en detalle_ventas")
            
            # Opción de limpieza
            print("🧹 Limpiando registros órfanos...")
            cursor.execute("""
                DELETE FROM detalle_ventas
                WHERE venta_id NOT IN (SELECT id FROM ventas)
            """)
            print(f"✅ {cursor.rowcount} registros órfanos eliminados")
        else:
            print("✅ No hay registros órfanos en detalle_ventas")
        
        # Verificar productos órfanos
        cursor.execute("""
            SELECT COUNT(*) as orphan_products
            FROM detalle_ventas dv
            LEFT JOIN productos p ON dv.producto_id = p.id
            WHERE p.id IS NULL
        """)
        
        orphan_products = cursor.fetchone()['orphan_products']
        if orphan_products > 0:
            print(f"⚠️ Encontrados {orphan_products} productos órfanos en detalle_ventas")
            # Estos necesitan revisión manual
        else:
            print("✅ No hay productos órfanos en detalle_ventas")
            
    except Exception as e:
        print(f"❌ Error al validar foreign keys: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🔍 Validación y corrección de base de datos Mi Chas-K")
    print("=" * 60)
    
    # Obtener URL de base de datos
    db_url = get_database_url()
    if not db_url:
        print("❌ No se encontró DATABASE_URL")
        print("Asegúrate de tener el archivo .env con la variable DATABASE_URL")
        return
    
    print(f"🔗 Conectando a base de datos...")
    print(f"URL: {db_url[:30]}...")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa")
        
        # Verificar tablas principales
        tables = ['ventas', 'detalle_ventas', 'productos', 'categorias']
        
        for table in tables:
            exists = check_table_structure(cursor, table)
            if not exists:
                print(f"❌ Tabla crítica '{table}' no encontrada")
        
        # Agregar columnas faltantes
        if add_missing_columns(cursor):
            print("✅ Columnas verificadas/agregadas correctamente")
        
        # Validar foreign keys
        if validate_foreign_keys(cursor):
            print("✅ Foreign keys validados correctamente")
        
        # Estadísticas finales
        print("\n📊 Estadísticas de la base de datos:")
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  - {table}: {count} registros")
            except:
                print(f"  - {table}: Error al contar")
        
        print("\n✅ Validación completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
