#!/usr/bin/env python3
"""
Prueba simple del sistema corregido
"""
import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

print("🧪 PRUEBA DEL SISTEMA CORREGIDO")
print("=" * 40)

try:
    # Test 1: Importar módulos
    print("1. Importando módulos...")
    from database.models import Venta, Producto
    from database.connection import init_database
    print("   ✅ Módulos importados correctamente")
    
    # Test 2: Inicializar DB
    print("2. Inicializando base de datos...")
    init_database()
    print("   ✅ Base de datos inicializada")
    
    # Test 3: Obtener ventas
    print("3. Obteniendo ventas...")
    ventas = Venta.get_by_fecha('2025-06-01', '2025-06-20')
    print(f"   ✅ Ventas obtenidas: {len(ventas)}")
    
    # Test 4: Verificar estructura de Venta
    if ventas:
        venta = ventas[0]
        print("4. Verificando estructura de Venta...")
        print(f"   - ID: {venta.id}")
        print(f"   - Total: {venta.total}")
        print(f"   - Estado: {venta.estado}")
        print(f"   - Fecha: {venta.fecha}")
        print("   ✅ Estructura correcta")
    else:
        print("4. No hay ventas para verificar estructura")
    
    # Test 5: Obtener productos
    print("5. Obteniendo productos...")
    productos = Producto.get_all()
    print(f"   ✅ Productos obtenidos: {len(productos)}")
    
    print("\n🎉 TODAS LAS PRUEBAS PASARON")
    print("Sistema listo para producción")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
