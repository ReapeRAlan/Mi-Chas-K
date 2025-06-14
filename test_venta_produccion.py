#!/usr/bin/env python3
"""
Script para probar una venta directamente en la base de datos de producción
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

def crear_venta_prueba(conn):
    """Crear una venta de prueba directamente en la base de datos"""
    logger.info("🧪 Creando venta de prueba...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Obtener algunos productos
            cursor.execute("SELECT * FROM productos WHERE activo = TRUE LIMIT 3")
            productos = cursor.fetchall()
            
            if not productos:
                logger.error("❌ No hay productos disponibles")
                return False
            
            logger.info(f"📦 Productos disponibles: {len(productos)}")
            
            # Crear fecha/hora de México
            from datetime import datetime, timezone, timedelta
            mexico_tz = timezone(timedelta(hours=-6))
            fecha_mexico = datetime.now(mexico_tz)
            
            # Crear venta
            producto = productos[0]
            total_venta = float(producto['precio'])
            
            cursor.execute("""
                INSERT INTO ventas (total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (total_venta, "Efectivo", 0.0, 0.0, fecha_mexico.replace(tzinfo=None), "PRUEBA_SCRIPT", "Venta de prueba desde script"))
            
            venta_result = cursor.fetchone()
            venta_id = venta_result['id']
            
            logger.info(f"✅ Venta #{venta_id} creada - Total: ${total_venta}")
            
            # Crear detalle de venta
            cursor.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (venta_id, producto['id'], 1, float(producto['precio']), total_venta))
            
            logger.info(f"✅ Detalle de venta creado para producto: {producto['nombre']}")
            
            # Actualizar stock
            nuevo_stock = producto['stock'] - 1
            cursor.execute("""
                UPDATE productos SET stock = %s WHERE id = %s
            """, (nuevo_stock, producto['id']))
            
            logger.info(f"✅ Stock actualizado: {producto['stock']} → {nuevo_stock}")
            
            # Confirmar transacción
            conn.commit()
            
            logger.info(f"🎉 VENTA DE PRUEBA COMPLETADA EXITOSAMENTE!")
            logger.info(f"   ID: #{venta_id}")
            logger.info(f"   Producto: {producto['nombre']}")
            logger.info(f"   Total: ${total_venta}")
            logger.info(f"   Fecha: {fecha_mexico}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando venta de prueba: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False

def verificar_venta_reciente(conn):
    """Verificar las ventas más recientes"""
    logger.info("\n🔍 Verificando ventas recientes...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT v.id, v.total, v.vendedor, v.fecha, v.observaciones,
                       p.nombre as producto_nombre
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                ORDER BY v.fecha DESC
                LIMIT 5
            """)
            ventas = cursor.fetchall()
            
            if ventas:
                logger.info("📊 Últimas 5 ventas:")
                for venta in ventas:
                    logger.info(f"   #{venta['id']} | {venta['fecha']} | ${venta['total']} | {venta['vendedor']} | {venta['producto_nombre']} | {venta['observaciones']}")
            else:
                logger.info("📊 No hay ventas recientes")
                
    except Exception as e:
        logger.error(f"❌ Error verificando ventas: {e}")

def main():
    """Función principal"""
    logger.info("🚀 PRUEBA DE VENTA EN PRODUCCIÓN")
    logger.info("="*60)
    
    conn = get_db_connection()
    
    try:
        # Verificar ventas antes
        verificar_venta_reciente(conn)
        
        # Crear venta de prueba
        success = crear_venta_prueba(conn)
        
        # Verificar ventas después
        verificar_venta_reciente(conn)
        
        logger.info("="*60)
        if success:
            logger.info("🎉 PRUEBA DE VENTA EXITOSA")
        else:
            logger.info("💥 PRUEBA DE VENTA FALLÓ")
            
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
