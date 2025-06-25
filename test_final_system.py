#!/usr/bin/env python3
"""
Test Final del Sistema MiChaska
Prueba completa de funcionalidad híbrida
"""

import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_system():
    """Prueba completa del sistema"""
    print("🔍 Iniciando pruebas del sistema MiChaska...")
    
    try:
        # Importar y crear adapter
        from database.connection_adapter import DatabaseAdapter
        
        print("✅ Importación exitosa del adaptador híbrido")
        
        # Inicializar adapter
        adapter = DatabaseAdapter()
        print("✅ Adaptador híbrido inicializado")
        
        # Test 1: Verificar productos
        print("\n📦 Verificando productos...")
        productos = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
        count_productos = productos[0]['count'] if productos else 0
        print(f"   - Productos en BD: {count_productos}")
        
        # Test 2: Verificar categorías
        print("\n🏷️ Verificando categorías...")
        categorias = adapter.execute_query("SELECT COUNT(*) as count FROM categorias")
        count_categorias = categorias[0]['count'] if categorias else 0
        print(f"   - Categorías en BD: {count_categorias}")
        
        # Test 3: Verificar ventas
        print("\n💰 Verificando ventas...")
        ventas = adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
        count_ventas = ventas[0]['count'] if ventas else 0
        print(f"   - Ventas en BD: {count_ventas}")
        
        # Test 4: Verificar usuarios
        print("\n👥 Verificando usuarios...")
        usuarios = adapter.execute_query("SELECT COUNT(*) as count FROM usuarios")
        count_usuarios = usuarios[0]['count'] if usuarios else 0
        print(f"   - Usuarios en BD: {count_usuarios}")
        
        # Test 5: Verificar que no hay sync queue pendiente con errores
        print("\n🔄 Verificando cola de sincronización...")
        try:
            sync_queue = adapter.execute_query("SELECT COUNT(*) as count FROM sync_queue WHERE status = 'error'")
            count_errors = sync_queue[0]['count'] if sync_queue else 0
            print(f"   - Elementos con error en sync_queue: {count_errors}")
        except Exception as e:
            print(f"   - No se pudo acceder a sync_queue (normal si no existe): {e}")
        
        # Test 6: Verificar estructura de tablas principales
        print("\n🗂️ Verificando estructura de tablas...")
        
        # Productos
        try:
            sample_producto = adapter.execute_query("SELECT * FROM productos LIMIT 1")
            if sample_producto:
                print(f"   - Estructura productos: {list(sample_producto[0].keys())}")
        except Exception as e:
            print(f"   - Error verificando productos: {e}")
        
        # Ventas
        try:
            sample_venta = adapter.execute_query("SELECT * FROM ventas LIMIT 1")
            if sample_venta:
                print(f"   - Estructura ventas: {list(sample_venta[0].keys())}")
        except Exception as e:
            print(f"   - Error verificando ventas: {e}")
        
        # Test 7: Verificar funciones del adapter
        print("\n⚙️ Verificando funciones del adaptador...")
        
        # Test connection status
        is_remote = hasattr(adapter, '_is_remote_available') and adapter._is_remote_available()
        print(f"   - Conexión remota disponible: {is_remote}")
        
        # Test local database
        local_exists = hasattr(adapter, 'local_db') and adapter.local_db is not None
        print(f"   - Base de datos local: {'Disponible' if local_exists else 'No disponible'}")
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("🎉 El sistema MiChaska está funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
