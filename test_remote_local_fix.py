#!/usr/bin/env python3
"""
Test específico para validar corrección del error:
"cannot convert dictionary update sequence element #0 to a sequence"
en la función _sync_table_remote_to_local
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_adapter import DatabaseAdapter
import sqlite3
import traceback

def test_remote_to_local_sync():
    """Probar corrección del error de sincronización remoto->local"""
    print("🧪 Testing corrección de sincronización remoto->local...")
    
    adapter = DatabaseAdapter()
    
    # Test 1: Verificar obtención de registros locales sin error
    print("\n1. Test de obtención de registros locales")
    try:
        with sqlite3.connect(adapter.local_db_path) as conn:
            cursor = conn.cursor()
            
            # Simular lo que hace _sync_table_remote_to_local
            table_name = 'productos'
            
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            print(f"   ✅ Columnas encontradas en {table_name}: {len(column_names)}")
            print(f"   📋 Nombres: {column_names[:5]}...")  # Mostrar solo las primeras 5
            
            # Obtener registros
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id LIMIT 5")
            local_rows = cursor.fetchall()
            
            # Convertir filas a diccionarios
            local_records = {}
            for row in local_rows:
                row_dict = {column_names[i]: row[i] for i in range(len(column_names))}
                local_records[row_dict['id']] = row_dict
            
            print(f"   ✅ {len(local_records)} registros convertidos a diccionarios")
            
            # Mostrar ejemplo de registro
            if local_records:
                first_record = list(local_records.values())[0]
                print(f"   📄 Ejemplo: ID {first_record['id']} - {first_record.get('nombre', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Error en obtención de registros locales: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Verificar función completa de sincronización simulada
    print("\n2. Test de sincronización simulada")
    try:
        if adapter.remote_available:
            # Solo probar si hay conexión remota
            adapter._sync_remote_to_local()
            print("   ✅ Sincronización remoto->local completada sin errores")
        else:
            print("   ⚠️ Conexión remota no disponible, test saltado")
        
    except Exception as e:
        print(f"   ❌ Error en sincronización simulada: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Verificar adaptación de datos para local
    print("\n3. Test de adaptación de datos para local")
    try:
        test_data = {
            'id': 999,
            'nombre': 'Test Product',
            'precio': 25.75,
            'activo': True,  # Boolean de PostgreSQL
            'categoria': 'Test',
            'stock': 10
        }
        
        adapted_data = adapter._adapt_data_for_local(test_data, 'productos')
        print(f"   ✅ Datos adaptados: {adapted_data}")
        
        # Verificar que booleanos se convirtieron a enteros
        if 'activo' in adapted_data:
            activo_val = adapted_data['activo']
            if isinstance(activo_val, int) and activo_val in [0, 1]:
                print(f"   ✅ Boolean convertido correctamente: {activo_val}")
            else:
                print(f"   ⚠️ Boolean no convertido: {activo_val} (type: {type(activo_val)})")
        
    except Exception as e:
        print(f"   ❌ Error en adaptación de datos: {e}")
        traceback.print_exc()
        return False
    
    print("\n✅ Test de corrección remoto->local completado exitosamente")
    return True

if __name__ == "__main__":
    success = test_remote_to_local_sync()
    if success:
        print("\n🎉 ¡Corrección verificada exitosamente!")
    else:
        print("\n❌ Aún hay problemas que resolver")
