#!/usr/bin/env python3
"""
Script para corregir el problema del campo 'estado' en la base de datos
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Obtener la URL de la base de datos desde las variables de entorno"""
    load_dotenv()
    return os.getenv('DATABASE_URL')

def connect_to_db():
    """Conectar a la base de datos PostgreSQL"""
    try:
        db_url = get_database_url()
        if not db_url:
            raise Exception("DATABASE_URL no encontrada en variables de entorno")
        
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise

def get_ventas_columns(conn):
    """Obtener las columnas reales de la tabla ventas"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'ventas'
                ORDER BY ordinal_position
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo columnas de ventas: {e}")
        return []

def column_exists(conn, table_name, column_name):
    """Verificar si una columna existe en una tabla"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                )
            """, (table_name, column_name))
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error verificando columna {column_name} en {table_name}: {e}")
        return False

def add_estado_column(conn):
    """Agregar la columna estado si no existe"""
    try:
        if not column_exists(conn, 'ventas', 'estado'):
            with conn.cursor() as cursor:
                cursor.execute("ALTER TABLE ventas ADD COLUMN estado VARCHAR(20) DEFAULT 'Completada'")
                conn.commit()
                logger.info("✅ Columna 'estado' agregada a la tabla ventas")
                return True
        else:
            logger.info("ℹ️ Columna 'estado' ya existe en la tabla ventas")
            return False
    except Exception as e:
        logger.error(f"Error agregando columna estado: {e}")
        conn.rollback()
        return False

def main():
    """Función principal"""
    logger.info("🔧 Iniciando corrección del campo 'estado'...")
    
    try:
        # Conectar a la base de datos
        conn = connect_to_db()
        logger.info("✅ Conectado a la base de datos de producción")
        
        # Obtener columnas actuales
        logger.info("📊 Columnas actuales en tabla ventas:")
        columns = get_ventas_columns(conn)
        
        existing_columns = []
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            logger.info(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
            existing_columns.append(col['column_name'])
        
        # Verificar si existe la columna estado
        if 'estado' not in existing_columns:
            logger.warning("⚠️ Columna 'estado' NO EXISTE")
            logger.info("🔧 Agregando columna 'estado'...")
            add_estado_column(conn)
        else:
            logger.info("✅ Columna 'estado' ya existe")
        
        # Verificar columnas finales
        logger.info("\n📊 Columnas finales en tabla ventas:")
        final_columns = get_ventas_columns(conn)
        for col in final_columns:
            logger.info(f"   - {col['column_name']}")
        
        conn.close()
        logger.info("\n✅ Corrección completada")
        
    except Exception as e:
        logger.error(f"❌ Error durante la corrección: {e}")
        raise

if __name__ == "__main__":
    main()
