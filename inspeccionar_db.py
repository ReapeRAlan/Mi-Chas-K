#!/usr/bin/env python3
"""
Script para inspeccionar la estructura de la base de datos de producción
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtener conexión directa a la base de datos de producción"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("No se encontró DATABASE_URL en las variables de entorno")
        sys.exit(1)
    
    try:
        logger.info("Conectando a la base de datos de producción...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        logger.info("✅ Conexión establecida exitosamente")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)

def listar_tablas(conn):
    """Listar todas las tablas en la base de datos"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tablas = cursor.fetchall()
        
        logger.info("📋 TABLAS EN LA BASE DE DATOS:")
        for tabla in tablas:
            logger.info(f"   📊 {tabla['table_name']}")
        
        return [tabla['table_name'] for tabla in tablas]

def describir_tabla(conn, tabla_name):
    """Describir la estructura de una tabla específica"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (tabla_name,))
        
        columnas = cursor.fetchall()
        
        logger.info(f"\n🔍 ESTRUCTURA DE LA TABLA '{tabla_name}':")
        logger.info("-" * 60)
        for col in columnas:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            logger.info(f"   📝 {col['column_name']} - {col['data_type']} {nullable}{default}")

def mostrar_datos_muestra(conn, tabla_name, limite=3):
    """Mostrar algunos registros de muestra de la tabla"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"SELECT * FROM {tabla_name} LIMIT %s", (limite,))
            registros = cursor.fetchall()
            
            if registros:
                logger.info(f"\n📊 MUESTRA DE DATOS EN '{tabla_name}' (primeros {limite} registros):")
                logger.info("-" * 60)
                for i, registro in enumerate(registros, 1):
                    logger.info(f"   Registro {i}: {dict(registro)}")
            else:
                logger.info(f"\n📊 La tabla '{tabla_name}' está vacía")
                
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de '{tabla_name}': {e}")

def main():
    """Función principal"""
    logger.info("🔍 INSPECCIÓN DE BASE DE DATOS DE PRODUCCIÓN")
    
    conn = get_db_connection()
    
    try:
        # Listar todas las tablas
        tablas = listar_tablas(conn)
        
        # Describir cada tabla y mostrar datos de muestra
        for tabla in tablas:
            describir_tabla(conn, tabla)
            mostrar_datos_muestra(conn, tabla)
            logger.info("\n" + "="*80 + "\n")
            
    except Exception as e:
        logger.error(f"❌ Error durante la inspección: {e}")
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
