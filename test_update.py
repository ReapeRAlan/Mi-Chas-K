#!/usr/bin/env python3
"""
Test de consultas UPDATE
"""
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from database.connection_adapter import execute_query, execute_update
    
    print("=== TEST DE CONSULTAS UPDATE ===")
    
    # Obtener un producto para probar
    productos = execute_query("SELECT id, nombre, stock FROM productos LIMIT 1")
    
    if productos:
        producto = productos[0]
        print(f"Producto de prueba: {producto['nombre']} (ID: {producto['id']}, Stock actual: {producto['stock']})")
        
        nuevo_stock = producto['stock'] + 1 if producto['stock'] is not None else 1
        print(f"Intentando actualizar stock a: {nuevo_stock}")
        
        # Probar actualización
        result = execute_update(
            "UPDATE productos SET stock = ? WHERE id = ?",
            (nuevo_stock, producto['id']),
            {
                'table': 'productos',
                'operation': 'UPDATE',
                'data': {'id': producto['id'], 'stock': nuevo_stock}
            }
        )
        
        if result is not None:
            print("✅ Actualización exitosa")
            
            # Verificar el cambio
            productos_updated = execute_query("SELECT stock FROM productos WHERE id = ?", (producto['id'],))
            if productos_updated:
                new_stock = productos_updated[0]['stock']
                print(f"Stock después de actualización: {new_stock}")
                
                if new_stock == nuevo_stock:
                    print("✅ Verificación exitosa - el stock se actualizó correctamente")
                else:
                    print(f"❌ Error - stock esperado: {nuevo_stock}, stock actual: {new_stock}")
            else:
                print("❌ No se pudo verificar la actualización")
        else:
            print("❌ Error en la actualización")
    else:
        print("❌ No se encontraron productos para probar")
        
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
