#!/usr/bin/env python3
"""
Test de conexión a Render paso a paso
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== TEST DE CONEXIÓN A RENDER ===")

# Mostrar configuración
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")

try:
    print("\n1. Intentando conectar a PostgreSQL...")
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        cursor_factory=RealDictCursor
    )
    
    print("✅ Conexión exitosa!")
    
    cursor = conn.cursor()
    
    # Listar tablas
    print("\n2. Listando tablas disponibles...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cursor.fetchall()
    print(f"Tablas encontradas: {[t['table_name'] for t in tables]}")
    
    # Verificar estructura de productos
    if any(t['table_name'] == 'productos' for t in tables):
        print("\n3. Analizando tabla 'productos'...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'productos'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Columnas de productos:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Contar productos
        cursor.execute("SELECT COUNT(*) as count FROM productos")
        count = cursor.fetchone()
        print(f"\nTotal productos: {count['count']}")
        
        # Mostrar algunos productos
        if count['count'] > 0:
            cursor.execute("SELECT * FROM productos LIMIT 5")
            productos = cursor.fetchall()
            print("\nPrimeros 5 productos:")
            for p in productos:
                print(f"  {dict(p)}")
    
    # Verificar otras tablas importantes
    for table in ['categorias', 'ventas', 'vendedores']:
        if any(t['table_name'] == table for t in tables):
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()
            print(f"\nTotal {table}: {count['count']}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Análisis completado exitosamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
