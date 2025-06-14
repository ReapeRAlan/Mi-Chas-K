#!/usr/bin/env python3
"""
Script de prueba para verificar el procesamiento de ventas
"""
import sys
import os
sys.path.append('/home/ghost/Escritorio/CHASKAS/Mi-Chas-K')

from database.models import Producto, Carrito, ItemCarrito
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_venta_simple():
    """Prueba básica de creación de venta"""
    logger.info("🧪 Iniciando prueba de venta simple...")
    
    try:
        # Obtener algunos productos
        productos = Producto.get_all()
        if not productos:
            logger.error("❌ No hay productos disponibles")
            return False
        
        logger.info(f"📦 Productos disponibles: {len(productos)}")
        
        # Crear carrito
        carrito = Carrito()
        
        # Agregar un producto al carrito
        producto = productos[0]
        logger.info(f"🛒 Agregando producto: {producto.nombre} - ${producto.precio}")
        
        item = ItemCarrito(producto=producto, cantidad=1)
        carrito.agregar_item(item)
        
        logger.info(f"💰 Total del carrito: ${carrito.total}")
        
        # Procesar venta
        logger.info("💳 Procesando venta...")
        venta = carrito.procesar_venta(
            metodo_pago="Efectivo",
            vendedor="TEST",
            observaciones="Prueba desde script"
        )
        
        if venta and venta.id:
            logger.info(f"✅ Venta #{venta.id} procesada exitosamente!")
            logger.info(f"   Total: ${venta.total}")
            logger.info(f"   Vendedor: {venta.vendedor}")
            logger.info(f"   Fecha: {venta.fecha}")
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
    logger.info("🚀 INICIANDO PRUEBAS DE VENTA")
    logger.info("="*50)
    
    success = test_venta_simple()
    
    logger.info("="*50)
    if success:
        logger.info("🎉 TODAS LAS PRUEBAS PASARON")
    else:
        logger.info("💥 ALGUNAS PRUEBAS FALLARON")
    
    return success

if __name__ == "__main__":
    main()
