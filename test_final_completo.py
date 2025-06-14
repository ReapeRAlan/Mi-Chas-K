#!/usr/bin/env python3
"""
Prueba final del flujo completo de venta con fecha correcta
"""
import os
import sys
sys.path.append('/home/ghost/Escritorio/CHASKAS/Mi-Chas-K')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar las clases del sistema
from database.models import Producto, Carrito, ItemCarrito

def get_db_connection():
    """Obtener conexión directa a la base de datos de producción"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("No se encontró DATABASE_URL")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Error conectando: {e}")
        return None

def test_flujo_completo():
    """Probar el flujo completo usando las clases del sistema"""
    logger.info("🧪 PRUEBA FINAL DEL FLUJO COMPLETO")
    logger.info("="*60)
    
    try:
        # 1. Obtener productos
        logger.info("📦 Obteniendo productos...")
        productos = Producto.get_all()
        
        if not productos:
            logger.error("❌ No hay productos disponibles")
            return False
        
        producto = productos[0]
        logger.info(f"✅ Producto seleccionado: {producto.nombre} - ${producto.precio}")
        
        # 2. Crear carrito y agregar producto
        logger.info("🛒 Creando carrito...")
        carrito = Carrito()
        
        item = ItemCarrito(producto=producto, cantidad=1)
        carrito.agregar_item(item)
        
        logger.info(f"✅ Carrito creado - Total: ${carrito.total}")
        
        # 3. Procesar venta (aquí debe usar la fecha correcta)
        logger.info("💳 Procesando venta...")
        
        venta = carrito.procesar_venta(
            metodo_pago="Efectivo",
            vendedor="PRUEBA_FINAL",
            observaciones="Prueba final del sistema con fecha correcta"
        )
        
        if venta and venta.id:
            logger.info(f"✅ Venta procesada exitosamente:")
            logger.info(f"   ID: #{venta.id}")
            logger.info(f"   Total: ${venta.total}")
            logger.info(f"   Fecha: {venta.fecha}")
            logger.info(f"   Vendedor: {venta.vendedor}")
            
            # 4. Verificar en base de datos
            conn = get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM ventas WHERE id = %s", (venta.id,))
                    venta_db = cursor.fetchone()
                    
                    if venta_db:
                        fecha_db = venta_db['fecha']
                        logger.info(f"🔍 Verificación en BD:")
                        logger.info(f"   Fecha en BD: {fecha_db}")
                        
                        # Verificar que es fecha de México (13 junio, hora 20+)
                        es_fecha_correcta = (
                            fecha_db.year == 2025 and
                            fecha_db.month == 6 and
                            fecha_db.day == 13 and
                            fecha_db.hour >= 20  # Debe ser después de las 8 PM
                        )
                        
                        if es_fecha_correcta:
                            logger.info("🎉 ✅ FECHA CORRECTA - 13 de junio 2025, hora México")
                            return True
                        else:
                            logger.error(f"❌ FECHA INCORRECTA - Esperado: 13-jun-2025 20:xx, Obtenido: {fecha_db}")
                            return False
                
                conn.close()
            
            return True
        else:
            logger.error("❌ Error al procesar la venta")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    success = test_flujo_completo()
    
    logger.info("="*60)
    if success:
        logger.info("🎉 PRUEBA EXITOSA - SISTEMA FUNCIONANDO CORRECTAMENTE")
    else:
        logger.info("💥 PRUEBA FALLÓ - REVISAR CONFIGURACIÓN")
    
    return success

if __name__ == "__main__":
    main()
