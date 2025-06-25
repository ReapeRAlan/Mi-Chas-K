#!/usr/bin/env python3
"""
Test comprehensivo de todas las correcciones aplicadas
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_all_fixes():
    print("🧪 PROBANDO TODAS LAS CORRECCIONES APLICADAS")
    print("=" * 60)
    
    try:
        from database.connection_adapter import DatabaseAdapter
        print("✅ Importación exitosa")
        
        adapter = DatabaseAdapter()
        print("✅ Adaptador creado")
        
        # Test 1: Verificar métodos críticos
        print("\n🔍 Test 1: Métodos críticos")
        methods_to_check = [
            '_sync_remote_to_local',
            '_adapt_query_for_remote',
            '_convert_to_postgres_params',
            'force_sync_now'
        ]
        
        for method in methods_to_check:
            if hasattr(adapter, method):
                print(f"✅ {method} existe")
            else:
                print(f"❌ {method} NO existe")
        
        # Test 2: Conversión de consultas
        print("\n🔍 Test 2: Conversión de consultas")
        test_queries = [
            "SELECT * FROM productos WHERE activo = 1",
            "SELECT * FROM ventas WHERE fecha >= datetime('now', '-7 days')",
            "INSERT INTO productos (nombre, precio, activo) VALUES (?, ?, ?)"
        ]
        
        for query in test_queries:
            adapted = adapter._adapt_query_for_remote(query)
            postgres = adapter._convert_to_postgres_params(adapted)
            print(f"Original: {query}")
            print(f"Adaptado: {adapted}")
            print(f"PostgreSQL: {postgres}")
            print("---")
        
        # Test 3: Consulta real con adaptación
        print("\n🔍 Test 3: Consulta real")
        try:
            productos = adapter.execute_query("SELECT COUNT(*) as total FROM productos WHERE activo = 1")
            if productos:
                print(f"✅ Consulta exitosa: {productos[0]['total']} productos activos")
            else:
                print("⚠️ Sin resultados")
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
        
        # Test 4: Funciones de sincronización
        print("\n🔍 Test 4: Funciones de sincronización")
        try:
            sync_result = adapter._sync_remote_to_local()
            print(f"✅ _sync_remote_to_local ejecutado: {sync_result}")
        except Exception as e:
            print(f"❌ Error en _sync_remote_to_local: {e}")
        
        print("\n🎯 TODOS LOS TESTS COMPLETADOS")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_all_fixes()
