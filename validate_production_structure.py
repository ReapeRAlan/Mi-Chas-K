#!/usr/bin/env python3
"""
Script para validar y corregir la estructura de la base de datos de producción
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

def get_table_structure(conn, table_name):
    """Obtener la estructura de una tabla"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo estructura de tabla {table_name}: {e}")
        return []

def get_foreign_keys(conn, table_name):
    """Obtener las foreign keys de una tabla"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                WHERE
                    tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = %s
            """, (table_name,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo foreign keys de {table_name}: {e}")
        return []

def table_exists(conn, table_name):
    """Verificar si una tabla existe"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table_name,))
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error verificando existencia de tabla {table_name}: {e}")
        return False

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

def add_column_if_not_exists(conn, table_name, column_name, column_definition):
    """Agregar una columna si no existe"""
    try:
        if not column_exists(conn, table_name, column_name):
            with conn.cursor() as cursor:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                cursor.execute(sql)
                conn.commit()
                logger.info(f"✅ Columna {column_name} agregada a {table_name}")
                return True
        else:
            logger.info(f"ℹ️ Columna {column_name} ya existe en {table_name}")
            return False
    except Exception as e:
        logger.error(f"Error agregando columna {column_name} a {table_name}: {e}")
        conn.rollback()
        return False

def check_orphaned_records(conn):
    """Verificar registros huérfanos en detalle_ventas"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Verificar detalle_ventas sin venta correspondiente
            cursor.execute("""
                SELECT dv.id, dv.venta_id 
                FROM detalle_ventas dv 
                LEFT JOIN ventas v ON dv.venta_id = v.id 
                WHERE v.id IS NULL
                LIMIT 10
            """)
            orphaned_details = cursor.fetchall()
            
            if orphaned_details:
                logger.warning(f"⚠️ Encontrados {len(orphaned_details)} registros huérfanos en detalle_ventas")
                for record in orphaned_details:
                    logger.warning(f"   - detalle_ventas.id={record['id']}, venta_id={record['venta_id']} (venta no existe)")
            else:
                logger.info("✅ No se encontraron registros huérfanos en detalle_ventas")
            
            return orphaned_details
    except Exception as e:
        logger.error(f"Error verificando registros huérfanos: {e}")
        return []

def clean_orphaned_records(conn):
    """Limpiar registros huérfanos"""
    try:
        with conn.cursor() as cursor:
            # Eliminar detalle_ventas huérfanos
            cursor.execute("""
                DELETE FROM detalle_ventas 
                WHERE venta_id NOT IN (SELECT id FROM ventas)
            """)
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"🧹 Eliminados {deleted_count} registros huérfanos de detalle_ventas")
            else:
                logger.info("✅ No había registros huérfanos para eliminar")
                
            return deleted_count
    except Exception as e:
        logger.error(f"Error limpiando registros huérfanos: {e}")
        conn.rollback()
        return 0

def get_table_counts(conn):
    """Obtener conteos de registros en las tablas principales"""
    tables = ['categorias', 'productos', 'ventas', 'detalle_ventas']
    counts = {}
    
    try:
        with conn.cursor() as cursor:
            for table in tables:
                if table_exists(conn, table):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
                else:
                    counts[table] = "NO EXISTE"
    except Exception as e:
        logger.error(f"Error obteniendo conteos: {e}")
    
    return counts

def main():
    """Función principal"""
    logger.info("🔍 Iniciando validación de estructura de base de datos de producción...")
    
    try:
        # Conectar a la base de datos
        conn = connect_to_db()
        logger.info("✅ Conectado a la base de datos de producción")
        
        # Verificar tablas principales
        tables = ['categorias', 'productos', 'ventas', 'detalle_ventas']
        logger.info("\n📊 VERIFICANDO TABLAS:")
        
        for table in tables:
            exists = table_exists(conn, table)
            logger.info(f"   - {table}: {'✅ EXISTE' if exists else '❌ NO EXISTE'}")
        
        # Obtener conteos
        logger.info("\n📈 CONTEOS DE REGISTROS:")
        counts = get_table_counts(conn)
        for table, count in counts.items():
            logger.info(f"   - {table}: {count}")
        
        # Verificar estructura de tabla ventas
        logger.info("\n🏗️ ESTRUCTURA DE TABLA VENTAS:")
        if table_exists(conn, 'ventas'):
            ventas_structure = get_table_structure(conn, 'ventas')
            for col in ventas_structure:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                logger.info(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        # Verificar si falta columna estado en ventas
        logger.info("\n🔧 VERIFICANDO COLUMNA 'estado' EN VENTAS:")
        if table_exists(conn, 'ventas'):
            if not column_exists(conn, 'ventas', 'estado'):
                logger.warning("⚠️ Columna 'estado' NO EXISTE en tabla ventas")
                logger.info("🔧 Agregando columna 'estado'...")
                add_column_if_not_exists(conn, 'ventas', 'estado', "VARCHAR(20) DEFAULT 'completada'")
            else:
                logger.info("✅ Columna 'estado' ya existe en ventas")
        
        # Verificar foreign keys
        logger.info("\n🔗 FOREIGN KEYS DE detalle_ventas:")
        if table_exists(conn, 'detalle_ventas'):
            fks = get_foreign_keys(conn, 'detalle_ventas')
            for fk in fks:
                logger.info(f"   - {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # Verificar registros huérfanos
        logger.info("\n🧹 VERIFICANDO REGISTROS HUÉRFANOS:")
        orphaned = check_orphaned_records(conn)
        
        if orphaned:
            respuesta = input("\n❓ ¿Deseas limpiar los registros huérfanos? (s/n): ")
            if respuesta.lower() in ['s', 'si', 'y', 'yes']:
                clean_orphaned_records(conn)
        
        # Conteos finales
        logger.info("\n📈 CONTEOS FINALES:")
        final_counts = get_table_counts(conn)
        for table, count in final_counts.items():
            logger.info(f"   - {table}: {count}")
        
        conn.close()
        logger.info("\n✅ Validación completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la validación: {e}")
        raise

if __name__ == "__main__":
    main()
