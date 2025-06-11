#!/usr/bin/env python3
"""
Script para probar el flujo completo de venta y generación de tickets
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Venta, DetalleVenta, Producto, Carrito
from utils.pdf_generator import TicketGenerator

def test_venta_completa():
    """Prueba el flujo completo de una venta"""
    print("🧪 Probando flujo completo de venta...")
    
    # 1. Crear carrito
    carrito = Carrito()
    
    # 2. Agregar productos al carrito
    productos = Producto.get_all()[:3]  # Tomar los primeros 3 productos
    
    for i, producto in enumerate(productos):
        cantidad = i + 1  # 1, 2, 3
        print(f"  📦 Agregando {cantidad}x {producto.nombre}")
        carrito.agregar_producto(producto, cantidad)
    
    print(f"  💰 Total del carrito: ${carrito.total:.2f} MXN")
    
    # 3. Procesar venta
    print("  💳 Procesando venta...")
    venta = carrito.procesar_venta(
        metodo_pago="Efectivo",
        vendedor="Prueba",
        observaciones="Venta de prueba completa"
    )
    
    if not venta:
        print("  ❌ Error al procesar venta")
        return None
    
    print(f"  ✅ Venta #{venta.id} procesada exitosamente")
    
    # 4. Generar ticket
    print("  🧾 Generando ticket...")
    try:
        generator = TicketGenerator()
        ruta_ticket = generator.generar_ticket(venta)
        print(f"  ✅ Ticket generado: {ruta_ticket}")
        
        # Verificar que el archivo existe
        if os.path.exists(ruta_ticket):
            size = os.path.getsize(ruta_ticket)
            print(f"  📄 Archivo PDF creado - Tamaño: {size} bytes")
            return ruta_ticket
        else:
            print("  ❌ El archivo PDF no se creó")
            return None
            
    except Exception as e:
        print(f"  ❌ Error al generar ticket: {str(e)}")
        return None

def test_ticket_existente():
    """Prueba generar ticket de una venta existente"""
    print("\n🧪 Probando ticket de venta existente...")
    
    ventas = Venta.get_all()
    if not ventas:
        print("  ❌ No hay ventas en la base de datos")
        return None
    
    venta = ventas[0]  # Tomar la primera venta
    print(f"  🔍 Usando venta #{venta.id} - Total: ${venta.total:.2f}")
    
    try:
        generator = TicketGenerator()
        ruta_ticket = generator.generar_ticket(venta)
        print(f"  ✅ Ticket generado: {ruta_ticket}")
        return ruta_ticket
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧾 Testing Generación de Tickets")
    print("=" * 50)
    
    # Probar venta completa
    ticket1 = test_venta_completa()
    
    # Probar ticket de venta existente
    ticket2 = test_ticket_existente()
    
    print("\n" + "=" * 50)
    print("📋 Resumen de pruebas:")
    print(f"  Venta nueva: {'✅ OK' if ticket1 else '❌ FALLO'}")
    print(f"  Venta existente: {'✅ OK' if ticket2 else '❌ FALLO'}")
    
    if ticket1 or ticket2:
        print("\n📁 Archivos generados en la carpeta 'tickets/'")
        print("💡 Puedes abrir los PDF para verificar el contenido")
    
    print("\n✅ Pruebas completadas")
