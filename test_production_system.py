#!/usr/bin/env python3
"""
Script para probar funcionalidades críticas del sistema con la base de datos de producción
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Producto, Venta, DetalleVenta, Vendedor
from database.connection import execute_query, execute_update, init_database
from utils.timezone_utils import get_mexico_datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_queries():
    """Probar consultas básicas"""
    logger.info("🧪 Probando consultas básicas...")
    
    try:
        # Probar obtener productos
        productos = Producto.get_all()
        logger.info(f"✅ Productos obtenidos: {len(productos)}")
        
        # Probar obtener ventas
        ventas = Venta.get_all()
        logger.info(f"✅ Ventas obtenidas: {len(ventas)}")
        
        # Probar obtener vendedores
        vendedores = Vendedor.get_all()
        logger.info(f"✅ Vendedores obtenidos: {len(vendedores)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en consultas básicas: {e}")
        return False

def test_venta_creation():
    """Probar creación de venta con fecha personalizada"""
    logger.info("🧪 Probando creación de venta...")
    
    try:
        # Obtener un producto para la prueba
        productos = Producto.get_all()
        if not productos:
            logger.error("❌ No hay productos disponibles para la prueba")
            return False
        
        producto = productos[0]
        
        # Crear una venta de prueba
        fecha_custom = get_mexico_datetime() - timedelta(days=1)  # Ayer
        venta_id = Venta.procesar_venta(
            productos=[{"id": producto.id, "cantidad": 1, "precio": producto.precio}],
            total=producto.precio,
            metodo_pago="Efectivo",
            vendedor="Test",
            descuento=0,
            fecha_personalizada=fecha_custom
        )
        
        if venta_id:
            logger.info(f"✅ Venta de prueba creada con ID: {venta_id}")
            
            # Eliminar la venta de prueba
            execute_update("DELETE FROM detalle_ventas WHERE venta_id = %s", (venta_id,))
            execute_update("DELETE FROM ventas WHERE id = %s", (venta_id,))
            
            # Restaurar stock
            execute_update("UPDATE productos SET stock = stock + 1 WHERE id = %s", (producto.id,))
            
            logger.info("✅ Venta de prueba eliminada")
            return True
        else:
            logger.error("❌ No se pudo crear la venta de prueba")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando creación de venta: {e}")
        return False

def test_database_structure():
    """Probar estructura de base de datos"""
    logger.info("🧪 Probando estructura de base de datos...")
    
    try:
        # Verificar que todas las columnas necesarias existen
        test_queries = [
            "SELECT id, total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones, estado FROM ventas LIMIT 1",
            "SELECT id, venta_id, producto_id, cantidad, precio_unitario, subtotal FROM detalle_ventas LIMIT 1",
            "SELECT id, nombre, precio, stock, categoria, activo FROM productos LIMIT 1"
        ]
        
        for query in test_queries:
            result = execute_query(query)
            logger.info(f"✅ Query exitosa: {query.split('FROM')[1].split('LIMIT')[0].strip()}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en estructura de base de datos: {e}")
        return False

def test_foreign_keys():
    """Probar integridad de foreign keys"""
    logger.info("🧪 Probando integridad de foreign keys...")
    
    try:
        # Verificar que no hay registros huérfanos
        orphaned_query = """
            SELECT COUNT(*) as count FROM detalle_ventas dv 
            LEFT JOIN ventas v ON dv.venta_id = v.id 
            WHERE v.id IS NULL
        """
        result = execute_query(orphaned_query)
        orphaned_count = result[0]['count'] if result else 0
        
        if orphaned_count == 0:
            logger.info("✅ No se encontraron registros huérfanos en detalle_ventas")
            return True
        else:
            logger.warning(f"⚠️ Se encontraron {orphaned_count} registros huérfanos en detalle_ventas")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando foreign keys: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando pruebas del sistema...")
    
    try:
        # Inicializar base de datos
        init_database()
        logger.info("✅ Base de datos inicializada")
        
        # Ejecutar pruebas
        tests = [
            ("Consultas básicas", test_basic_queries),
            ("Estructura de base de datos", test_database_structure),
            ("Integridad de foreign keys", test_foreign_keys),
            ("Creación de venta", test_venta_creation),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            result = test_func()
            results.append((test_name, result))
        
        # Mostrar resumen
        logger.info("\n📊 RESUMEN DE PRUEBAS:")
        all_passed = True
        for test_name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            logger.info(f"   - {test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("\n🎉 TODAS LAS PRUEBAS PASARON")
        else:
            logger.warning("\n⚠️ ALGUNAS PRUEBAS FALLARON")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Error general en las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
