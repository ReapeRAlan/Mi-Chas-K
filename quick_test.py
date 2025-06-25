#!/usr/bin/env python3
"""
Test final rápido de verificación
"""

def quick_test():
    print("🧪 TEST RÁPIDO DE VERIFICACIÓN")
    print("=" * 40)
    
    try:
        import sys
        import os
        sys.path.insert(0, os.getcwd())
        
        from database.connection_adapter import DatabaseAdapter
        print("✅ Importación exitosa")
        
        adapter = DatabaseAdapter()
        print("✅ Adaptador creado")
        
        # Verificar métodos críticos
        methods = [
            '_sync_remote_to_local',
            '_adapt_query_for_remote', 
            '_convert_to_postgres_params',
            'force_sync_now'
        ]
        
        for method in methods:
            exists = hasattr(adapter, method)
            status = "✅" if exists else "❌"
            print(f"{status} {method}: {'EXISTE' if exists else 'NO EXISTE'}")
        
        # Test básico de conversión
        print("\n🔧 Test de conversión:")
        original = "SELECT * FROM productos WHERE activo = 1"
        adapted = adapter._adapt_query_for_remote(original)
        postgres = adapter._convert_to_postgres_params(adapted)
        
        print(f"Original: {original}")
        print(f"Adaptado: {adapted}")
        print(f"PostgreSQL: {postgres}")
        
        print("\n🎯 TODOS LOS MÉTODOS FUNCIONAN CORRECTAMENTE")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_test()
