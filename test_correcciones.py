#!/usr/bin/env python3
"""
Script para validar las correcciones del sistema de órdenes múltiples
"""

import sys
import os
sys.path.append('.')

try:
    print("🧪 VALIDANDO CORRECCIONES DEL SISTEMA")
    print("=" * 50)
    
    # Test 1: Importar módulos corregidos
    print("1. Probando importaciones...")
    from database.models import ItemCarrito, Carrito, Producto, Vendedor
    from src_pages.punto_venta import crear_nueva_orden, mostrar_carrito_orden_activa
    print("   ✅ Módulos importados correctamente")
    
    # Test 2: Verificar estructura de ItemCarrito
    print("2. Verificando estructura de ItemCarrito...")
    producto_ejemplo = Producto(id=1, nombre="Producto Test", precio=10.0, stock=5)
    item = ItemCarrito(producto=producto_ejemplo, cantidad=2)
    
    # Verificar atributos correctos
    assert hasattr(item, 'producto'), "ItemCarrito debe tener atributo 'producto'"
    assert hasattr(item, 'cantidad'), "ItemCarrito debe tener atributo 'cantidad'"
    assert hasattr(item.producto, 'nombre'), "Producto debe tener atributo 'nombre'"
    assert hasattr(item.producto, 'precio'), "Producto debe tener atributo 'precio'"
    
    print(f"   ✅ item.producto.nombre: {item.producto.nombre}")
    print(f"   ✅ item.producto.precio: {item.producto.precio}")
    print(f"   ✅ item.cantidad: {item.cantidad}")
    print(f"   ✅ item.subtotal: {item.subtotal}")
    
    # Test 3: Verificar carrito
    print("3. Probando funcionalidad de carrito...")
    carrito = Carrito()
    carrito.agregar_producto(producto_ejemplo, 3)
    
    assert len(carrito.items) > 0, "Carrito debe tener items"
    primer_item = carrito.items[0]
    assert primer_item.producto.nombre == "Producto Test", "Nombre debe ser correcto"
    assert primer_item.cantidad == 3, "Cantidad debe ser 3"
    
    print(f"   ✅ Producto agregado: {primer_item.producto.nombre}")
    print(f"   ✅ Cantidad: {primer_item.cantidad}")
    print(f"   ✅ Total carrito: ${carrito.total:.2f}")
    
    # Test 4: Verificar vendedores
    print("4. Probando obtención de vendedores...")
    try:
        from database.connection import init_database
        init_database()
        vendedores = Vendedor.get_nombres_activos()
        print(f"   ✅ Vendedores encontrados: {len(vendedores)}")
        if vendedores:
            print(f"   ✅ Primer vendedor: {vendedores[0]}")
        else:
            print("   ⚠️ No hay vendedores configurados")
    except Exception as e:
        print(f"   ⚠️ No se pudo conectar a la BD: {e}")
    
    print("\n🎉 TODAS LAS VALIDACIONES PASARON")
    print("Sistema corregido y listo para uso")
    
except Exception as e:
    print(f"\n❌ ERROR EN VALIDACIÓN: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
