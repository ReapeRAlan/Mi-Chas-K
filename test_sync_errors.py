#!/usr/bin/env python3
"""
Test específico para validar corrección de errores de sincronización
- can't adapt type 'dict'
- cannot convert dictionary update sequence element #0 to a sequence
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_adapter import DatabaseAdapter
import json
import sqlite3
from datetime import datetime
import traceback

def test_sync_error_fixes():
    """Probar las correcciones de errores de sincronización"""
    print("🧪 Testing correcciones de errores de sincronización...")
    
    adapter = DatabaseAdapter()
    
    # Test 1: Verificar deserialización de JSON con metadata
    print("\n1. Test de deserialización de JSON con metadata")
    try:
        # Simular datos como se almacenan en la cola
        test_data = {
            'table': 'productos',
            'operation': 'INSERT',
            'data': {
                'id': 999,
                'nombre': 'Producto Test',
                'precio': 10.50,
                'stock': 5,
                'activo': 1,
                'categoria_id': 1
            },
            'original_query': 'INSERT INTO productos...',
            'original_params': [999, 'Producto Test', 10.50],
            'timestamp': datetime.now().isoformat()
        }
        
        json_data = json.dumps(test_data)
        
        # Simular lo que hace la función de procesamiento
        parsed_data = json.loads(json_data)
        if isinstance(parsed_data, dict) and 'data' in parsed_data:
            data = parsed_data['data']
        else:
            data = parsed_data
        
        print(f"✅ Datos extraídos correctamente: {data}")
        
    except Exception as e:
        print(f"❌ Error en deserialización: {e}")
        traceback.print_exc()
    
    # Test 2: Verificar adaptación de datos para remoto
    print("\n2. Test de adaptación de datos para remoto")
    try:
        test_data = {
            'id': 999,
            'nombre': 'Producto Test',
            'precio': 10.50,
            'stock': 5,
            'activo': 1,
            'categoria_id': 1,
            'metadata': {'extra': 'data'}  # Esto debería ser filtrado
        }
        
        adapted_data = adapter._adapt_data_for_remote(test_data, 'productos')
        print(f"✅ Datos adaptados correctamente: {adapted_data}")
        
        # Verificar que no hay diccionarios anidados
        for key, value in adapted_data.items():
            if isinstance(value, dict):
                print(f"⚠️ Advertencia: Valor dict encontrado en {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error en adaptación de datos: {e}")
        traceback.print_exc()
    
    # Test 3: Verificar manejo de valores complejos
    print("\n3. Test de manejo de valores complejos")
    try:
        complex_data = {
            'id': 999,
            'nombre': 'Test',
            'precio': 10.50,
            'stock': 5,
            'activo': True,
            'categoria_id': 1,
            'metadata': {'config': {'option': 'value'}},  # Diccionario anidado
            'tags': ['tag1', 'tag2'],  # Lista
            'null_value': None  # Valor nulo
        }
        
        adapted_data = adapter._adapt_data_for_remote(complex_data, 'productos')
        print(f"✅ Datos complejos adaptados: {adapted_data}")
        
    except Exception as e:
        print(f"❌ Error en manejo de datos complejos: {e}")
        traceback.print_exc()
    
    # Test 4: Verificar cola de sincronización
    print("\n4. Test de cola de sincronización")
    try:
        # Agregar elemento a la cola
        sync_data = {
            'table': 'productos',
            'operation': 'INSERT',
            'data': {
                'id': 999,
                'nombre': 'Test Sync',
                'precio': 15.75,
                'stock': 10,
                'activo': 1,
                'categoria_id': 1
            }
        }
        
        adapter._add_to_sync_queue_robust(sync_data, "INSERT INTO productos...", (999, 'Test Sync'))
        print("✅ Elemento agregado a cola de sincronización")
        
        # Verificar que se puede leer de la cola
        with sqlite3.connect(adapter.local_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_queue ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"✅ Elemento leído de cola: {result[2]} - {result[3]}")  # operation, data
            else:
                print("❌ No se encontró el elemento en la cola")
        
    except Exception as e:
        print(f"❌ Error en cola de sincronización: {e}")
        traceback.print_exc()
    
    # Test 5: Verificar procesamiento de cola (simulado)
    print("\n5. Test de procesamiento de cola (simulado)")
    try:
        # Obtener elemento de la cola
        with sqlite3.connect(adapter.local_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, table_name, operation, data, attempts
                FROM sync_queue 
                WHERE status = 'pending'
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                item_id, table_name, operation, data_json, attempts = result
                
                # Simular deserialización
                parsed_data = json.loads(data_json)
                if isinstance(parsed_data, dict) and 'data' in parsed_data:
                    data = parsed_data['data']
                else:
                    data = parsed_data
                
                print(f"✅ Procesamiento simulado exitoso: {operation} en {table_name}")
                print(f"   Datos: {data}")
                
                # Marcar como procesado
                cursor.execute("UPDATE sync_queue SET status = 'test_completed' WHERE id = ?", (item_id,))
                conn.commit()
                
            else:
                print("ℹ️ No hay elementos pendientes en la cola")
        
    except Exception as e:
        print(f"❌ Error en procesamiento de cola: {e}")
        traceback.print_exc()
    
    print("\n✅ Test de correcciones completado")

if __name__ == "__main__":
    test_sync_error_fixes()
