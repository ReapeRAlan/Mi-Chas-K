#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a la base de datos PostgreSQL de Render
"""

import os
import psycopg2
from psycopg2 import sql

# Configuración de la base de datos
DATABASE_URL = "postgresql://admin:wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd"

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        print("🔄 Intentando conectar a PostgreSQL...")
        
        # Conectar usando DATABASE_URL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa!")
        
        # Probar una consulta simple
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"📊 Versión de PostgreSQL: {db_version[0]}")
        
        # Verificar si existen tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Tablas existentes: {[table[0] for table in tables]}")
        else:
            print("📋 No hay tablas en la base de datos")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        print("✅ Conexión cerrada correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🎉 ¡La configuración de base de datos está lista para Render!")
    else:
        print("\n⚠️  Revisar la configuración de base de datos")
