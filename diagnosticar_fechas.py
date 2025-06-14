#!/usr/bin/env python3
"""
Script para diagnosticar el problema de fechas en PostgreSQL
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
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
        conn.autocommit = False
        logger.info("✅ Conexión establecida exitosamente")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)

def verificar_estructura_ventas(conn):
    """Verificar la estructura de la tabla ventas"""
    logger.info("🔍 Verificando estructura de tabla ventas...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Ver la definición de la tabla
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'ventas' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        columnas = cursor.fetchall()
        
        logger.info("📋 Estructura de tabla 'ventas':")
        for col in columnas:
            default = col['column_default'] or 'NULL'
            logger.info(f"   📝 {col['column_name']}: {col['data_type']} | Default: {default}")

def verificar_triggers(conn):
    """Verificar si hay triggers en la tabla ventas"""
    logger.info("\n🔍 Verificando triggers en tabla ventas...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT trigger_name, event_manipulation, action_timing, action_statement
            FROM information_schema.triggers 
            WHERE event_object_table = 'ventas'
        """)
        triggers = cursor.fetchall()
        
        if triggers:
            logger.info("⚠️ Triggers encontrados:")
            for trigger in triggers:
                logger.info(f"   🎯 {trigger['trigger_name']}: {trigger['event_manipulation']} {trigger['action_timing']}")
                logger.info(f"      Action: {trigger['action_statement']}")
        else:
            logger.info("✅ No hay triggers en la tabla ventas")

def test_insert_directo(conn):
    """Probar insertar una venta directamente con fecha específica"""
    logger.info("\n🧪 Probando INSERT directo con fecha específica...")
    
    try:
        # Fecha específica de México
        fecha_mexico = datetime(2025, 6, 13, 20, 15, 0)  # 13 jun 2025, 8:15 PM
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Insertar con fecha específica
            cursor.execute("""
                INSERT INTO ventas (total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, fecha
            """, (99.99, "PRUEBA", 0.0, 0.0, fecha_mexico, "TEST_FECHA", "Prueba de fecha específica"))
            
            resultado = cursor.fetchone()
            venta_id = resultado['id']
            fecha_guardada = resultado['fecha']
            
            logger.info(f"✅ Venta de prueba creada:")
            logger.info(f"   ID: #{venta_id}")
            logger.info(f"   Fecha enviada: {fecha_mexico}")
            logger.info(f"   Fecha guardada: {fecha_guardada}")
            
            # Verificar si son iguales
            if isinstance(fecha_guardada, datetime):
                diferencia = fecha_guardada - fecha_mexico
                logger.info(f"   Diferencia: {diferencia.total_seconds()} segundos")
                
                if diferencia.total_seconds() == 0:
                    logger.info("   ✅ FECHA GUARDADA CORRECTAMENTE")
                else:
                    logger.info("   ⚠️ FECHA MODIFICADA AL GUARDAR")
            
            # Verificar zona horaria de PostgreSQL
            cursor.execute("SHOW timezone;")
            pg_timezone = cursor.fetchone()['timezone']
            logger.info(f"   🌍 Zona horaria PostgreSQL: {pg_timezone}")
            
            # Confirmar cambios
            conn.commit()
            
            return venta_id, fecha_guardada
            
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        conn.rollback()
        return None, None

def verificar_ventas_recientes(conn):
    """Verificar las últimas ventas para ver el patrón"""
    logger.info("\n📊 Verificando últimas ventas...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, fecha, total, vendedor, observaciones
            FROM ventas 
            ORDER BY id DESC 
            LIMIT 5
        """)
        ventas = cursor.fetchall()
        
        logger.info("📋 Últimas 5 ventas:")
        for venta in ventas:
            fecha_str = venta['fecha'].strftime('%Y-%m-%d %H:%M:%S') if venta['fecha'] else 'NULL'
            logger.info(f"   #{venta['id']} | {fecha_str} | ${venta['total']} | {venta['vendedor']}")

def main():
    """Función principal"""
    logger.info("🔍 DIAGNÓSTICO DE PROBLEMA DE FECHAS")
    logger.info("="*60)
    
    conn = get_db_connection()
    
    try:
        verificar_estructura_ventas(conn)
        verificar_triggers(conn)
        verificar_ventas_recientes(conn)
        
        venta_id, fecha_guardada = test_insert_directo(conn)
        
        if venta_id:
            logger.info(f"\n🎯 RESULTADO: Venta #{venta_id} con fecha {fecha_guardada}")
        
        logger.info("="*60)
        logger.info("🔍 DIAGNÓSTICO COMPLETADO")
        
    except Exception as e:
        logger.error(f"❌ Error durante el diagnóstico: {e}")
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
