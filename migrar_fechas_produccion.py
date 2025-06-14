#!/usr/bin/env python3
"""
Script de migración de fechas a zona horaria México (UTC-6)
Para ejecutar directamente en la base de datos de producción PostgreSQL
Versión: 1.0.0
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zona horaria de México (UTC-6)
MEXICO_TZ = timezone(timedelta(hours=-6))

def get_db_connection():
    """Obtener conexión directa a la base de datos de producción"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("No se encontró DATABASE_URL en las variables de entorno")
        print("\nPor favor, ejecuta este comando con la URL de la base de datos:")
        print("DATABASE_URL='postgresql://...' python migrar_fechas_produccion.py")
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

def get_registros_para_migrar(conn) -> Dict[str, List[Dict[str, Any]]]:
    """Obtener todos los registros que necesitan migración de fecha"""
    registros = {}
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Ventas - columna 'fecha'
        cursor.execute("""
            SELECT id, fecha, total, vendedor 
            FROM ventas 
            ORDER BY fecha
        """)
        registros['ventas'] = [dict(row) for row in cursor.fetchall()]
        
        # Gastos diarios - columna 'fecha'
        cursor.execute("""
            SELECT id, fecha, concepto, monto, categoria 
            FROM gastos_diarios 
            ORDER BY fecha
        """)
        registros['gastos_diarios'] = [dict(row) for row in cursor.fetchall()]
        
        # Cortes de caja - columna 'fecha_registro'
        cursor.execute("""
            SELECT id, fecha_registro, dinero_inicial, dinero_final, vendedor 
            FROM cortes_caja 
            ORDER BY fecha_registro
        """)
        registros['cortes_caja'] = [dict(row) for row in cursor.fetchall()]
        
        # Vendedores - columna 'fecha_registro'
        cursor.execute("""
            SELECT id, nombre, fecha_registro 
            FROM vendedores 
            WHERE fecha_registro IS NOT NULL 
            ORDER BY fecha_registro
        """)
        registros['vendedores'] = [dict(row) for row in cursor.fetchall()]
    
    return registros

def mostrar_resumen_migracion(registros: Dict[str, List[Dict[str, Any]]]):
    """Mostrar resumen de registros a migrar"""
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE REGISTROS A MIGRAR")
    logger.info("="*60)
    
    total_registros = 0
    for tabla, datos in registros.items():
        cantidad = len(datos)
        total_registros += cantidad
        logger.info(f"📊 {tabla.upper()}: {cantidad} registros")
        
        if datos and cantidad > 0:
            # Mostrar rango de fechas
            if tabla == 'ventas':
                fechas = [r['fecha'] for r in datos]
            elif tabla == 'gastos_diarios':
                fechas = [r['fecha'] for r in datos]
            elif tabla == 'cortes_caja':
                fechas = [r['fecha_registro'] for r in datos if r['fecha_registro']]
            elif tabla == 'vendedores':
                fechas = [r['fecha_registro'] for r in datos if r['fecha_registro']]
            
            if fechas:
                min_fecha = min(fechas)
                max_fecha = max(fechas)
                logger.info(f"   📅 Rango: {min_fecha} → {max_fecha}")
    
    logger.info(f"\n🔢 TOTAL DE REGISTROS A MIGRAR: {total_registros}")
    logger.info("="*60)

def migrar_tabla_ventas(conn, registros: List[Dict[str, Any]]) -> int:
    """Migrar fechas de la tabla ventas"""
    if not registros:
        return 0
    
    logger.info("🔄 Migrando tabla VENTAS...")
    actualizados = 0
    
    with conn.cursor() as cursor:
        for venta in registros:
            fecha_utc = venta['fecha']
            
            # Si la fecha ya está en UTC, convertir a México
            if fecha_utc.tzinfo is None:
                # Asumir que es UTC
                fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
            
            # Convertir a zona horaria de México
            fecha_mexico = fecha_utc.astimezone(MEXICO_TZ)
            
            cursor.execute("""
                UPDATE ventas 
                SET fecha = %s 
                WHERE id = %s
            """, (fecha_mexico.replace(tzinfo=None), venta['id']))
            
            actualizados += 1
            
            if actualizados % 100 == 0:
                logger.info(f"   ✅ Procesadas {actualizados} ventas...")
    
    conn.commit()
    logger.info(f"✅ VENTAS: {actualizados} registros migrados")
    return actualizados

def migrar_tabla_gastos(conn, registros: List[Dict[str, Any]]) -> int:
    """Migrar fechas de la tabla gastos_diarios"""
    if not registros:
        return 0
    
    logger.info("🔄 Migrando tabla GASTOS_DIARIOS...")
    actualizados = 0
    
    with conn.cursor() as cursor:
        for gasto in registros:
            fecha_utc = gasto['fecha']
            
            # Si la fecha ya está en UTC, convertir a México
            if fecha_utc.tzinfo is None:
                # Asumir que es UTC
                fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
            
            # Convertir a zona horaria de México
            fecha_mexico = fecha_utc.astimezone(MEXICO_TZ)
            
            cursor.execute("""
                UPDATE gastos_diarios 
                SET fecha = %s 
                WHERE id = %s
            """, (fecha_mexico.replace(tzinfo=None), gasto['id']))
            
            actualizados += 1
    
    conn.commit()
    logger.info(f"✅ GASTOS_DIARIOS: {actualizados} registros migrados")
    return actualizados

def migrar_tabla_cortes(conn, registros: List[Dict[str, Any]]) -> int:
    """Migrar fechas de la tabla cortes_caja"""
    if not registros:
        return 0
    
    logger.info("🔄 Migrando tabla CORTES_CAJA...")
    actualizados = 0
    
    with conn.cursor() as cursor:
        for corte in registros:
            fecha_utc = corte['fecha_registro']
            
            # Si la fecha ya está en UTC, convertir a México
            if fecha_utc.tzinfo is None:
                # Asumir que es UTC
                fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
            
            # Convertir a zona horaria de México
            fecha_mexico = fecha_utc.astimezone(MEXICO_TZ)
            
            cursor.execute("""
                UPDATE cortes_caja 
                SET fecha_registro = %s 
                WHERE id = %s
            """, (fecha_mexico.replace(tzinfo=None), corte['id']))
            
            actualizados += 1
    
    conn.commit()
    logger.info(f"✅ CORTES_CAJA: {actualizados} registros migrados")
    return actualizados

def migrar_tabla_vendedores(conn, registros: List[Dict[str, Any]]) -> int:
    """Migrar fechas de la tabla vendedores"""
    if not registros:
        return 0
    
    logger.info("🔄 Migrando tabla VENDEDORES...")
    actualizados = 0
    
    with conn.cursor() as cursor:
        for vendedor in registros:
            fecha_utc = vendedor['fecha_registro']
            
            # Si la fecha ya está en UTC, convertir a México
            if fecha_utc.tzinfo is None:
                # Asumir que es UTC
                fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
            
            # Convertir a zona horaria de México
            fecha_mexico = fecha_utc.astimezone(MEXICO_TZ)
            
            cursor.execute("""
                UPDATE vendedores 
                SET fecha_registro = %s 
                WHERE id = %s
            """, (fecha_mexico.replace(tzinfo=None), vendedor['id']))
            
            actualizados += 1
    
    conn.commit()
    logger.info(f"✅ VENDEDORES: {actualizados} registros migrados")
    return actualizados

def verificar_migracion(conn):
    """Verificar que la migración se ejecutó correctamente"""
    logger.info("\n🔍 Verificando migración...")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Verificar algunas ventas recientes
        cursor.execute("""
            SELECT fecha, total 
            FROM ventas 
            ORDER BY fecha DESC 
            LIMIT 5
        """)
        ventas_recientes = cursor.fetchall()
        
        if ventas_recientes:
            logger.info("📊 Últimas 5 ventas (fechas migradas):")
            for venta in ventas_recientes:
                logger.info(f"   📅 {venta['fecha']} - ${venta['total']}")
        
        # Verificar gastos recientes
        cursor.execute("""
            SELECT fecha, concepto, monto 
            FROM gastos_diarios 
            ORDER BY fecha DESC 
            LIMIT 3
        """)
        gastos_recientes = cursor.fetchall()
        
        if gastos_recientes:
            logger.info("💰 Últimos 3 gastos (fechas migradas):")
            for gasto in gastos_recientes:
                logger.info(f"   📅 {gasto['fecha']} - {gasto['concepto']} - ${gasto['monto']}")
        
        # Verificar vendedores
        cursor.execute("""
            SELECT nombre, fecha_registro 
            FROM vendedores 
            ORDER BY fecha_registro DESC 
            LIMIT 3
        """)
        vendedores_recientes = cursor.fetchall()
        
        if vendedores_recientes:
            logger.info("👥 Últimos vendedores registrados (fechas migradas):")
            for vendedor in vendedores_recientes:
                logger.info(f"   📅 {vendedor['fecha_registro']} - {vendedor['nombre']}")

def main():
    """Función principal del script de migración"""
    logger.info("🚀 INICIANDO MIGRACIÓN DE FECHAS A ZONA HORARIA MÉXICO")
    logger.info(f"⏰ Fecha/hora actual de migración: {datetime.now()}")
    
    # Conectar a la base de datos
    conn = get_db_connection()
    
    try:
        # Obtener registros para migrar
        logger.info("📋 Obteniendo registros de la base de datos...")
        registros = get_registros_para_migrar(conn)
        
        # Mostrar resumen
        mostrar_resumen_migracion(registros)
        
        # Pedir confirmación
        print("\n" + "="*60)
        respuesta = input("¿Continuar con la migración? (escribe 'SI' para confirmar): ")
        
        if respuesta.upper() != 'SI':
            logger.info("❌ Migración cancelada por el usuario")
            return
        
        # Ejecutar migración
        logger.info("\n🔄 INICIANDO PROCESO DE MIGRACIÓN...")
        total_migrados = 0
        
        total_migrados += migrar_tabla_ventas(conn, registros['ventas'])
        total_migrados += migrar_tabla_gastos(conn, registros['gastos_diarios'])
        total_migrados += migrar_tabla_cortes(conn, registros['cortes_caja'])
        total_migrados += migrar_tabla_vendedores(conn, registros['vendedores'])
        
        # Verificar migración
        verificar_migracion(conn)
        
        # Resumen final
        logger.info("\n" + "="*60)
        logger.info("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info(f"📊 Total de registros migrados: {total_migrados}")
        logger.info("🌎 Todas las fechas ahora están en hora de México (UTC-6)")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
