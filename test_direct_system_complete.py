#!/usr/bin/env python3
"""
Prueba completa del sistema directo PostgreSQL
Validación para tablets - MiChaska
"""
import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal

# Agregar el directorio padre al path
sys.path.append('/home/ghost/Escritorio/Mi-Chas-K')

from database.connection_direct_final import DirectPostgreSQLAdapter
from database.connection_optimized import get_db_adapter, test_database_connection

def test_connection():
    """Probar conexión básica"""
    print("🔌 Probando conexión...")
    try:
        adapter = get_db_adapter()
        result = adapter.execute_query("SELECT current_timestamp as now, 'PostgreSQL Direct' as system")
        if result:
            print(f"✅ Conexión exitosa: {result[0]}")
            return True
        else:
            print("❌ Sin resultados en prueba de conexión")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_products():
    """Probar consulta de productos"""
    print("\n📦 Probando productos...")
    try:
        adapter = get_db_adapter()
        productos = adapter.get_productos()
        print(f"✅ {len(productos)} productos encontrados")
        
        if productos:
            for i, producto in enumerate(productos[:3]):
                print(f"   [{i+1}] {producto['nombre']} - ${producto['precio']} (Stock: {producto['stock']})")
        
        return len(productos) > 0
    except Exception as e:
        print(f"❌ Error obteniendo productos: {e}")
        return False

def test_categories():
    """Probar consulta de categorías"""
    print("\n📂 Probando categorías...")
    try:
        adapter = get_db_adapter()
        categorias = adapter.get_categorias()
        print(f"✅ {len(categorias)} categorías encontradas")
        
        if categorias:
            for i, categoria in enumerate(categorias[:3]):
                print(f"   [{i+1}] {categoria['nombre']} - Activo: {categoria['activo']}")
        
        return len(categorias) > 0
    except Exception as e:
        print(f"❌ Error obteniendo categorías: {e}")
        return False

def test_dashboard_data():
    """Probar datos del dashboard"""
    print("\n📊 Probando dashboard...")
    try:
        adapter = get_db_adapter()
        
        # Obtener fecha actual
        hoy = date.today().strftime('%Y-%m-%d')
        
        dashboard_data = adapter.get_dashboard_data(fecha_desde=hoy)
        
        print(f"✅ Dashboard data obtenida:")
        print(f"   - Ventas totales: {dashboard_data['resumen']['total_ventas']}")
        print(f"   - Ingresos totales: ${dashboard_data['resumen']['total_ingresos']}")
        print(f"   - Productos top: {len(dashboard_data['productos_top'])}")
        print(f"   - Ventas por día: {len(dashboard_data['ventas_por_dia'])}")
        
        return True
    except Exception as e:
        print(f"❌ Error obteniendo datos de dashboard: {e}")
        return False

def test_insert_product():
    """Probar inserción de producto"""
    print("\n➕ Probando inserción de producto...")
    try:
        adapter = get_db_adapter()
        
        # Datos de prueba
        producto_data = {
            'nombre': f'Producto Test {datetime.now().strftime("%H:%M:%S")}',
            'categoria': 'Test',
            'precio': 15.50,
            'descripcion': 'Producto de prueba para validación',
            'stock': 10,
            'activo': True,  # Importante: boolean verdadero
            'fecha_creacion': datetime.now(),
            'fecha_modificacion': datetime.now()
        }
        
        inserted_id = adapter.execute_insert('productos', producto_data)
        
        if inserted_id:
            print(f"✅ Producto insertado con ID: {inserted_id}")
            
            # Verificar que se insertó correctamente
            result = adapter.execute_query("SELECT * FROM productos WHERE id = %s", (inserted_id,))
            if result:
                producto = result[0]
                print(f"   - Nombre: {producto['nombre']}")
                print(f"   - Precio: ${producto['precio']}")
                print(f"   - Activo: {producto['activo']} (tipo: {type(producto['activo'])})")
                
                # Limpiar producto de prueba
                adapter.execute_delete('productos', 'id = %s', (inserted_id,))
                print(f"🧹 Producto de prueba eliminado")
            
            return True
        else:
            print("❌ No se pudo insertar el producto")
            return False
    except Exception as e:
        print(f"❌ Error insertando producto: {e}")
        return False

def test_sale_creation():
    """Probar creación de venta completa"""
    print("\n💰 Probando creación de venta...")
    try:
        adapter = get_db_adapter()
        
        # Obtener un producto existente
        productos = adapter.get_productos()
        if not productos:
            print("❌ No hay productos para crear venta")
            return False
        
        producto = productos[0]
        
        # Datos de venta
        venta_data = {
            'total': 100.00,
            'metodo_pago': 'Efectivo',
            'descuento': 0.00,
            'impuestos': 0.00,
            'fecha': datetime.now(),
            'vendedor': 'Test',
            'observaciones': 'Venta de prueba sistema directo',
            'estado': 'Completada'
        }
        
        # Detalles de venta
        detalles = [{
            'producto_id': producto['id'],
            'cantidad': 2,
            'precio_unitario': 50.00,
            'subtotal': 100.00
        }]
        
        venta_id = adapter.crear_venta(venta_data, detalles)
        
        if venta_id:
            print(f"✅ Venta creada con ID: {venta_id}")
            
            # Verificar venta
            venta_result = adapter.execute_query("SELECT * FROM ventas WHERE id = %s", (venta_id,))
            if venta_result:
                venta = venta_result[0]
                print(f"   - Total: ${venta['total']}")
                print(f"   - Método: {venta['metodo_pago']}")
                print(f"   - Estado: {venta['estado']}")
            
            # Verificar detalles
            detalles_result = adapter.execute_query("SELECT * FROM detalle_ventas WHERE venta_id = %s", (venta_id,))
            print(f"   - Detalles: {len(detalles_result)} items")
            
            # Limpiar venta de prueba
            adapter.execute_delete('detalle_ventas', 'venta_id = %s', (venta_id,))
            adapter.execute_delete('ventas', 'id = %s', (venta_id,))
            print(f"🧹 Venta de prueba eliminada")
            
            return True
        else:
            print("❌ No se pudo crear la venta")
            return False
    except Exception as e:
        print(f"❌ Error creando venta: {e}")
        return False

def test_boolean_handling():
    """Probar manejo específico de booleanos"""
    print("\n🔄 Probando manejo de booleanos...")
    try:
        adapter = get_db_adapter()
        
        # Crear categoría con diferentes tipos de valores booleanos
        test_data = [
            {'nombre': 'Test Bool 1', 'activo': True, 'descripcion': 'Boolean True'},
            {'nombre': 'Test Bool 2', 'activo': False, 'descripcion': 'Boolean False'},
            {'nombre': 'Test Bool 3', 'activo': 1, 'descripcion': 'Integer 1'},
            {'nombre': 'Test Bool 4', 'activo': 0, 'descripcion': 'Integer 0'},
            {'nombre': 'Test Bool 5', 'activo': 'true', 'descripcion': 'String true'},
            {'nombre': 'Test Bool 6', 'activo': 'false', 'descripcion': 'String false'},
        ]
        
        inserted_ids = []
        for data in test_data:
            data['fecha_creacion'] = datetime.now()
            category_id = adapter.execute_insert('categorias', data)
            if category_id:
                inserted_ids.append(category_id)
                print(f"✅ Categoría insertada: {data['nombre']} (activo: {data['activo']})")
            else:
                print(f"❌ Error insertando: {data['nombre']}")
        
        # Verificar valores insertados
        if inserted_ids:
            ids_str = ','.join(map(str, inserted_ids))
            result = adapter.execute_query(f"SELECT nombre, activo FROM categorias WHERE id IN ({ids_str})")
            
            print(f"\n📋 Valores almacenados en PostgreSQL:")
            for row in result:
                print(f"   - {row['nombre']}: {row['activo']} (tipo: {type(row['activo'])})")
            
            # Limpiar datos de prueba
            for category_id in inserted_ids:
                adapter.execute_delete('categorias', 'id = %s', (category_id,))
            print(f"\n🧹 {len(inserted_ids)} categorías de prueba eliminadas")
        
        return len(inserted_ids) > 0
        
    except Exception as e:
        print(f"❌ Error probando booleanos: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS COMPLETAS - SISTEMA DIRECTO POSTGRESQL")
    print("=" * 60)
    
    tests = [
        ("Conexión", test_connection),
        ("Productos", test_products),
        ("Categorías", test_categories),
        ("Dashboard", test_dashboard_data),
        ("Inserción Producto", test_insert_product),
        ("Creación Venta", test_sale_creation),
        ("Manejo Booleanos", test_boolean_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("💯 Sistema directo PostgreSQL LISTO para producción en tablets")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron, revisar errores")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
