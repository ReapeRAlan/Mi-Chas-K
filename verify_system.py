#!/usr/bin/env python3
"""
Verificación final del sistema antes de iniciar
"""
import sys
import os
sys.path.insert(0, os.getcwd())

def verify_system():
    """Verificar que todo esté funcionando"""
    print("=== VERIFICACIÓN FINAL DEL SISTEMA ===")
    
    try:
        from database.connection_adapter import execute_query, execute_update
        
        # 1. Test consulta básica
        print("1. Probando consulta básica...")
        productos = execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = 1")
        if productos:
            print(f"   ✅ {productos[0]['count']} productos activos encontrados")
        else:
            print("   ❌ No se pudieron obtener productos")
            return False
        
        # 2. Test consulta dashboard
        print("2. Probando consultas del dashboard...")
        ventas_hoy = execute_query("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM ventas 
            WHERE DATE(fecha) = DATE('now')
        """)
        if ventas_hoy:
            print(f"   ✅ Ventas de hoy: {ventas_hoy[0]['total']} ventas, ${ventas_hoy[0]['monto']}")
        else:
            print("   ❌ Error en consulta de ventas")
            return False
        
        # 3. Test actualización
        print("3. Probando actualización...")
        primer_producto = execute_query("SELECT id, stock FROM productos LIMIT 1")
        if primer_producto:
            producto_id = primer_producto[0]['id']
            stock_original = primer_producto[0]['stock']
            nuevo_stock = stock_original + 1
            
            result = execute_update(
                "UPDATE productos SET stock = ? WHERE id = ?",
                (nuevo_stock, producto_id),
                {
                    'table': 'productos',
                    'operation': 'UPDATE',
                    'data': {'id': producto_id, 'stock': nuevo_stock}
                }
            )
            
            if result is not None:
                # Restaurar stock original
                execute_update(
                    "UPDATE productos SET stock = ? WHERE id = ?",
                    (stock_original, producto_id),
                    {
                        'table': 'productos',
                        'operation': 'UPDATE',
                        'data': {'id': producto_id, 'stock': stock_original}
                    }
                )
                print("   ✅ Actualización funcionando correctamente")
            else:
                print("   ❌ Error en actualización")
                return False
        
        # 4. Test vendedores
        print("4. Verificando vendedores...")
        vendedores = execute_query("SELECT COUNT(*) as count FROM vendedores WHERE activo = 1")
        if vendedores and vendedores[0]['count'] > 0:
            print(f"   ✅ {vendedores[0]['count']} vendedores activos")
        else:
            print("   ❌ No hay vendedores activos")
            return False
        
        print("\n✅ SISTEMA LISTO - Todos los tests pasaron")
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    if verify_system():
        print("\n🚀 El sistema está listo para iniciar Streamlit")
    else:
        print("\n❌ Hay problemas que necesitan ser resueltos antes de iniciar")
