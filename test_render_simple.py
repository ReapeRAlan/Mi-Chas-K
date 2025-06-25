#!/usr/bin/env python3
"""
Test simple de conexión a Render
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

try:
    print("Conectando a Render...")
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'), 
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        cursor_factory=RealDictCursor
    )
    print("✅ Conectado exitosamente")
    
    cursor = conn.cursor()
    
    # Probar una consulta simple
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print(f"Versión PostgreSQL: {version[0]}")
    
    # Listar tablas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"Tablas encontradas: {[t[0] for t in tables]}")
    
    # Si existe la tabla productos, obtener algunos datos
    if any(t[0] == 'productos' for t in tables):
        print("\n=== PRODUCTOS ===")
        cursor.execute("SELECT * FROM productos LIMIT 5")
        productos = cursor.fetchall()
        for p in productos:
            print(f"  {dict(p)}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
