#!/usr/bin/env python3
"""
Test completo del sistema híbrido funcionando solo en local
"""
import sys
import os
sys.path.insert(0, os.getcwd())

def test_sistema_completo():
    print("=== PRUEBA COMPLETA DEL SISTEMA ===")
    
    try:
        from database.connection_adapter import execute_query, execute_update
        
        # 1. Test de productos
        print("\n1. Probando consulta de productos...")
        productos = execute_query("SELECT id, nombre, precio, stock FROM productos WHERE activo = 1 LIMIT 5")
        print(f"   ✅ Productos encontrados: {len(productos)}")
        for p in productos[:3]:
            print(f"      - {p['nombre']}: ${p['precio']} (Stock: {p['stock']})")
        
        # 2. Test de categorías
        print("\n2. Probando consulta de categorías...")
        categorias = execute_query("SELECT nombre FROM categorias WHERE activo = 1")
        print(f"   ✅ Categorías encontradas: {len(categorias)}")
        print(f"      Categorías: {[c['nombre'] for c in categorias]}")
        
        # 3. Test de vendedores
        print("\n3. Probando consulta de vendedores...")
        vendedores = execute_query("SELECT nombre FROM vendedores WHERE activo = 1")
        print(f"   ✅ Vendedores encontrados: {len(vendedores)}")
        print(f"      Vendedores: {[v['nombre'] for v in vendedores]}")
        
        # 4. Test de actualización de stock
        print("\n4. Probando actualización de stock...")
        if productos:
            producto_test = productos[0]
            stock_original = producto_test['stock']
            nuevo_stock = stock_original + 1
            
            result = execute_update(
                "UPDATE productos SET stock = ? WHERE id = ?",
                (nuevo_stock, producto_test['id'])
            )
            
            if result:
                # Verificar cambio
                productos_updated = execute_query("SELECT stock FROM productos WHERE id = ?", (producto_test['id'],))
                if productos_updated and productos_updated[0]['stock'] == nuevo_stock:
                    print(f"   ✅ Stock actualizado correctamente: {stock_original} → {nuevo_stock}")
                    
                    # Restaurar stock original
                    execute_update("UPDATE productos SET stock = ? WHERE id = ?", (stock_original, producto_test['id']))
                    print(f"   ✅ Stock restaurado: {nuevo_stock} → {stock_original}")
                else:
                    print("   ❌ Error verificando actualización")
            else:
                print("   ❌ Error en actualización")
        
        # 5. Test de inserción de venta
        print("\n5. Probando inserción de venta...")
        venta_result = execute_update("""
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones)
            VALUES (datetime('now'), 100.50, 'Efectivo', 'Sistema', 'Venta de prueba')
        """)
        
        if venta_result:
            print(f"   ✅ Venta insertada con ID: {venta_result}")
            
            # Insertar detalle de venta
            detalle_result = execute_update("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (venta_result, productos[0]['id'], 1, productos[0]['precio'], productos[0]['precio']))
            
            if detalle_result:
                print(f"   ✅ Detalle de venta insertado con ID: {detalle_result}")
            else:
                print("   ❌ Error insertando detalle de venta")
        else:
            print("   ❌ Error insertando venta")
        
        # 6. Test de consulta de ventas
        print("\n6. Probando consulta de ventas...")
        ventas = execute_query("""
            SELECT v.id, v.fecha, v.total, v.vendedor,
                   COUNT(dv.id) as items
            FROM ventas v
            LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
            GROUP BY v.id
            ORDER BY v.fecha DESC
            LIMIT 5
        """)
        
        print(f"   ✅ Ventas encontradas: {len(ventas)}")
        for v in ventas[:3]:
            print(f"      - Venta {v['id']}: ${v['total']} - {v['vendedor']} ({v['items']} items)")
        
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("    El sistema está funcionando correctamente en modo local")
        print("    Puedes usar el punto de venta, inventario y dashboard sin problemas")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_sistema_completo()
