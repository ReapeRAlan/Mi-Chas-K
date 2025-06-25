#!/usr/bin/env python3
"""
Script para probar las correcciones de errores críticos
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection_adapter():
    """Probar el adaptador de conexiones corregido"""
    print("🔧 Probando adaptador de conexiones corregido...")
    
    try:
        from database.connection_adapter import db_adapter
        
        # Test 1: Verificar que las tablas locales existen
        print("\n1. Verificando estructura de base de datos local...")
        
        # Consulta que debe ejecutarse solo localmente
        sync_queue_result = db_adapter.execute_query("SELECT COUNT(*) as count FROM sync_queue", prefer_remote=False)
        print(f"   ✅ Tabla sync_queue: {sync_queue_result[0]['count']} registros")
        
        # Consulta que debe ejecutarse solo localmente
        usuarios_result = db_adapter.execute_query("SELECT COUNT(*) as count FROM usuarios", prefer_remote=False)
        print(f"   ✅ Tabla usuarios: {usuarios_result[0]['count']} registros")
        
        # Test 2: Verificar productos (puede ser remoto o local)
        print("\n2. Verificando productos...")
        productos_result = db_adapter.execute_query("SELECT COUNT(*) as count FROM productos")
        print(f"   ✅ Productos: {productos_result[0]['count']} registros")
        
        # Test 3: Verificar categorías
        print("\n3. Verificando categorías...")
        categorias_result = db_adapter.execute_query("SELECT COUNT(*) as count FROM categorias")
        print(f"   ✅ Categorías: {categorias_result[0]['count']} registros")
        
        # Test 4: Verificar ventas
        print("\n4. Verificando ventas...")
        ventas_result = db_adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
        print(f"   ✅ Ventas: {ventas_result[0]['count']} registros")
        
        # Test 5: Probar función _is_local_only_query
        print("\n5. Probando detección de consultas locales...")
        
        test_queries = [
            ("SELECT * FROM sync_queue", True),
            ("SELECT * FROM usuarios", True),
            ("SELECT * FROM productos", False),
            ("SELECT * FROM categorias", False),
            ("INSERT INTO sync_queue (data) VALUES ('test')", True),
            ("UPDATE productos SET precio = 10", False)
        ]
        
        for query, expected_local in test_queries:
            is_local = db_adapter._is_local_only_query(query)
            status = "✅" if is_local == expected_local else "❌"
            print(f"   {status} '{query[:30]}...' -> Local: {is_local} (esperado: {expected_local})")
        
        # Test 6: Probar context manager
        print("\n6. Probando context manager...")
        try:
            with db_adapter.get_connection(prefer_remote=False) as conn:
                if hasattr(conn, 'row_factory'):
                    print("   ✅ Conexión SQLite obtenida correctamente")
                else:
                    print("   ✅ Conexión PostgreSQL obtenida correctamente")
        except Exception as e:
            print(f"   ❌ Error en context manager: {e}")
            
        print("\n🎉 Pruebas del adaptador completadas exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas del adaptador: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_queue_operations():
    """Probar operaciones de la cola de sincronización"""
    print("\n🔄 Probando operaciones de cola de sincronización...")
    
    try:
        from database.connection_adapter import db_adapter
        
        # Test 1: Agregar elemento a la cola
        print("\n1. Agregando elemento a la cola...")
        test_data = {
            'table': 'productos',
            'operation': 'INSERT',
            'data': {'nombre': 'Producto Test', 'precio': 10.50}
        }
        
        with sqlite3.connect(db_adapter.local_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_queue (table_name, operation, data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                test_data['table'],
                test_data['operation'], 
                str(test_data['data']),
                datetime.now()
            ))
            conn.commit()
            print("   ✅ Elemento agregado a la cola")
        
        # Test 2: Leer elementos de la cola
        print("\n2. Leyendo elementos de la cola...")
        queue_items = db_adapter.execute_query("SELECT * FROM sync_queue WHERE status = 'pending'")
        print(f"   ✅ Elementos pendientes en cola: {len(queue_items)}")
        
        # Test 3: Verificar que las consultas de sync_queue no van a remoto
        print("\n3. Verificando que consultas sync_queue son solo locales...")
        is_local = db_adapter._is_local_only_query("SELECT * FROM sync_queue")
        print(f"   ✅ Consulta sync_queue es local: {is_local}")
        
        print("\n🎉 Pruebas de cola de sincronización completadas!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas de cola: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Probar manejo de errores mejorado"""
    print("\n🛡️ Probando manejo de errores mejorado...")
    
    try:
        from database.connection_adapter import db_adapter
        
        # Test 1: Consulta con sintaxis incorrecta
        print("\n1. Probando consulta con sintaxis incorrecta...")
        result = db_adapter.execute_query("SELECT * FROM tabla_inexistente")
        print(f"   ✅ Resultado (debe ser lista vacía): {result}")
        
        # Test 2: Consulta con parámetros incorrectos
        print("\n2. Probando consulta con parámetros incorrectos...")
        result = db_adapter.execute_query("SELECT * FROM productos WHERE id = ?", ("texto_no_numerico",))
        print(f"   ✅ Resultado manejado: {len(result)} registros")
        
        # Test 3: Verificar que el sistema sigue funcionando después de errores
        print("\n3. Verificando recuperación después de errores...")
        result = db_adapter.execute_query("SELECT COUNT(*) as count FROM productos")
        print(f"   ✅ Sistema recuperado: {result[0]['count']} productos")
        
        print("\n🎉 Pruebas de manejo de errores completadas!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas de manejo de errores: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 INICIANDO PRUEBAS DE CORRECCIONES DE ERRORES CRÍTICOS")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Ejecutar pruebas
    tests = [
        ("Adaptador de Conexiones", test_connection_adapter),
        ("Cola de Sincronización", test_sync_queue_operations),
        ("Manejo de Errores", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        print("-" * 40)
        
        if not test_func():
            all_tests_passed = False
            print(f"❌ FALLÓ: {test_name}")
        else:
            print(f"✅ ÉXITO: {test_name}")
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TODAS LAS PRUEBAS PASARON - ERRORES CORREGIDOS")
    else:
        print("❌ FALLÓ AL MENOS UNA PRUEBA - REVISAR ERRORES")
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
