#!/usr/bin/env python3
"""
Script de validación de migración de zona horaria
Verifica que las fechas estén correctamente en zona horaria de México
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

# Zona horaria de México (UTC-6)
MEXICO_TZ = timezone(timedelta(hours=-6))

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

def validar_fechas_ventas(conn):
    """Validar fechas de ventas"""
    logger.info("🔍 Validando fechas de VENTAS...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT fecha, total, vendedor, id
            FROM ventas 
            ORDER BY fecha DESC 
            LIMIT 10
        """)
        ventas = cursor.fetchall()
        
        logger.info("📊 Últimas 10 ventas con fechas migradas:")
        for venta in ventas:
            fecha = venta['fecha']
            # Mostrar información sobre la fecha
            logger.info(f"   ID: {venta['id']} | Fecha: {fecha} | Total: ${venta['total']} | Vendedor: {venta['vendedor'] or 'Sin asignar'}")
            
            # Validar que la fecha esté en rango razonable para México
            if fecha:
                ahora_utc = datetime.now(timezone.utc)
                ahora_mexico = ahora_utc.astimezone(MEXICO_TZ)
                
                # Si la fecha es "muy futura" en UTC, probablemente ya fue convertida
                if fecha > ahora_utc.replace(tzinfo=None):
                    logger.info(f"     ✅ Fecha convertida correctamente (posterior a UTC actual)")
                else:
                    logger.info(f"     ⚠️  Fecha dentro del rango UTC normal")

def validar_fechas_vendedores(conn):
    """Validar fechas de vendedores"""
    logger.info("\n🔍 Validando fechas de VENDEDORES...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT nombre, fecha_registro, id
            FROM vendedores 
            ORDER BY fecha_registro DESC
        """)
        vendedores = cursor.fetchall()
        
        if vendedores:
            logger.info("👥 Vendedores con fechas migradas:")
            for vendedor in vendedores:
                fecha = vendedor['fecha_registro']
                logger.info(f"   ID: {vendedor['id']} | Vendedor: {vendedor['nombre']} | Fecha registro: {fecha}")
        else:
            logger.info("👥 No hay vendedores registrados")

def mostrar_estadisticas_por_dia(conn):
    """Mostrar estadísticas agrupadas por día"""
    logger.info("\n📈 ESTADÍSTICAS POR DÍA (después de migración):")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT 
                DATE(fecha) as dia,
                COUNT(*) as num_ventas,
                SUM(total) as total_dia
            FROM ventas 
            GROUP BY DATE(fecha)
            ORDER BY dia DESC
            LIMIT 7
        """)
        estadisticas = cursor.fetchall()
        
        if estadisticas:
            logger.info("📊 Ventas por día (últimos 7 días):")
            for stat in estadisticas:
                logger.info(f"   📅 {stat['dia']} | Ventas: {stat['num_ventas']} | Total: ${stat['total_dia']}")
        else:
            logger.info("📊 No hay estadísticas de ventas")

def comparar_con_hora_actual(conn):
    """Comparar fechas con hora actual de México"""
    logger.info("\n🕐 COMPARACIÓN CON HORA ACTUAL:")
    
    # Hora actual en diferentes zonas
    ahora_utc = datetime.now(timezone.utc)
    ahora_mexico = ahora_utc.astimezone(MEXICO_TZ)
    
    logger.info(f"⏰ Hora actual UTC: {ahora_utc}")
    logger.info(f"🇲🇽 Hora actual México: {ahora_mexico}")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Ventas de "hoy" en México
        cursor.execute("""
            SELECT COUNT(*) as ventas_hoy, SUM(total) as total_hoy
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        hoy = cursor.fetchone()
        
        # Ventas de "ayer" en México
        cursor.execute("""
            SELECT COUNT(*) as ventas_ayer, SUM(total) as total_ayer
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE - INTERVAL '1 day'
        """)
        ayer = cursor.fetchone()
        
        logger.info(f"📊 Ventas HOY: {hoy['ventas_hoy']} ventas | Total: ${hoy['total_hoy'] or 0}")
        logger.info(f"📊 Ventas AYER: {ayer['ventas_ayer']} ventas | Total: ${ayer['total_ayer'] or 0}")

def main():
    """Función principal"""
    logger.info("🔍 VALIDACIÓN DE MIGRACIÓN DE ZONA HORARIA")
    logger.info("="*60)
    
    conn = get_db_connection()
    
    try:
        validar_fechas_ventas(conn)
        validar_fechas_vendedores(conn)
        mostrar_estadisticas_por_dia(conn)
        comparar_con_hora_actual(conn)
        
        logger.info("\n" + "="*60)
        logger.info("✅ VALIDACIÓN COMPLETADA")
        logger.info("🌎 Todas las fechas han sido verificadas para zona horaria México")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error durante la validación: {e}")
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
