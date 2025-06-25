#!/usr/bin/env python3
"""
Script para conectar a la base de datos real de Render y descargar todos los datos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

def connect_to_render_db():
    """Conectar a la base de datos de Render"""
    try:
        # Usar las variables de entorno correctas
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'), 
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            cursor_factory=RealDictCursor
        )
        print("✅ Conectado a la base de datos de Render")
        return conn
    except Exception as e:
        print(f"❌ Error conectando a Render: {e}")
        return None

def get_table_structure(conn, table_name):
    """Obtener la estructura de una tabla"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        print(f"❌ Error obteniendo estructura de {table_name}: {e}")
        return []

def get_all_tables(conn):
    """Obtener lista de todas las tablas"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ Error obteniendo tablas: {e}")
        return []

def get_table_data(conn, table_name, limit=None):
    """Obtener datos de una tabla"""
    try:
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return data
    except Exception as e:
        print(f"❌ Error obteniendo datos de {table_name}: {e}")
        return []

def main():
    print("=== Análisis de Base de Datos Real de Render ===")
    
    # Verificar variables de entorno
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Faltan variables de entorno: {missing_vars}")
        return
    
    print(f"Host: {os.getenv('DB_HOST')}")
    print(f"Database: {os.getenv('DB_NAME')}")
    print(f"User: {os.getenv('DB_USER')}")
    
    # Conectar
    conn = connect_to_render_db()
    if not conn:
        return
    
    try:
        # Obtener todas las tablas
        print("\n=== TABLAS EXISTENTES ===")
        tables = get_all_tables(conn)
        for table in tables:
            print(f"  - {table}")
        
        # Analizar estructura de tablas principales
        main_tables = ['productos', 'categorias', 'ventas', 'items_venta', 'detalle_ventas', 'vendedores']
        
        for table in main_tables:
            if table in tables:
                print(f"\n=== ESTRUCTURA DE {table.upper()} ===")
                structure = get_table_structure(conn, table)
                for col in structure:
                    default_val = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                    nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
                    print(f"  {col['column_name']}: {col['data_type']} ({nullable}) {default_val}")
                
                # Obtener algunos datos de ejemplo
                print(f"\n=== DATOS DE {table.upper()} (primeros 5) ===")
                data = get_table_data(conn, table, 5)
                if data:
                    for i, row in enumerate(data):
                        print(f"  Registro {i+1}: {dict(row)}")
                else:
                    print("  No hay datos")
        
        # Contar registros en cada tabla
        print("\n=== CONTEO DE REGISTROS ===")
        for table in tables:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.close()
                print(f"  {table}: {count} registros")
            except Exception as e:
                print(f"  {table}: Error - {e}")
    
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
    finally:
        conn.close()
        print("\n✅ Análisis completado")

if __name__ == "__main__":
    main()
