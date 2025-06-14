#!/usr/bin/env python3
"""
Prueba completa de venta con la lógica exacta de la aplicación
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simular la función get_mexico_datetime()
def get_mexico_datetime_simple():
    """Función simplificada para obtener hora México"""
    from datetime import datetime, timezone, timedelta
    
    # UTC actual
    utc_now = datetime.now(timezone.utc)
    
    # Convertir a México (UTC-6)
    mexico_tz = timezone(timedelta(hours=-6))
    mexico_time = utc_now.astimezone(mexico_tz)
    
    # Devolver sin timezone info para PostgreSQL
    return mexico_time.replace(tzinfo=None)

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

def simular_venta_completa(conn):
    """Simular el flujo completo de una venta como lo hace la aplicación"""
    logger.info("🛒 Simulando venta completa...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. Obtener productos (como el carrito)
            cursor.execute("SELECT * FROM productos WHERE activo = TRUE AND stock > 0 LIMIT 1")
            producto = cursor.fetchone()
            
            if not producto:
                logger.error("❌ No hay productos disponibles")
                return False
            
            logger.info(f"📦 Producto seleccionado: {producto['nombre']} - ${producto['precio']}")
            
            # 2. Crear fecha México como lo hace la aplicación
            fecha_venta = get_mexico_datetime_simple()
            logger.info(f"🕐 Fecha de venta: {fecha_venta}")
            
            # 3. Simular datos del carrito
            cantidad = 1
            precio_unitario = float(producto['precio'])
            subtotal = cantidad * precio_unitario
            total_venta = subtotal
            
            # 4. Crear venta (como models.Venta.save())
            query_venta = """
                INSERT INTO ventas (total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params_venta = (total_venta, "Efectivo", 0.0, 0.0, fecha_venta, "PRUEBA_COMPLETA", "Simulación completa del flujo")
            
            cursor.execute(query_venta, params_venta)
            venta_result = cursor.fetchone()
            venta_id = venta_result['id']
            
            logger.info(f"✅ Venta #{venta_id} creada con fecha: {fecha_venta}")
            
            # 5. Crear detalle de venta
            query_detalle = """
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            params_detalle = (venta_id, producto['id'], cantidad, precio_unitario, subtotal)
            cursor.execute(query_detalle, params_detalle)
            
            logger.info(f"✅ Detalle creado: {cantidad}x {producto['nombre']}")
            
            # 6. Actualizar stock
            nuevo_stock = producto['stock'] - cantidad
            query_stock = "UPDATE productos SET stock = %s WHERE id = %s"
            cursor.execute(query_stock, (nuevo_stock, producto['id']))
            
            logger.info(f"✅ Stock actualizado: {producto['stock']} → {nuevo_stock}")
            
            # 7. Confirmar transacción
            conn.commit()
            
            # 8. Verificar la venta creada
            cursor.execute("SELECT * FROM ventas WHERE id = %s", (venta_id,))
            venta_verificada = cursor.fetchone()
            
            logger.info(f"\n🎉 VENTA COMPLETADA:")
            logger.info(f"   ID: #{venta_verificada['id']}")
            logger.info(f"   Total: ${venta_verificada['total']}")
            logger.info(f"   Fecha guardada: {venta_verificada['fecha']}")
            logger.info(f"   Vendedor: {venta_verificada['vendedor']}")
            logger.info(f"   Método: {venta_verificada['metodo_pago']}")
            
            # 9. Verificar que la fecha es correcta
            fecha_guardada = venta_verificada['fecha']
            if isinstance(fecha_guardada, datetime):
                es_fecha_correcta = (
                    fecha_guardada.year == 2025 and 
                    fecha_guardada.month == 6 and 
                    fecha_guardada.day == 13 and
                    fecha_guardada.hour >= 19  # Debe ser después de las 7 PM
                )
                
                logger.info(f"✅ Verificación de fecha: {'CORRECTA' if es_fecha_correcta else 'INCORRECTA'}")
                logger.info(f"   Esperado: 2025-06-13 19:xx:xx")
                logger.info(f"   Obtenido: {fecha_guardada}")
                
                return es_fecha_correcta
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error en simulación: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    logger.info("🧪 SIMULACIÓN COMPLETA DE VENTA")
    logger.info("="*60)
    
    # Mostrar información de hora actual
    fecha_actual = get_mexico_datetime_simple()
    logger.info(f"🕐 Hora actual México: {fecha_actual}")
    
    conn = get_db_connection()
    
    try:
        success = simular_venta_completa(conn)
        
        logger.info("="*60)
        if success:
            logger.info("🎉 SIMULACIÓN EXITOSA - Fecha correcta")
        else:
            logger.info("💥 SIMULACIÓN FALLÓ - Problema con fecha")
            
    except Exception as e:
        logger.error(f"❌ Error durante la simulación: {e}")
        raise
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()
