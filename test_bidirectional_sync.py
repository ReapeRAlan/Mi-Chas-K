#!/usr/bin/env python3
"""
Test completo de sincronización bidireccional
Sistema Mi Chas-K - Versión Híbrida Robusta
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_adapter import DatabaseAdapter

def test_connection():
    """Probar conexiones básicas"""
    print("🧪 Probando conexiones básicas...")
    
    try:
        adapter = DatabaseAdapter()
        
        # Test conexión local
        with adapter.get_connection(prefer_remote=False) as conn:
            print("✅ Conexión local exitosa")
        
        # Test conexión remota
        if adapter.remote_available:
            with adapter.get_connection(prefer_remote=True) as conn:
                print("✅ Conexión remota exitosa")
        else:
            print("⚠️ Conexión remota no disponible")
        
        return True
    except Exception as e:
        print(f"❌ Error en conexiones: {e}")
        return False

def test_crud_operations():
    """Probar operaciones CRUD con sincronización"""
    print("\n🧪 Probando operaciones CRUD...")
    
    try:
        adapter = DatabaseAdapter()
        
        # 1. Test INSERT
        print("➕ Probando INSERT...")
        producto_test = {
            'nombre': f'Producto Test {datetime.now().strftime("%H%M%S")}',
            'precio': 15.50,
            'categoria': 'Test',
            'stock': 100,
            'descripcion': 'Producto de prueba para sincronización',
            'activo': 1
        }
        
        product_id = adapter.execute_crud_operation('INSERT', 'productos', producto_test)
        if product_id:
            print(f"✅ Producto insertado con ID: {product_id}")
        else:
            print("❌ Error insertando producto")
            return False
        
        # 2. Test UPDATE
        print("🔄 Probando UPDATE...")
        update_data = {
            'precio': 18.75,
            'stock': 80,
            'descripcion': 'Producto actualizado por test bidireccional'
        }
        
        rows_updated = adapter.execute_crud_operation(
            'UPDATE', 'productos', update_data, f'id = {product_id}'
        )
        if rows_updated:
            print(f"✅ Producto actualizado ({rows_updated} filas)")
        else:
            print("❌ Error actualizando producto")
        
        # 3. Test SELECT para verificar
        print("🔍 Verificando datos...")
        productos = adapter.execute_query(
            "SELECT * FROM productos WHERE nombre LIKE ?", 
            ('%Producto Test%',)
        )
        
        if productos:
            print(f"✅ Encontrados {len(productos)} productos de test")
            for p in productos:
                print(f"   - {p['nombre']}: ${p['precio']} (Stock: {p['stock']})")
        
        # 4. Test venta completa
        print("💰 Probando venta completa...")
        venta_data = {
            'total': 37.50,
            'metodo_pago': 'Efectivo',
            'vendedor': 'Test Bidireccional',
            'observaciones': 'Venta de prueba bidireccional'
        }
        
        venta_id = adapter.execute_crud_operation('INSERT', 'ventas', venta_data)
        if venta_id:
            print(f"✅ Venta creada con ID: {venta_id}")
            
            # Agregar detalles de venta
            detalle_data = {
                'venta_id': venta_id,
                'producto_id': product_id,
                'cantidad': 2,
                'precio_unitario': 18.75,
                'subtotal': 37.50
            }
            
            detalle_id = adapter.execute_crud_operation('INSERT', 'detalle_ventas', detalle_data)
            if detalle_id:
                print(f"✅ Detalle de venta creado con ID: {detalle_id}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones CRUD: {e}")
        return False

def test_sync_queue():
    """Probar cola de sincronización"""
    print("\n🧪 Probando cola de sincronización...")
    
    try:
        adapter = DatabaseAdapter()
        
        # Verificar cola antes
        queue_before = adapter.execute_query(
            "SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'"
        )
        pending_before = queue_before[0]['count'] if queue_before else 0
        print(f"📝 Cola de sincronización: {pending_before} elementos pendientes")
        
        # Forzar sincronización
        print("🔄 Forzando sincronización...")
        sync_success = adapter.force_sync()
        
        if sync_success:
            print("✅ Sincronización forzada exitosa")
        else:
            print("⚠️ Sincronización con advertencias o sin conexión remota")
        
        # Verificar cola después
        queue_after = adapter.execute_query(
            "SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'"
        )
        pending_after = queue_after[0]['count'] if queue_after else 0
        print(f"📝 Cola después de sincronización: {pending_after} elementos pendientes")
        
        # Mostrar estadísticas de cola
        stats = adapter.execute_query("""
            SELECT status, COUNT(*) as count 
            FROM sync_queue 
            GROUP BY status
        """)
        
        if stats:
            print("📊 Estadísticas de cola de sincronización:")
            for stat in stats:
                print(f"   - {stat['status']}: {stat['count']} elementos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando cola de sincronización: {e}")
        return False

def test_system_status():
    """Probar estado del sistema"""
    print("\n🧪 Verificando estado del sistema...")
    
    try:
        adapter = DatabaseAdapter()
        status = adapter.get_system_status()
        
        print("📊 Estado del Sistema Híbrido:")
        print(f"   🌐 Conexión remota: {'✅ Disponible' if status.get('remote_available') else '❌ No disponible'}")
        print(f"   💾 Base local: {'✅ OK' if status.get('local_available') else '❌ Error'}")
        print(f"   🔄 Sincronización: {'✅ Habilitada' if status.get('sync_enabled') else '❌ Deshabilitada'}")
        print(f"   📶 Internet: {'✅ Conectado' if status.get('internet_connection') else '❌ Sin conexión'}")
        
        # Estadísticas de datos
        local_stats = status.get('local_stats', {})
        remote_stats = status.get('remote_stats', {})
        
        print("\n📈 Estadísticas de Datos:")
        print("   Local:")
        for table, count in local_stats.items():
            print(f"     - {table}: {count}")
        
        if remote_stats:
            print("   Remoto:")
            for table, count in remote_stats.items():
                print(f"     - {table}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estado del sistema: {e}")
        return False

def test_conflict_resolution():
    """Probar resolución de conflictos"""
    print("\n🧪 Probando resolución de conflictos...")
    
    try:
        adapter = DatabaseAdapter()
        
        # Crear datos que podrían generar conflictos
        print("🔄 Creando escenario de conflicto...")
        
        # Insertar producto localmente
        producto_local = {
            'nombre': f'Conflicto Test {datetime.now().strftime("%H%M%S")}',
            'precio': 10.00,
            'categoria': 'Conflicto',
            'stock': 50,
            'activo': 1
        }
        
        product_id = adapter.execute_crud_operation('INSERT', 'productos', producto_local)
        print(f"✅ Producto local creado: ID {product_id}")
        
        # Simular cambio remoto (actualizando directamente en local con precio diferente)
        time.sleep(1)  # Asegurar timestamp diferente
        
        # Actualizar con precio diferente para simular conflicto
        update_data = {
            'precio': 12.50,
            'stock': 45
        }
        
        adapter.execute_crud_operation('UPDATE', 'productos', update_data, f'id = {product_id}')
        print("✅ Simulación de conflicto preparada")
        
        # Ejecutar sincronización para ver resolución
        if adapter.remote_available:
            print("🔄 Ejecutando sincronización para resolver conflictos...")
            adapter.force_sync()
            print("✅ Sincronización de resolución de conflictos completada")
        else:
            print("⚠️ No se puede probar resolución remota sin conexión")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando resolución de conflictos: {e}")
        return False

def run_comprehensive_test():
    """Ejecutar suite completa de pruebas"""
    print("🚀 Iniciando pruebas completas de sincronización bidireccional")
    print("=" * 60)
    
    tests = [
        ("Conexiones", test_connection),
        ("Operaciones CRUD", test_crud_operations),
        ("Cola de Sincronización", test_sync_queue),
        ("Estado del Sistema", test_system_status),
        ("Resolución de Conflictos", test_conflict_resolution)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Ejecutando: {test_name}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            success = test_func()
            end_time = time.time()
            
            duration = end_time - start_time
            results.append({
                'test': test_name,
                'success': success,
                'duration': duration
            })
            
            status = "✅ EXITOSO" if success else "❌ FALLIDO"
            print(f"{status} ({duration:.2f}s)")
            
        except Exception as e:
            print(f"❌ EXCEPCIÓN: {e}")
            results.append({
                'test': test_name,
                'success': False,
                'duration': 0,
                'error': str(e)
            })
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    total_time = sum(r['duration'] for r in results)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        duration = result['duration']
        print(f"{status} {result['test']} ({duration:.2f}s)")
        if 'error' in result:
            print(f"   Error: {result['error']}")
    
    print(f"\n📊 Total: {successful_tests}/{total_tests} pruebas exitosas")
    print(f"⏱️ Tiempo total: {total_time:.2f}s")
    
    if successful_tests == total_tests:
        print("🎉 ¡Todas las pruebas fueron exitosas!")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar logs para detalles.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
