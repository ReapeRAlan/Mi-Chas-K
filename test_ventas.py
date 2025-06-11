#!/usr/bin/env python3
"""
Script para probar las ventas y generar datos de prueba
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Venta, DetalleVenta, Producto
from database.connection import execute_update

def crear_venta_prueba():
    """Crea una venta de prueba para probar el sistema"""
    print("🛒 Creando venta de prueba...")
    
    # Obtener algunos productos
    productos = Producto.get_all()
    if len(productos) < 3:
        print("❌ No hay suficientes productos en la base de datos")
        return None
    
    # Crear una venta
    venta = Venta(
        total=0.0,
        metodo_pago="Efectivo",
        fecha=datetime.now(),
        vendedor="Sistema",
        observaciones="Venta de prueba"
    )
    
    # Calcular total y crear detalles
    detalles = []
    total_venta = 0.0
    
    # Agregar 3 productos aleatorios
    for i, producto in enumerate(productos[:3]):
        cantidad = i + 1  # 1, 2, 3
        subtotal = cantidad * producto.precio
        total_venta += subtotal
        
        detalle = DetalleVenta(
            venta_id=0,  # Se asignará después
            producto_id=producto.id or 0,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            subtotal=subtotal
        )
        detalles.append(detalle)
    
    venta.total = total_venta
    
    # Guardar venta
    venta_id = venta.save()
    print(f"✅ Venta creada con ID: {venta_id}")
    
    # Guardar detalles
    for detalle in detalles:
        detalle.venta_id = venta_id
        detalle.save()
        producto_info = Producto.get_by_id(detalle.producto_id)
        nombre_producto = producto_info.nombre if producto_info else "Producto desconocido"
        print(f"  - {detalle.cantidad}x {nombre_producto}")
    
    print(f"💰 Total de la venta: ${total_venta:.2f} MXN")
    return venta_id

def crear_multiples_ventas():
    """Crea múltiples ventas para poblar el dashboard"""
    print("📊 Creando múltiples ventas para el dashboard...")
    
    # Crear 5 ventas de prueba
    for i in range(5):
        venta_id = crear_venta_prueba()
        if venta_id:
            print(f"Venta {i+1} creada")
    
    print("✅ Ventas de prueba creadas exitosamente")

def probar_pdf():
    """Prueba la generación de PDF"""
    from utils.pdf_generator import TicketGenerator
    
    print("🧾 Probando generación de tickets PDF...")
    
    # Obtener la última venta
    ventas = Venta.get_all()
    if not ventas:
        print("❌ No hay ventas para generar ticket")
        return
    
    venta = ventas[0]  # La más reciente
    
    try:
        generator = TicketGenerator()
        ruta_ticket = generator.generar_ticket(venta)
        print(f"✅ Ticket generado: {ruta_ticket}")
        return ruta_ticket
    except Exception as e:
        print(f"❌ Error al generar ticket: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Sistema MiChaska")
    print("=" * 50)
    
    # Crear ventas de prueba
    crear_multiples_ventas()
    
    print("\n" + "=" * 50)
    
    # Probar PDF
    probar_pdf()
    
    print("\n✅ Pruebas completadas")
