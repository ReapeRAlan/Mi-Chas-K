#!/usr/bin/env python3
"""
Prueba completa del sistema híbrido
"""
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from database.connection_adapter import db_adapter, execute_query, execute_update
    import json
    
    print("=== PRUEBA SISTEMA HÍBRIDO COMPLETO ===")
    
    # 1. Estado del sistema
    print("\n1. 📊 ESTADO DEL SISTEMA")
    status = db_adapter.get_system_status()
    print(f"   Internet: {'✅' if status['internet'] else '❌'}")
    print(f"   Base local: {'✅' if status['local_db']['available'] else '❌'} ({status['local_db']['size_mb']} MB)")
    print(f"   Base remota: {'✅' if status['remote_db']['available'] else '❌'}")
    print(f"   Esquema remoto cacheado: {'✅' if status['remote_db']['schema_cached'] else '❌'}")
    
    print(f"\n   Datos locales:")
    for table, count in status['local_db']['tables'].items():
        print(f"     - {table}: {count} registros")
    
    print(f"\n   Sincronización:")
    sync_status = status['sync']
    print(f"     - Habilitada: {'✅' if sync_status['enabled'] else '❌'}")
    print(f"     - Pendientes: {sync_status['pending']}")
    print(f"     - Completadas: {sync_status['completed']}")
    print(f"     - Fallidas: {sync_status['failed']}")
    
    # 2. Validación de estructura remota
    print("\n2. 🔍 VALIDACIÓN DE ESTRUCTURA REMOTA")
    if db_adapter.remote_schema_cache:
        for table, schema in db_adapter.remote_schema_cache.items():
            print(f"   📋 Tabla {table}: {len(schema['columns'])} columnas")
            for col_name, col_info in list(schema['columns'].items())[:3]:  # Mostrar solo primeras 3
                nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                print(f"     - {col_name}: {col_info['type']} ({nullable})")
            if len(schema['columns']) > 3:
                print(f"     ... y {len(schema['columns']) - 3} columnas más")
    else:
        print("   ⚠️ No hay esquema remoto cacheado")
    
    # 3. Prueba de consultas
    print("\n3. 📖 PRUEBA DE CONSULTAS")
    
    # Consulta local
    productos_local = execute_query("SELECT COUNT(*) as count FROM productos", prefer_remote=False)
    print(f"   Local - Productos: {productos_local[0]['count'] if productos_local else 0}")
    
    # Consulta remota (si está disponible)
    if db_adapter.remote_available:
        try:
            productos_remote = execute_query("SELECT COUNT(*) as count FROM productos", prefer_remote=True)
            print(f"   Remota - Productos: {productos_remote[0]['count'] if productos_remote else 0}")
        except Exception as e:
            print(f"   Remota - Error: {e}")
    else:
        print("   Remota - No disponible")
    
    # 4. Prueba de escritura híbrida
    print("\n4. ✏️ PRUEBA DE ESCRITURA HÍBRIDA")
    
    # Obtener un producto para actualizar
    productos = execute_query("SELECT id, nombre, stock FROM productos LIMIT 1")
    
    if productos:
        producto = productos[0]
        print(f"   Producto de prueba: {producto['nombre']} (Stock: {producto['stock']})")
        
        nuevo_stock = (producto['stock'] or 0) + 1
        print(f"   Actualizando stock a: {nuevo_stock}")
        
        # Actualizar con sincronización híbrida
        result = execute_update(
            "UPDATE productos SET stock = ? WHERE id = ?",
            (nuevo_stock, producto['id']),
            {
                'table': 'productos',
                'operation': 'UPDATE',
                'data': {'id': producto['id'], 'stock': nuevo_stock}
            }
        )
        
        if result:
            print(f"   ✅ Actualización exitosa (Resultado: {result})")
            
            # Verificar actualización
            verificacion = execute_query("SELECT stock FROM productos WHERE id = ?", (producto['id'],))
            if verificacion:
                stock_actual = verificacion[0]['stock']
                print(f"   ✅ Verificación: Stock actual = {stock_actual}")
            
            # Ver estado de sincronización después de la operación
            sync_final = db_adapter.get_sync_status()
            print(f"   📝 Cola de sincronización: {sync_final['pending']} pendientes")
        else:
            print("   ❌ Error en actualización")
    else:
        print("   ⚠️ No hay productos para probar")
    
    # 5. Resumen final
    print("\n5. 📋 RESUMEN FINAL")
    final_status = db_adapter.get_system_status()
    
    print(f"   Sistema funcionando: {'✅' if final_status['local_db']['available'] else '❌'}")
    print(f"   Modo híbrido: {'✅' if final_status['remote_db']['available'] else '❌ (Solo local)'}")
    print(f"   Sincronización activa: {'✅' if final_status['sync']['enabled'] else '❌'}")
    
    if final_status['sync']['recent_pending']:
        print(f"   Operaciones pendientes de sincronizar:")
        for op in final_status['sync']['recent_pending']:
            print(f"     - {op['table']}: {op['operation']} ({op['timestamp']})")
    
    print("\n🎉 PRUEBA COMPLETA DEL SISTEMA HÍBRIDO FINALIZADA")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
